import { Router } from "express";
import { prisma } from "../db.js";

const router = Router();

router.get("/", async (req, res, next) => {
  try {
    const templates = await prisma.template.findMany({
      orderBy: { updatedAt: "desc" },
    });
    res.json(templates);
  } catch (error) {
    next(error);
  }
});

router.post("/", async (req, res, next) => {
  try {
    const { name, schema, prompt, modelId } = req.body;
    if (!name || !schema || !prompt) {
      return res.status(400).json({ error: "name, schema, and prompt are required" });
    }
    const template = await prisma.template.create({
      data: { name, schema, prompt, modelId },
    });
    res.status(201).json(template);
  } catch (error) {
    next(error);
  }
});

router.get("/:id", async (req, res, next) => {
  try {
    const { id } = req.params;
    const template = await prisma.template.findUnique({ where: { id } });
    if (!template) {
      return res.status(404).json({ error: "Template not found" });
    }
    res.json(template);
  } catch (error) {
    next(error);
  }
});

router.put("/:id", async (req, res, next) => {
  try {
    const { id } = req.params;
    const { name, schema, prompt, modelId } = req.body;
    const template = await prisma.template.update({
      where: { id },
      data: { name, schema, prompt, modelId },
    });
    res.json(template);
  } catch (error) {
    next(error);
  }
});

router.delete("/:id", async (req, res, next) => {
  try {
    const { id } = req.params;
    await prisma.template.delete({ where: { id } });
    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

export default router;