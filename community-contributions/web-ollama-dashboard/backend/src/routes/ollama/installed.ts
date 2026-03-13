import axios from "axios";
import { Request, Response, Router } from "express";
import { OLLAMA_URL, handleOllamaError, supportsChat } from "./utils";

const router = Router();

// ---------------------------------------------------------------------------------------------------------------------
//  Route: GET /ollama/models/installed
// ---------------------------------------------------------------------------------------------------------------------

router.get("/models/installed", async (req: Request, res: Response) => {
  try {
    const url = `${OLLAMA_URL}/api/tags`;
    console.log(`Attempting to connect to Ollama at: ${url}`);

    const response = await axios.get(url, {
      timeout: 5000,
    });

    const allModels = response.data.models || [];

    // Filter models that support chat - check in parallel for better performance
    const chatChecks = await Promise.allSettled(
      allModels.map(
        async (model: { name: string; size: number; modified_at: string }) => {
          const supportsChatFormat = await supportsChat(model.name);
          return { model, supportsChatFormat };
        }
      )
    );

    const chatModels = chatChecks
      .filter(
        (result) =>
          result.status === "fulfilled" && result.value.supportsChatFormat
      )
      .map((result) => {
        if (result.status === "fulfilled") {
          return {
            name: result.value.model.name,
            size: result.value.model.size,
            modified_at: result.value.model.modified_at,
          };
        }
        return null;
      })
      .filter((model) => model !== null);

    res.json({
      success: true,
      count: chatModels.length,
      models: chatModels,
    });
  } catch (error) {
    handleOllamaError(error, res, OLLAMA_URL);
  }
});

export default router;
