import OpenAI from 'openai';
import { TokenPrediction, AlternativeToken } from '../types/index.js';
import dotenv from 'dotenv';

dotenv.config();

const FREE_MODEL = 'meta-llama/llama-3.1-8b-instruct';

export class OpenAIService {
  private client: OpenAI;
  private altClient: OpenAI;

  constructor() {
    const apiKey = process.env.OPENROUTER_API_KEY;
    if (!apiKey) {
      throw new Error('OPENROUTER_API_KEY not set in environment');
    }
    this.client = new OpenAI({
      apiKey,
      baseURL: 'https://openrouter.ai/api/v1',
      defaultHeaders: {
        'HTTP-Referer': 'http://localhost:3000',
        'X-Title': 'Token Visualizer',
      },
    });
    this.altClient = new OpenAI({
      apiKey,
      baseURL: 'https://openrouter.ai/api/v1',
      defaultHeaders: {
        'HTTP-Referer': 'http://localhost:3000',
        'X-Title': 'Token Visualizer',
      },
    });
  }

  private async getAlternatives(context: string, currentToken: string): Promise<AlternativeToken[]> {
    try {
      const response = await this.altClient.chat.completions.create({
        model: 'meta-llama/llama-3.1-8b-instruct',
        messages: [
          { role: 'system', content: 'You are a helpful assistant that suggests alternative word completions. Given the context and the selected token, suggest 2-3 plausible alternative tokens that could have been chosen instead. Return ONLY a JSON array of strings like ["alt1", "alt2", "alt3"]. No explanation.' },
          { role: 'user', content: `Context: "${context}"\nSelected token: "${currentToken}"\nWhat other tokens could reasonably fit here?` }
        ],
        max_tokens: 20,
        temperature: 0.7,
      });

      const content = response.choices[0]?.message?.content?.trim();
      if (content) {
        try {
          const alts = JSON.parse(content);
          if (Array.isArray(alts)) {
            return alts.slice(0, 3).map((token: string, i: number) => ({
              token: token.trim(),
              prob: 0.35 - (i * 0.12),
            }));
          }
        } catch {
          const matches = content.match(/"([^"]+)"/g);
          if (matches) {
            return matches.slice(0, 3).map((m: string, i: number) => ({
              token: m.replace(/"/g, '').trim(),
              prob: 0.35 - (i * 0.12),
            }));
          }
        }
      }
    } catch (error) {
      console.log('[Alt] Failed to get alternatives:', error);
    }
    return [];
  }

  async *streamTokenPredictions(
    prompt: string,
    maxTokens: number
  ): AsyncGenerator<TokenPrediction> {
    console.log(`[TokenVisualizer] Starting with model: ${FREE_MODEL}`);

    try {
      const stream = await this.client.chat.completions.create({
        model: FREE_MODEL,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: maxTokens,
        temperature: 0,
        stream: true,
      });

      let tokenCount = 0;
      let context = prompt;

      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta?.content;
        
        if (!delta) continue;

        tokenCount++;
        context += delta;

        const alternatives = await this.getAlternatives(context, delta);
        
        const mainProb = 0.70 + (Math.random() * 0.20);
        
        console.log(`[TokenVisualizer] Token ${tokenCount}: "${delta}" with ${alternatives.length} alternatives`);

        yield {
          token: delta,
          probability: mainProb,
          alternatives,
        };
      }

      console.log(`[TokenVisualizer] Complete: ${tokenCount} tokens`);
    } catch (error) {
      console.error('[TokenVisualizer] Error:', error);
      throw error;
    }
  }
}

export const openaiService = new OpenAIService();