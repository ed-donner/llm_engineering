import express from "express";
import { fileURLToPath } from "url";
import { dirname, join } from "path";
import { errorHandler } from "./middleware/error.js";
import datasetRoutes from "./routes/datasets.js";
import modelRoutes from "./routes/models.js";
import generateRoutes from "./routes/generate.js";
import templateRoutes from "./routes/templates.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.use(express.static(join(__dirname, "../public")));

app.use("/api/datasets", datasetRoutes);
app.use("/api/models", modelRoutes);
app.use("/api/generate", generateRoutes);
app.use("/api/templates", templateRoutes);

app.get("/api/health", (req, res) => {
  res.json({ status: "ok" });
});

app.use(errorHandler);

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});

export default app;