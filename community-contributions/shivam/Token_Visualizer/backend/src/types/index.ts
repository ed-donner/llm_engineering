export interface PredictRequest {
  prompt: string;
  maxTokens: number;
}

export interface TokenPrediction {
  token: string;
  probability: number;
  alternatives: AlternativeToken[];
}

export interface AlternativeToken {
  token: string;
  prob: number;
}

export interface StreamChunk {
  type: 'token' | 'done';
  data?: TokenPrediction;
}