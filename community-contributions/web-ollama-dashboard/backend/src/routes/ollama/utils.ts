import axios from "axios";
import { Response } from "express";

export const OLLAMA_URL = process.env.OLLAMA_URL || "http://127.0.0.1:11434";
export const OLLAMA_REGISTRY_URL =
  process.env.OLLAMA_REGISTRY_URL || "https://ollama.com";

// ---------------------------------------------------------------------------------------------------------------------
//  Function: supportsChat
// ---------------------------------------------------------------------------------------------------------------------

export const supportsChat = async (modelName: string): Promise<boolean> => {
  try {
    // Try to make a minimal chat request to check if the model supports chat
    const url = `${OLLAMA_URL}/api/chat`;
    const testResponse = await axios.post(
      url,
      {
        model: modelName,
        messages: [{ role: "user", content: "hi" }],
        stream: false,
      },
      {
        timeout: 3000, // Very short timeout for quick check
        validateStatus: (status) => status < 500, // Don't throw on 4xx errors
      }
    );

    // If we get a 200 response, the model supports chat
    // If we get 400, it might be a validation error but the endpoint exists
    // If we get 404, the model doesn't exist or doesn't support chat
    if (testResponse.status === 200) {
      return true;
    }
    if (testResponse.status === 400) {
      // 400 could mean validation error, but endpoint exists - assume it supports chat
      return true;
    }
    return false;
  } catch (error) {
    // If it's a timeout or connection error, assume it supports chat
    // (we don't want to exclude models due to temporary network issues)
    if (axios.isAxiosError(error)) {
      const statusCode = error.response?.status;
      if (statusCode === 404) {
        return false; // Model not found
      }
      // For timeouts or connection errors, assume it supports chat
      // to avoid blocking the list unnecessarily
      return true;
    }
    // For unknown errors, assume it supports chat to avoid blocking
    return true;
  }
};

// ---------------------------------------------------------------------------------------------------------------------
//  Function: handleOllamaError
// ---------------------------------------------------------------------------------------------------------------------

export const handleOllamaError = (
  error: unknown,
  res: Response,
  OLLAMA_URL: string
) => {
  console.error("Error fetching from Ollama:", error);
  console.error("OLLAMA_URL:", OLLAMA_URL);

  if (axios.isAxiosError(error)) {
    const errorCode = error.code;
    const errorMessage = error.message;
    const statusCode = error.response?.status;

    console.error("Axios error details:", {
      code: errorCode,
      message: errorMessage,
      status: statusCode,
      url: error.config?.url,
    });

    if (errorCode === "ECONNREFUSED" || errorCode === "ENOTFOUND") {
      res.status(503).json({
        success: false,
        error:
          "Ollama is not running. Make sure Ollama is installed and running.",
        details: `Could not connect to ${OLLAMA_URL}. Error code: ${errorCode}`,
      });
    } else if (errorCode === "ETIMEDOUT") {
      res.status(504).json({
        success: false,
        error: "Connection to Ollama timed out",
        details: `Timeout connecting to ${OLLAMA_URL}`,
      });
    } else {
      res.status(statusCode || 500).json({
        success: false,
        error: "Error querying Ollama",
        details: errorMessage,
        code: errorCode,
      });
    }
  } else {
    res.status(500).json({
      success: false,
      error: "Unknown error",
      details: error instanceof Error ? error.message : "Unknown error",
    });
  }
};
