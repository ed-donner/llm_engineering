import request from "supertest";
import express from "express";
import helloRoutes from "../hello";

const app = express();
app.use(express.json());
app.use("/api", helloRoutes);

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: Hello Route
// ---------------------------------------------------------------------------------------------------------------------

describe("GET /api/hello", () => {
  it("should return hello message", async () => {
    const response = await request(app).get("/api/hello");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      message: "Hello from Express + TypeScript!",
    });
  });
});

