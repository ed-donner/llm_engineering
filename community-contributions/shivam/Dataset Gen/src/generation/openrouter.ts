const OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1";

interface ChatMessage {
  role: "system" | "user";
  content: string;
}

interface ChatOptions {
  model: string;
  messages: ChatMessage[];
  temperature?: number;
  max_tokens?: number;
}

interface ChatResponse {
  choices: Array<{
    message: { content: string };
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

interface ModelInfo {
  id: string;
  name?: string;
  provider?: string;
}

export class OpenRouterClient {
  private apiKey: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.OPENROUTER_API_KEY || "";
    if (!this.apiKey) {
      throw new Error("OPENROUTER_API_KEY is required");
    }
  }

  async listModels(): Promise<ModelInfo[]> {
    const response = await fetch(`${OPENROUTER_BASE_URL}/models`, {
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to list models: ${response.status}`);
    }

    const data = await response.json();
    return data.data || [];
  }

  async chat(options: ChatOptions): Promise<string> {
    const response = await fetch(`${OPENROUTER_BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: options.model,
        messages: options.messages,
        temperature: options.temperature ?? 0.7,
        max_tokens: options.max_tokens ?? 4096,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`OpenRouter API error: ${error.error?.message || response.status}`);
    }

    const data: ChatResponse = await response.json();
    const content = data.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error("No content in response");
    }
    return content;
  }

  async testConnection(modelId: string): Promise<boolean> {
    try {
      await this.chat({
        model: modelId,
        messages: [{ role: "user", content: "Hi" }],
        max_tokens: 10,
      });
      return true;
    } catch {
      return false;
    }
  }
}

export const openrouter = new OpenRouterClient();