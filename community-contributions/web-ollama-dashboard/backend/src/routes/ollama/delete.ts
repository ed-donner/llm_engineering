import axios from "axios";
import { Request, Response, Router } from "express";
import { OLLAMA_URL, handleOllamaError } from "./utils";

const router = Router();

// ---------------------------------------------------------------------------------------------------------------------
//  Route: POST /ollama/models/delete
// ---------------------------------------------------------------------------------------------------------------------

router.post("/models/delete", async (req: Request, res: Response) => {
  try {
    const { modelName } = req.body;

    if (!modelName || typeof modelName !== "string") {
      res.status(400).json({
        success: false,
        error: "Model name is required",
      });
      return;
    }

    const url = `${OLLAMA_URL}/api/delete`;
    console.log(`Attempting to delete model: ${modelName} at ${url}`);

    // Ollama delete endpoint expects a DELETE request with the model name in the body
    const response = await axios.delete(url, {
      data: { name: modelName },
      timeout: 30000, // 30 seconds timeout
      headers: {
        "Content-Type": "application/json",
      },
    });

    res.json({
      success: true,
      message: `Model ${modelName} deleted successfully`,
      model: modelName,
    });
  } catch (error) {
    console.error("Error deleting model:", error);

    if (axios.isAxiosError(error)) {
      const errorCode = error.code;
      const errorMessage = error.message;
      const statusCode = error.response?.status;

      console.error("Axios error details:", {
        code: errorCode,
        message: errorMessage,
        status: statusCode,
        url: error.config?.url,
        modelName: req.body.modelName,
      });

      if (errorCode === "ECONNREFUSED" || errorCode === "ENOTFOUND") {
        console.error(
          `Cannot connect to Ollama at ${OLLAMA_URL}. Error code: ${errorCode}`
        );
        res.status(503).json({
          success: false,
          error:
            "Ollama is not running. Make sure Ollama is installed and running.",
          details: `Could not connect to ${OLLAMA_URL}. Error code: ${errorCode}`,
        });
      } else if (errorCode === "ETIMEDOUT") {
        console.error(`Timeout deleting model: ${req.body.modelName}`);
        res.status(504).json({
          success: false,
          error: "Deletion timed out",
          details: `Timeout deleting model.`,
        });
      } else {
        console.error(
          `Error deleting model ${req.body.modelName}: ${errorMessage} (code: ${errorCode}, status: ${statusCode})`
        );
        res.status(statusCode || 500).json({
          success: false,
          error: "Error deleting model",
          details: errorMessage,
          code: errorCode,
        });
      }
    } else {
      console.error("Unknown error type while deleting model:", error);
      handleOllamaError(error, res, OLLAMA_URL);
    }
  }
});

export default router;
