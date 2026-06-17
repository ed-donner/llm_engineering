import axios from "axios";
import { useState } from "react";

interface DeleteModelResponse {
  success: boolean;
  message?: string;
  error?: string;
  details?: string;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Hook: useDeleteModel
// ---------------------------------------------------------------------------------------------------------------------

export function useDeleteModel() {
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteModel = async (modelName: string): Promise<boolean> => {
    setDeleting(true);
    setError(null);

    try {
      const { data } = await axios.post<DeleteModelResponse>(
        "/api/ollama/models/delete",
        { modelName }
      );

      if (data.success) {
        setError(null);
        return true;
      } else {
        setError(data.error || "Failed to delete model");
        return false;
      }
    } catch (err) {
      const errorMessage =
        axios.isAxiosError(err) && err.response?.data?.error
          ? err.response.data.error
          : "Error deleting model";
      setError(errorMessage);
      console.error("Error deleting model:", err);
      return false;
    } finally {
      setDeleting(false);
    }
  };

  return { deleteModel, deleting, error };
}
