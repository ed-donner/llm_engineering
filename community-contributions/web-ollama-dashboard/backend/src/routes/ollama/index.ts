import { Router } from "express";
import availableRoutes from "./available";
import chatRoutes from "./chat";
import deleteRoutes from "./delete";
import healthRoutes from "./health";
import installRoutes from "./install";
import installedRoutes from "./installed";

const router = Router();

// Mount route handlers
router.use("/ollama", healthRoutes);
router.use("/ollama", installedRoutes);
router.use("/ollama", availableRoutes);
router.use("/ollama", installRoutes);
router.use("/ollama", deleteRoutes);
router.use("/ollama", chatRoutes);

export default router;
