import axios from "axios";
import { Request, Response, Router } from "express";
import { Readable } from "stream";
import { OLLAMA_URL, handleOllamaError } from "./utils";

const router = Router();

// ---------------------------------------------------------------------------------------------------------------------
//  Route: POST /ollama/models/install
// ---------------------------------------------------------------------------------------------------------------------

router.post("/models/install", async (req: Request, res: Response) => {
  try {
    const { modelName } = req.body;

    if (!modelName || typeof modelName !== "string") {
      res.status(400).json({
        success: false,
        error: "Model name is required",
      });
      return;
    }

    const url = `${OLLAMA_URL}/api/pull`;
    console.log(`Attempting to install model: ${modelName} at ${url}`);

    // Set up Server-Sent Events headers
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no");

    // Send initial connection message
    res.write(`data: ${JSON.stringify({ type: "start", model: modelName })}\n\n`);

    try {
      // Ollama pull endpoint returns streaming events
      const response = await axios.post(url, { name: modelName }, {
        timeout: 0, // No timeout for streaming
        responseType: "stream",
        headers: {
          "Content-Type": "application/json",
        },
      });

      // Process streaming response from Ollama
      const stream = response.data as Readable;
      let buffer = "";

      stream.on("data", (chunk: Buffer) => {
        buffer += chunk.toString();
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.trim()) {
            try {
              const event = JSON.parse(line);
              
              // Forward progress events to client
              const progressData = {
                type: "progress",
                status: event.status || "pulling",
                digest: event.digest || "",
                total: event.total || 0,
                completed: event.completed || 0,
                model: modelName,
              };

              res.write(`data: ${JSON.stringify(progressData)}\n\n`);
            } catch (parseError) {
              // Skip invalid JSON lines
              console.warn("Failed to parse Ollama event:", line);
            }
          }
        }
      });

      stream.on("end", () => {
        // Send completion message
        res.write(
          `data: ${JSON.stringify({
            type: "complete",
            success: true,
            message: `Model ${modelName} installed successfully`,
            model: modelName,
          })}\n\n`
        );
        res.end();
      });

      stream.on("error", (streamError: Error) => {
        console.error("Stream error:", streamError);
        res.write(
          `data: ${JSON.stringify({
            type: "error",
            success: false,
            error: "Error during installation",
            details: streamError.message,
          })}\n\n`
        );
        res.end();
      });
    } catch (streamError) {
      if (axios.isAxiosError(streamError)) {
        const errorCode = streamError.code;
        const errorMessage = streamError.message;
        const statusCode = streamError.response?.status;

        let errorResponse;
        if (errorCode === "ECONNREFUSED" || errorCode === "ENOTFOUND") {
          errorResponse = {
            type: "error",
            success: false,
            error:
              "Ollama is not running. Make sure Ollama is installed and running.",
            details: `Could not connect to ${OLLAMA_URL}. Error code: ${errorCode}`,
          };
        } else if (errorCode === "ETIMEDOUT") {
          errorResponse = {
            type: "error",
            success: false,
            error: "Installation timed out",
            details: `Timeout installing model. This may happen with large models.`,
          };
        } else {
          errorResponse = {
            type: "error",
            success: false,
            error: "Error installing model",
            details: errorMessage,
            code: errorCode,
          };
        }

        res.write(`data: ${JSON.stringify(errorResponse)}\n\n`);
        res.end();
      } else {
        res.write(
          `data: ${JSON.stringify({
            type: "error",
            success: false,
            error: "Unknown error",
            details:
              streamError instanceof Error
                ? streamError.message
                : "Unknown error",
          })}\n\n`
        );
        res.end();
      }
    }
  } catch (error) {
    handleOllamaError(error, res, OLLAMA_URL);
  }
});

export default router;
