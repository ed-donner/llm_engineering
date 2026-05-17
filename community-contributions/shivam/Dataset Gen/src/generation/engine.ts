import { prisma } from "../db.js";
import { openrouter } from "./openrouter.js";
import { buildPrompt, Schema } from "./prompt-builder.js";
import { validateRecords } from "./validator.js";

interface GenerationConfig {
  datasetId: string;
  modelId: string;
  prompt: string;
  targetCount: number;
  batchSize: number;
  temperature: number;
}

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseJSONResponse(content: string): unknown[] {
  let jsonStr = content.trim();

  if (jsonStr.startsWith("```json")) {
    jsonStr = jsonStr.slice(7);
  } else if (jsonStr.startsWith("```")) {
    jsonStr = jsonStr.slice(3);
  }

  if (jsonStr.endsWith("```")) {
    jsonStr = jsonStr.slice(0, -3);
  }

  jsonStr = jsonStr.trim();

  const parsed = JSON.parse(jsonStr);
  if (Array.isArray(parsed)) {
    return parsed;
  }
  if (typeof parsed === "object" && parsed !== null && "records" in parsed) {
    return parsed.records as unknown[];
  }
  throw new Error("Response is not an array");
}

async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelay = 1000
): Promise<T> {
  let lastError: Error | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      if (attempt < maxRetries - 1) {
        const delay = baseDelay * Math.pow(2, attempt);
        await sleep(delay);
      }
    }
  }

  throw lastError;
}

export async function runGeneration(config: GenerationConfig): Promise<void> {
  const run = await prisma.generationRun.create({
    data: {
      datasetId: config.datasetId,
      modelId: config.modelId,
      prompt: config.prompt,
      config: {
        temperature: config.temperature,
        batchSize: config.batchSize,
        targetCount: config.targetCount,
      },
      status: "RUNNING",
      totalTarget: config.targetCount,
      startedAt: new Date(),
    },
  });

  try {
    const dataset = await prisma.dataset.findUnique({
      where: { id: config.datasetId },
    });

    if (!dataset) {
      throw new Error("Dataset not found");
    }

    const schema = dataset.schema as unknown as Schema;
    let generated = 0;

    while (generated < config.targetCount) {
      const remaining = config.targetCount - generated;
      const currentBatchSize = Math.min(config.batchSize, remaining);

      const { system, user } = buildPrompt(schema, currentBatchSize, config.prompt);

      const records = await withRetry(
        async () => {
          const content = await openrouter.chat({
            model: config.modelId,
            messages: [
              { role: "system", content: system },
              { role: "user", content: user },
            ],
            temperature: config.temperature,
          });
          return parseJSONResponse(content);
        },
        3,
        1500
      );

      const validRecords = validateRecords(records, schema);

      if (validRecords.length > 0) {
        const recordsToInsert = validRecords.map((record, index) => ({
          datasetId: config.datasetId,
          data: record as object,
          rowIndex: generated + index,
        }));

        await prisma.record.createMany({ data: recordsToInsert as any });
        generated += validRecords.length;
      }

      await prisma.generationRun.update({
        where: { id: run.id },
        data: { progress: generated },
      });
    }

    await prisma.generationRun.update({
      where: { id: run.id },
      data: {
        status: "COMPLETED",
        progress: generated,
        completedAt: new Date(),
      },
    });
  } catch (error) {
    await prisma.generationRun.update({
      where: { id: run.id },
      data: {
        status: "FAILED",
        error: (error as Error).message,
        completedAt: new Date(),
      },
    });
    throw error;
  }
}