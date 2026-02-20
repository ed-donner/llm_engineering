import { renderHook, waitFor } from "@testing-library/react";
import axios from "axios";
import { useChat } from "../useChat";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios.isAxiosError
const mockIsAxiosError = jest.fn();
(axios.isAxiosError as any) = mockIsAxiosError;

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: useChat Hook
// ---------------------------------------------------------------------------------------------------------------------

describe("useChat", () => {
  const originalConsoleError = console.error;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIsAxiosError.mockClear();
    console.error = jest.fn(); // Mock console.error to avoid noise in test output
  });

  afterEach(() => {
    console.error = originalConsoleError;
  });

  it("should have initial loading state as false", () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it("should send message successfully", async () => {
    mockedAxios.post.mockResolvedValue({
      data: {
        success: true,
        response: "Hello! How can I help you?",
      },
    } as any);

    const { result } = renderHook(() => useChat());

    const response = await result.current.sendMessage({
      model: "test-model",
      messages: [{ role: "user", content: "Hello" }],
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(response).toBe("Hello! How can I help you?");
    expect(result.current.error).toBe(null);
    expect(mockedAxios.post).toHaveBeenCalledWith("/api/ollama/chat", {
      model: "test-model",
      messages: [{ role: "user", content: "Hello" }],
    });
  });

  it("should handle error when response is not successful", async () => {
    mockedAxios.post.mockResolvedValue({
      data: {
        success: false,
        error: "Model not found",
      },
    } as any);

    const { result } = renderHook(() => useChat());

    const response = await result.current.sendMessage({
      model: "non-existent-model",
      messages: [{ role: "user", content: "Hello" }],
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(response).toBe(null);
    expect(result.current.error).toBe("Model not found");
  });

  it("should handle axios errors", async () => {
    const axiosError = {
      response: {
        data: {
          error: "Connection refused",
        },
      },
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.post.mockRejectedValue(axiosError);

    const { result } = renderHook(() => useChat());

    const response = await result.current.sendMessage({
      model: "test-model",
      messages: [{ role: "user", content: "Hello" }],
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(response).toBe(null);
    expect(result.current.error).toBe("Connection refused");
  });

  it("should handle non-axios errors", async () => {
    const error = new Error("Network error");
    mockIsAxiosError.mockReturnValue(false);
    mockedAxios.post.mockRejectedValue(error);

    const { result } = renderHook(() => useChat());

    const response = await result.current.sendMessage({
      model: "test-model",
      messages: [{ role: "user", content: "Hello" }],
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(response).toBe(null);
    expect(result.current.error).toBe("Error sending message to model");
  });

  it("should set loading to true while sending message", async () => {
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    mockedAxios.post.mockReturnValue(promise as any);

    const { result } = renderHook(() => useChat());

    const sendPromise = result.current.sendMessage({
      model: "test-model",
      messages: [{ role: "user", content: "Hello" }],
    });

    // Wait a bit for the state to update
    await waitFor(
      () => {
        expect(result.current.loading).toBe(true);
      },
      { timeout: 1000 }
    );

    // Resolve the promise
    resolvePromise!({
      data: {
        success: true,
        response: "Response",
      },
    });

    await sendPromise;

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });
});

