import axios from "axios";
import { Response } from "express";
import { supportsChat, handleOllamaError } from "../utils";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios.isAxiosError
const mockIsAxiosError = jest.fn();
(axios.isAxiosError as any) = mockIsAxiosError;

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: supportsChat
// ---------------------------------------------------------------------------------------------------------------------

describe("supportsChat", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockIsAxiosError.mockClear();
  });

  it("should return true when model supports chat (200 status)", async () => {
    mockedAxios.post.mockResolvedValue({
      status: 200,
      data: { message: { content: "test" } },
    } as any);

    const result = await supportsChat("test-model");

    expect(result).toBe(true);
    expect(mockedAxios.post).toHaveBeenCalledWith(
      expect.stringContaining("/api/chat"),
      expect.objectContaining({
        model: "test-model",
        messages: [{ role: "user", content: "hi" }],
      }),
      expect.any(Object)
    );
  });

  it("should return true when model supports chat (400 status)", async () => {
    mockedAxios.post.mockResolvedValue({
      status: 400,
      data: {},
    } as any);

    const result = await supportsChat("test-model");

    expect(result).toBe(true);
  });

  it("should return false when model not found (404 status)", async () => {
    const error = {
      response: { status: 404 },
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.post.mockRejectedValue(error);

    const result = await supportsChat("non-existent-model");

    expect(result).toBe(false);
  });

  it("should return true on timeout errors", async () => {
    const error = {
      code: "ETIMEDOUT",
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.post.mockRejectedValue(error);

    const result = await supportsChat("test-model");

    expect(result).toBe(true);
  });

  it("should return true on connection errors", async () => {
    const error = {
      code: "ECONNREFUSED",
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.post.mockRejectedValue(error);

    const result = await supportsChat("test-model");

    expect(result).toBe(true);
  });
});

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: handleOllamaError
// ---------------------------------------------------------------------------------------------------------------------

describe("handleOllamaError", () => {
  let mockResponse: Partial<Response>;
  const originalConsoleError = console.error;

  beforeEach(() => {
    mockResponse = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn().mockReturnThis(),
    };
    jest.clearAllMocks();
    console.error = jest.fn(); // Mock console.error to avoid noise in test output
  });

  afterEach(() => {
    console.error = originalConsoleError;
  });

  it("should handle ECONNREFUSED error", () => {
    const error = {
      code: "ECONNREFUSED",
      message: "Connection refused",
    };
    mockIsAxiosError.mockReturnValue(true);

    handleOllamaError(error, mockResponse as Response, "http://localhost:11434");

    expect(mockResponse.status).toHaveBeenCalledWith(503);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      error: "Ollama is not running. Make sure Ollama is installed and running.",
      details: "Could not connect to http://localhost:11434. Error code: ECONNREFUSED",
    });
  });

  it("should handle ETIMEDOUT error", () => {
    const error = {
      code: "ETIMEDOUT",
      message: "Timeout",
    };
    mockIsAxiosError.mockReturnValue(true);

    handleOllamaError(error, mockResponse as Response, "http://localhost:11434");

    expect(mockResponse.status).toHaveBeenCalledWith(504);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      error: "Connection to Ollama timed out",
      details: "Timeout connecting to http://localhost:11434",
    });
  });

  it("should handle other axios errors", () => {
    const error = {
      code: "SOME_ERROR",
      message: "Some error",
      response: { status: 500 },
    };
    mockIsAxiosError.mockReturnValue(true);

    handleOllamaError(error, mockResponse as Response, "http://localhost:11434");

    expect(mockResponse.status).toHaveBeenCalledWith(500);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      error: "Error querying Ollama",
      details: "Some error",
      code: "SOME_ERROR",
    });
  });

  it("should handle unknown errors", () => {
    const error = new Error("Unknown error");
    mockIsAxiosError.mockReturnValue(false);

    handleOllamaError(error, mockResponse as Response, "http://localhost:11434");

    expect(mockResponse.status).toHaveBeenCalledWith(500);
    expect(mockResponse.json).toHaveBeenCalledWith({
      success: false,
      error: "Unknown error",
      details: "Unknown error",
    });
  });
});

