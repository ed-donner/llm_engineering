import axios from "axios";
import { useEffect, useState } from "react";

export interface OllamaModel {
  name: string;
  size: number;
  modified_at: string;
}

interface OllamaResponse {
  success: boolean;
  models: OllamaModel[];
  error?: string;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Hook: useOllamaModels
// ---------------------------------------------------------------------------------------------------------------------

export function useOllamaModels() {
  const [models, setModels] = useState<OllamaModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const { data } = await axios.get<OllamaResponse>(
        "/api/ollama/models/installed"
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
          : "Error connecting to Ollama";
      setError(errorMessage);
      console.error("Error fetching Ollama models:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  return { models, loading, error, refetch: fetchModels };
}
