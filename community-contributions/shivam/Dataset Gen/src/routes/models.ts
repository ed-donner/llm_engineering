import { Router } from "express";
import { openrouter } from "../generation/openrouter.js";

const router = Router();

router.get("/", async (req, res, next) => {
  try {
    const models = await openrouter.listModels();
    res.json(models);
  } catch (error) {
    next(error);
  }
});

router.post("/test", async (req, res, next) => {
  try {
    const { modelId } = req.body;
    if (!modelId) {
      return res.status(400).json({ error: "modelId is required" });
    }
    const success = await openrouter.testConnection(modelId);
    res.json({ success });
  } catch (error) {
    next(error);
  }
});

export default router;