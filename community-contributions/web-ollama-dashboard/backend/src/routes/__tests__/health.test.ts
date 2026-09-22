import express from "express";
import request from "supertest";
import healthRoutes from "../health";

const app = express();
app.use(express.json());
app.use("/api", healthRoutes);

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: Health Route
// ---------------------------------------------------------------------------------------------------------------------

describe("GET /api/health", () => {
  it("should return health status", async () => {
    const response = await request(app).get("/api/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      status: "ok",
      message: "Backend is running!",
    });
  });
});
