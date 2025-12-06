import axios from "axios";
import { Request, Response, Router } from "express";
import { OLLAMA_URL } from "./utils";

const router = Router();

// ---------------------------------------------------------------------------------------------------------------------
//  Route: GET /ollama/health
// ---------------------------------------------------------------------------------------------------------------------

router.get("/health", async (req: Request, res: Response) => {
  try {
    const url = `${OLLAMA_URL}/api/tags`;
    console.log(`Checking Ollama health at: ${url}`);

    const response = await axios.get(url, {
      timeout: 5000,
    });

    res.json({
      success: true,
      available: true,
      message: "Ollama is running and accessible",
      url: OLLAMA_URL,
    });
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const errorCode = error.code;
      const statusCode = error.response?.status;

      if (errorCode === "ECONNREFUSED" || errorCode === "ENOTFOUND") {
        res.json({
          success: false,
          available: false,
          message: "Ollama is not running or not accessible",
          url: OLLAMA_URL,
          error: `Could not connect to ${OLLAMA_URL}. Error code: ${errorCode}`,
        });
        return;
      }

      if (errorCode === "ETIMEDOUT") {
        res.json({
          success: false,
          available: false,
          message: "Connection to Ollama timed out",
          url: OLLAMA_URL,
          error: `Timeout connecting to ${OLLAMA_URL}`,
        });
        return;
      }

      res.json({
        success: false,
        available: false,
        message: "Error checking Ollama status",
        url: OLLAMA_URL,
        error: error.message,
        statusCode,
      });
      return;
    }

    res.json({
      success: false,
      available: false,
      message: "Unknown error while checking Ollama status",
      url: OLLAMA_URL,
      error: error instanceof Error ? error.message : "Unknown error",
    });
  }
});

export default router;
