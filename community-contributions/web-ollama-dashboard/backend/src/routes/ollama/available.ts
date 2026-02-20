import axios from "axios";
import { Request, Response, Router } from "express";
import { OLLAMA_REGISTRY_URL, OLLAMA_URL, handleOllamaError } from "./utils";

const router = Router();

// ---------------------------------------------------------------------------------------------------------------------
//  Route: GET /ollama/models/available
// ---------------------------------------------------------------------------------------------------------------------

router.get("/models/available", async (req: Request, res: Response) => {
  try {
    // First, get installed models to filter them out
    let installedModels: string[] = [];
    try {
      const installedResponse = await axios.get(`${OLLAMA_URL}/api/tags`, {
        timeout: 5000,
      });
      installedModels = (installedResponse.data.models || []).map(
        (model: { name: string }) => model.name
      );
    } catch (err) {
      // If we can't get installed models, continue anyway
      console.warn("Could not fetch installed models for filtering:", err);
    }

    // Fetch available models dynamically from Ollama library page
    try {
      const libraryUrl = `${OLLAMA_REGISTRY_URL}/library`;
      const response = await axios.get(libraryUrl, {
        timeout: 10000,
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
      });

      // Extract model names and sizes from the HTML page
      // The Ollama library page contains model names in various formats
      // We'll try to extract them from data attributes, links, or text content
      const html = response.data;
      const modelMap = new Map<string, number>();

      // Try to extract model names and sizes from various patterns in the HTML
      // Pattern 1: Look for links to model pages (e.g., /library/llama2)
      const libraryLinkPattern = /\/library\/([a-zA-Z0-9\-_:]+)/g;
      let match;
      while ((match = libraryLinkPattern.exec(html)) !== null) {
        const modelName = match[1];
        if (modelName && !modelMap.has(modelName)) {
          modelMap.set(modelName, 0); // Size will be fetched separately if needed
        }
      }

      // Pattern 2: Look for model names in data attributes or JSON structures
      const jsonDataPattern =
        /"name"\s*:\s*"([a-zA-Z0-9\-_:]+)"[^}]*"size"\s*:\s*(\d+)/g;
      while ((match = jsonDataPattern.exec(html)) !== null) {
        const modelName = match[1];
        const size = parseInt(match[2], 10);
        if (modelName && !isNaN(size)) {
          modelMap.set(modelName, size);
        }
      }

      // Pattern 3: Look for model tags or identifiers with size information
      const modelWithSizePattern =
        /<[^>]*data-model="([a-zA-Z0-9\-_:]+)"[^>]*data-size="(\d+)"/g;
      while ((match = modelWithSizePattern.exec(html)) !== null) {
        const modelName = match[1];
        const size = parseInt(match[2], 10);
        if (modelName && !isNaN(size)) {
          modelMap.set(modelName, size);
        }
      }

      // Pattern 4: Try to extract size from text patterns (e.g., "3.8GB", "7B parameters")
      // This is a fallback if size is not in structured data
      const modelNames = Array.from(modelMap.keys());
      for (const modelName of modelNames) {
        if (modelMap.get(modelName) === 0) {
          // Try to find size information near the model name in the HTML
          const modelSectionPattern = new RegExp(
            `(?:${modelName.replace(
              /[.*+?^${}()|[\]\\]/g,
              "\\$&"
            )}[^<]*?)(?:size|Size|SIZE)[^<]*?([0-9.]+)\\s*(GB|MB|TB|B|billion|million)`,
            "i"
          );
          const sizeMatch = modelSectionPattern.exec(html);
          if (sizeMatch) {
            const sizeValue = parseFloat(sizeMatch[1]);
            const unit = sizeMatch[2].toUpperCase();
            let sizeInBytes = 0;
            if (unit.includes("GB")) {
              sizeInBytes = sizeValue * 1024 * 1024 * 1024;
            } else if (unit.includes("MB")) {
              sizeInBytes = sizeValue * 1024 * 1024;
            } else if (unit.includes("TB")) {
              sizeInBytes = sizeValue * 1024 * 1024 * 1024 * 1024;
            } else if (
              unit.includes("B") &&
              !unit.includes("GB") &&
              !unit.includes("MB")
            ) {
              sizeInBytes = sizeValue;
            }
            if (sizeInBytes > 0) {
              modelMap.set(modelName, Math.round(sizeInBytes));
            }
          }
        }
      }

      // Filter out installed models
      // Note: For available models (not yet installed), we assume they support chat
      // since most modern Ollama models support chat format
      const availableModels = Array.from(modelMap.entries())
        .filter(([modelName]) => !installedModels.includes(modelName))
        .map(([name, size]) => ({
          name,
          size,
          installed: false,
        }))
        .sort((a, b) => a.name.localeCompare(b.name));

      if (availableModels.length === 0) {
        // If no models found via scraping, return an informative error
        res.status(503).json({
          success: false,
          error:
            "Could not fetch available models dynamically. The Ollama library page structure may have changed.",
          details:
            "Please check https://ollama.com/library manually for available models.",
        });
        return;
      }

      res.json({
        success: true,
        count: availableModels.length,
        models: availableModels,
        note: "Models fetched dynamically from Ollama library. For the complete list, visit https://ollama.com/library",
      });
    } catch (registryError) {
      console.error(
        "Error fetching available models from Ollama library:",
        registryError
      );

      if (axios.isAxiosError(registryError)) {
        res.status(500).json({
          success: false,
          error: "Error fetching available models from Ollama library",
          details: registryError.message,
          note: "Please check https://ollama.com/library manually for available models.",
        });
      } else {
        res.status(500).json({
          success: false,
          error: "Unknown error while fetching available models",
          details:
            registryError instanceof Error
              ? registryError.message
              : "Unknown error",
          note: "Please check https://ollama.com/library manually for available models.",
        });
      }
    }
  } catch (error) {
    handleOllamaError(error, res, OLLAMA_REGISTRY_URL);
  }
});

export default router;
