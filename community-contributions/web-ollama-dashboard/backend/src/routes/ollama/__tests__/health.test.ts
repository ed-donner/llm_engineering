import request from "supertest";
import express from "express";
import axios from "axios";
import ollamaHealthRoutes from "../health";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios.isAxiosError
const mockIsAxiosError = jest.fn();
(axios.isAxiosError as any) = mockIsAxiosError;

const app = express();
app.use(express.json());
app.use("/api/ollama", ollamaHealthRoutes);

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: Ollama Health Route
// ---------------------------------------------------------------------------------------------------------------------

describe("GET /api/ollama/health", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsAxiosError.mockClear();
  });

  it("should return success when Ollama is available", async () => {
    mockedAxios.get.mockResolvedValue({
      status: 200,
      data: { models: [] },
    } as any);

    const response = await request(app).get("/api/ollama/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      success: true,
      available: true,
      message: "Ollama is running and accessible",
      url: expect.any(String),
    });
  });

  it("should return unavailable when connection is refused", async () => {
    const error = {
      code: "ECONNREFUSED",
      message: "Connection refused",
      response: undefined,
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.get.mockRejectedValue(error);

    const response = await request(app).get("/api/ollama/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      success: false,
      available: false,
      message: "Ollama is not running or not accessible",
      url: expect.any(String),
      error: expect.stringContaining("ECONNREFUSED"),
    });
  });

  it("should return unavailable when connection times out", async () => {
    const error = {
      code: "ETIMEDOUT",
      message: "Timeout",
      response: undefined,
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.get.mockRejectedValue(error);

    const response = await request(app).get("/api/ollama/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      success: false,
      available: false,
      message: "Connection to Ollama timed out",
      url: expect.any(String),
      error: expect.stringContaining("Timeout"),
    });
  });

  it("should handle unknown errors", async () => {
    const error = new Error("Unknown error");
    mockIsAxiosError.mockReturnValue(false);
    mockedAxios.get.mockRejectedValue(error);

    const response = await request(app).get("/api/ollama/health");

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      success: false,
      available: false,
      message: "Unknown error while checking Ollama status",
      url: expect.any(String),
      error: "Unknown error",
    });
  });
});

