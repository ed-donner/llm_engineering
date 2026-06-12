import { Router } from "express";
import { prisma } from "../db.js";

const router = Router();

router.get("/", async (req, res, next) => {
  try {
    const datasets = await prisma.dataset.findMany({
      orderBy: { createdAt: "desc" },
      select: {
        id: true,
        name: true,
        description: true,
        createdAt: true,
        updatedAt: true,
        _count: { select: { records: true } },
      },
    });
    res.json(datasets);
  } catch (error) {
    next(error);
  }
});

router.post("/", async (req, res, next) => {
  try {
    const { name, description, schema } = req.body;
    if (!name || !schema) {
      return res.status(400).json({ error: "name and schema are required" });
    }
    const dataset = await prisma.dataset.create({
      data: { name, description, schema },
    });
    res.status(201).json(dataset);
  } catch (error) {
    next(error);
  }
});

router.get("/:id", async (req, res, next) => {
  try {
    const { id } = req.params;
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 50;
    const skip = (page - 1) * limit;

    const dataset = await prisma.dataset.findUnique({
      where: { id },
      include: {
        records: {
          orderBy: { rowIndex: "asc" },
          skip,
          take: limit,
        },
        runs: {
          orderBy: { createdAt: "desc" },
          take: 1,
        },
      },
    });

    if (!dataset) {
      return res.status(404).json({ error: "Dataset not found" });
    }

    const totalRecords = await prisma.record.count({ where: { datasetId: id } });

    res.json({
      ...dataset,
      pagination: {
        page,
        limit,
        totalRecords,
        totalPages: Math.ceil(totalRecords / limit),
      },
    });
  } catch (error) {
    next(error);
  }
});

router.delete("/:id", async (req, res, next) => {
  try {
    const { id } = req.params;
    await prisma.dataset.delete({ where: { id } });
    res.status(204).send();
  } catch (error) {
    next(error);
  }
});

router.get("/:id/records", async (req, res, next) => {
  try {
    const { id } = req.params;
    const page = parseInt(req.query.page as string) || 1;
    const limit = parseInt(req.query.limit as string) || 100;
    const skip = (page - 1) * limit;

    const [records, total] = await Promise.all([
      prisma.record.findMany({
        where: { datasetId: id },
        orderBy: { rowIndex: "asc" },
        skip,
        take: limit,
      }),
      prisma.record.count({ where: { datasetId: id } }),
    ]);

    res.json({
      records,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    });
  } catch (error) {
    next(error);
  }
});

router.get("/:id/export/json", async (req, res, next) => {
  try {
    const { id } = req.params;
    const dataset = await prisma.dataset.findUnique({ where: { id } });

    if (!dataset) {
      return res.status(404).json({ error: "Dataset not found" });
    }

    const records = await prisma.record.findMany({
      where: { datasetId: id },
      orderBy: { rowIndex: "asc" },
      select: { data: true },
    });

    const data = records.map((r) => r.data);

    res.setHeader("Content-Type", "application/json");
    res.setHeader("Content-Disposition", `attachment; filename="${dataset.name}.json"`);

    res.write("[\n");
    for (let i = 0; i < data.length; i++) {
      const comma = i < data.length - 1 ? "," : "";
      res.write(JSON.stringify(data[i], null, 2) + comma);
      if (i % 100 === 0) await new Promise((r) => setImmediate(r));
    }
    res.write("\n]");
    res.end();
  } catch (error) {
    next(error);
  }
});

router.get("/:id/export/csv", async (req, res, next) => {
  try {
    const { id } = req.params;
    const dataset = await prisma.dataset.findUnique({ where: { id } });

    if (!dataset) {
      return res.status(404).json({ error: "Dataset not found" });
    }

    const schema = dataset.schema as { name: string }[];
    const fields = schema.map((f) => f.name);

    const records = await prisma.record.findMany({
      where: { datasetId: id },
      orderBy: { rowIndex: "asc" },
      select: { data: true },
    });

    res.setHeader("Content-Type", "text/csv");
    res.setHeader("Content-Disposition", `attachment; filename="${dataset.name}.csv"`);

    res.write(fields.join(",") + "\n");

    for (const record of records) {
      const row = fields.map((field) => {
        const value = record.data[field];
        if (value === null || value === undefined) return "";
        const str = String(value);
        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
          return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
      });
      res.write(row.join(",") + "\n");

      if (record.rowIndex % 100 === 0) await new Promise((r) => setImmediate(r));
    }

    res.end();
  } catch (error) {
    next(error);
  }
});

router.get("/:id/export/sql", async (req, res, next) => {
  try {
    const { id } = req.params;
    const dataset = await prisma.dataset.findUnique({ where: { id } });

    if (!dataset) {
      return res.status(404).json({ error: "Dataset not found" });
    }

    const schema = dataset.schema as { name: string }[];
    const fields = schema.map((f) => f.name);
    const tableName = dataset.name.toLowerCase().replace(/[^a-z0-9]/g, "_");

    const records = await prisma.record.findMany({
      where: { datasetId: id },
      orderBy: { rowIndex: "asc" },
      select: { data: true },
    });

    res.setHeader("Content-Type", "text/plain");
    res.setHeader("Content-Disposition", `attachment; filename="${dataset.name}.sql"`);

    const batchSize = 50;
    for (let i = 0; i < records.length; i += batchSize) {
      const batch = records.slice(i, i + batchSize);
      const values = batch.map((record) => {
        const row = fields.map((field) => {
          const value = record.data[field];
          if (value === null || value === undefined) return "NULL";
          if (typeof value === "boolean") return value ? "TRUE" : "FALSE";
          if (typeof value === "number") return String(value);
          if (typeof value === "object") return `'${JSON.stringify(value).replace(/'/g, "''")}'`;
          return `'${String(value).replace(/'/g, "''")}'`;
        });
        return `(${row.join(", ")})`;
      }).join(",\n");

      const stmt = `INSERT INTO ${tableName} (${fields.join(", ")}) VALUES \n${values};\n\n`;
      res.write(stmt);

      if (i % 500 === 0) await new Promise((r) => setImmediate(r));
    }

    res.end();
  } catch (error) {
    next(error);
  }
});

export default router;