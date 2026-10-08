import request from "supertest";
import express from "express";
import axios from "axios";
import chatRoutes from "../chat";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios.isAxiosError
const mockIsAxiosError = jest.fn();
(axios.isAxiosError as any) = mockIsAxiosError;

const app = express();
app.use(express.json());
app.use("/api/ollama", chatRoutes);

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: Chat Route
// ---------------------------------------------------------------------------------------------------------------------

describe("POST /api/ollama/chat", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsAxiosError.mockClear();
  });

  it("should return error when model is missing", async () => {
    const response = await request(app)
      .post("/api/ollama/chat")
      .send({ messages: [{ role: "user", content: "test" }] });

    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      success: false,
      error: "Model name is required",
    });
  });

  it("should return error when messages are missing", async () => {
    const response = await request(app)
      .post("/api/ollama/chat")
      .send({ model: "test-model" });

    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      success: false,
      error: "Messages array is required and cannot be empty",
    });
  });

  it("should return error when messages array is empty", async () => {
    const response = await request(app)
      .post("/api/ollama/chat")
      .send({ model: "test-model", messages: [] });

    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      success: false,
      error: "Messages array is required and cannot be empty",
    });
  });

  it("should return error when message is missing role", async () => {
    const response = await request(app)
      .post("/api/ollama/chat")
      .send({
        model: "test-model",
        messages: [{ content: "test" }],
      });

    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      success: false,
      error: "Each message must have 'role' and 'content' fields",
    });
  });

  it("should return error when message is missing content", async () => {
    const response = await request(app)
      .post("/api/ollama/chat")
      .send({
        model: "test-model",
        messages: [{ role: "user" }],
      });

    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      success: false,
      error: "Each message must have 'role' and 'content' fields",
    });
  });

  it("should return error when role is not a string", async () => {
    const response = await request(app)
      .post("/api/ollama/chat")
      .send({
        model: "test-model",
        messages: [{ role: 123, content: "test" }],
      });

    expect(response.status).toBe(400);
    expect(response.body).toEqual({
      success: false,
      error: "Message 'role' and 'content' must be strings",
    });
  });

  it("should successfully send chat message", async () => {
    mockedAxios.post.mockResolvedValue({
      status: 200,
      data: {
        message: {
          content: "Hello! How can I help you?",
        },
      },
    } as any);

    const response = await request(app)
      .post("/api/ollama/chat")
      .send({
        model: "test-model",
        messages: [
          { role: "system", content: "You are a helpful assistant" },
          { role: "user", content: "Hello" },
        ],
      });

    expect(response.status).toBe(200);
    expect(response.body).toEqual({
      success: true,
      response: "Hello! How can I help you?",
      model: "test-model",
    });
    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining("/api/chat"),
      expect.objectContaining({
        model: "test-model",
        messages: [
          { role: "system", content: "You are a helpful assistant" },
          { role: "user", content: "Hello" },
        ],
        stream: false,
      }),
      expect.any(Object)
    );
  });

  it("should handle Ollama connection errors", async () => {
    const error = {
      code: "ECONNREFUSED",
      message: "Connection refused",
      response: undefined,
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.post.mockRejectedValue(error);

    const response = await request(app)
      .post("/api/ollama/chat")
      .send({
        model: "test-model",
        messages: [{ role: "user", content: "test" }],
      });

    expect(response.status).toBe(503);
    expect(response.body).toEqual({
      success: false,
      error: "Ollama is not running. Make sure Ollama is installed and running.",
      details: expect.stringContaining("ECONNREFUSED"),
    });
  });
});

