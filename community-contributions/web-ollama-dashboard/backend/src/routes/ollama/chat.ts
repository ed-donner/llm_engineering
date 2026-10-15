import axios from "axios";
import { Request, Response, Router } from "express";
import { OLLAMA_URL, handleOllamaError } from "./utils";

const router = Router();

// ---------------------------------------------------------------------------------------------------------------------
//  Route: POST /ollama/chat
// ---------------------------------------------------------------------------------------------------------------------

router.post("/chat", async (req: Request, res: Response) => {
  try {
    console.log("Chat request payload:", JSON.stringify(req.body, null, 2));
    const { model, messages } = req.body;

    if (!model || typeof model !== "string") {
      res.status(400).json({
        success: false,
        error: "Model name is required",
      });
      return;
    }

    if (!Array.isArray(messages) || messages.length === 0) {
      res.status(400).json({
        success: false,
        error: "Messages array is required and cannot be empty",
      });
      return;
    }

    // Validate messages format
    for (const msg of messages) {
      if (!msg.role || !msg.content) {
        res.status(400).json({
          success: false,
          error: "Each message must have 'role' and 'content' fields",
        });
        return;
      }
      if (typeof msg.role !== "string" || typeof msg.content !== "string") {
        res.status(400).json({
          success: false,
          error: "Message 'role' and 'content' must be strings",
        });
        return;
      }
    }

    const url = `${OLLAMA_URL}/api/chat`;
    console.log(`Sending messages to model ${model} at ${url}`);

    const requestBody = {
      model,
      messages,
      stream: false,
    };

    const response = await axios.post(url, requestBody, {
      timeout: 300000, // 5 minutes timeout for LLM responses
      headers: {
        "Content-Type": "application/json",
      },
    });

    const responseText = response.data.message?.content || "";

    res.json({
      success: true,
      response: responseText,
      model,
    });
  } catch (error) {
    console.error("Error sending message to Ollama:", error);

    if (axios.isAxiosError(error)) {
      const errorCode = error.code;
      const errorMessage = error.message;
      const statusCode = error.response?.status;

      console.error("Axios error details:", {
        code: errorCode,
        message: errorMessage,
        status: statusCode,
        url: error.config?.url,
        model: req.body.model,
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
        console.error(`Timeout sending message to model: ${req.body.model}`);
        res.status(504).json({
          success: false,
          error: "Request timed out",
          details: `Timeout sending message to model. This may happen with large models or long responses.`,
        });
      } else {
        console.error(
          `Error sending message to model ${req.body.model}: ${errorMessage} (code: ${errorCode}, status: ${statusCode})`
        );
        res.status(statusCode || 500).json({
          success: false,
          error: "Error sending message to model",
          details: errorMessage,
          code: errorCode,
        });
      }
    } else {
      console.error("Unknown error type while sending message:", error);
      handleOllamaError(error, res, OLLAMA_URL);
    }
  }
});

export default router;
