import { Router } from "express";
import { prisma } from "../db.js";
import { runGeneration } from "../generation/engine.js";

const router = Router();

router.post("/", async (req, res, next) => {
  try {
    const { datasetId, modelId, prompt, targetCount, batchSize, temperature } = req.body;

    if (!datasetId || !modelId || !prompt || !targetCount) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    const dataset = await prisma.dataset.findUnique({ where: { id: datasetId } });
    if (!dataset) {
      return res.status(404).json({ error: "Dataset not found" });
    }

    const run = await prisma.generationRun.create({
      data: {
        datasetId,
        modelId,
        prompt,
        config: {
          temperature: temperature ?? 0.7,
          batchSize: batchSize ?? 20,
          targetCount,
        },
        status: "QUEUED",
        totalTarget: targetCount,
      },
    });

    runGeneration({
      datasetId,
      modelId,
      prompt,
      targetCount,
      batchSize: batchSize ?? 20,
      temperature: temperature ?? 0.7,
    }).catch((err) => {
      console.error("Generation error:", err);
    });

    res.status(201).json(run);
  } catch (error) {
    next(error);
  }
});

router.get("/:runId", async (req, res, next) => {
  try {
    const { runId } = req.params;
    const run = await prisma.generationRun.findUnique({
      where: { id: runId },
    });

    if (!run) {
      return res.status(404).json({ error: "Run not found" });
    }

    res.json(run);
  } catch (error) {
    next(error);
  }
});

export default router;