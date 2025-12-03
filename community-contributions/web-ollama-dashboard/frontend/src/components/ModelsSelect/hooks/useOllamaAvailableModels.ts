import axios from "axios";
import { useEffect, useState } from "react";

export interface OllamaAvailableModel {
  name: string;
  size: number;
  installed: boolean;
}

interface OllamaAvailableResponse {
  success: boolean;
  models: OllamaAvailableModel[];
  error?: string;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Hook: useOllamaAvailableModels
// ---------------------------------------------------------------------------------------------------------------------

export function useOllamaAvailableModels() {
  const [models, setModels] = useState<OllamaAvailableModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<OllamaAvailableResponse>(
        "/api/ollama/models/available"
      );

      if (data.success) {
        setModels(data.models);
        setError(null);
      } else {
        setError(data.error || "Unknown error");
      }
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.error
          ? err.response.data.error
          : "Error fetching available models";
      setError(errorMessage);
      console.error("Error fetching available Ollama models:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return { models, loading, error, refetch: fetchModels };
}
