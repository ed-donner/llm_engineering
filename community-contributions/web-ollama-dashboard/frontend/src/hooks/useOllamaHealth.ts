import axios from "axios";
import { useEffect, useState } from "react";

interface OllamaHealthResponse {
  success: boolean;
  available: boolean;
  message?: string;
  url?: string;
  error?: string;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Hook: useOllamaHealth
// ---------------------------------------------------------------------------------------------------------------------

export function useOllamaHealth() {
  const [available, setAvailable] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      setLoading(true);
      setError(null);

      try {
        const { data } = await axios.get<OllamaHealthResponse>(
          "/api/ollama/health"
        );

        setAvailable(data.available);
        setMessage(data.message || null);
        if (!data.available && data.error) {
          setError(data.error);
        }
      } catch (err) {
        setAvailable(false);
        const errorMessage =
          axios.isAxiosError(err) && err.response?.data?.error
            ? err.response.data.error
            : "Error checking Ollama status";
        setError(errorMessage);
        setMessage("Unable to check Ollama status");
        console.error("Error checking Ollama health:", err);
      } finally {
        setLoading(false);
      }
    };

    checkHealth();
  }, []);

  return { available, loading, error, message };
}
