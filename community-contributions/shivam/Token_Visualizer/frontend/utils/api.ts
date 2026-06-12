export interface TokenPrediction {
  token: string;
  probability: number;
  alternatives: AlternativeToken[];
}

export interface AlternativeToken {
  token: string;
  prob: number;
}

interface StreamMessage {
  type: 'token' | 'done' | 'error';
  data?: TokenPrediction;
  error?: string;
}

export async function* streamTokenPredictions(
  prompt: string,
  maxTokens: number
): AsyncGenerator<TokenPrediction> {
  const response = await fetch('http://localhost:8000/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, maxTokens }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error: ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const json = line.slice(6);
        try {
          const msg: StreamMessage = JSON.parse(json);
          if (msg.type === 'token' && msg.data) {
            yield msg.data;
          } else if (msg.type === 'error') {
            throw new Error(msg.error);
          }
        } catch {
          // Skip invalid JSON
        }
      }
    }
  }
}