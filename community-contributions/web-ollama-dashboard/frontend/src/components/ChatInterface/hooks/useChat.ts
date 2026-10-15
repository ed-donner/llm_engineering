import axios from "axios";
import { useState } from "react";

interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

interface ChatRequest {
  model: string;
  messages: ChatMessage[];
}

interface ChatResponse {
  success: boolean;
  response?: string;
  error?: string;
  details?: string;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Hook: useChat
// ---------------------------------------------------------------------------------------------------------------------

export function useChat() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async ({
    model,
    messages,
  }: ChatRequest): Promise<string | null> => {
    setLoading(true);
    setError(null);

    try {
      const { data } = await axios.post<ChatResponse>("/api/ollama/chat", {
        model,
        messages,
      });

      if (data.success && data.response) {
        setError(null);
        return data.response;
      } else {
        const errorMessage = data.error || "Failed to get response from model";
        setError(errorMessage);
        return null;
      }
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.error
          ? err.response.data.error
          : "Error sending message to model";
      setError(errorMessage);
      console.error("Error sending message:", err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { sendMessage, loading, error };
}
