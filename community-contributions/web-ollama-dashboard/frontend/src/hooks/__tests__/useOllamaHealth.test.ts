import { renderHook, waitFor } from "@testing-library/react";
import axios from "axios";
import { useOllamaHealth } from "../useOllamaHealth";

// Mock axios
jest.mock("axios");
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios.isAxiosError
const mockIsAxiosError = jest.fn();
(axios.isAxiosError as any) = mockIsAxiosError;

// ---------------------------------------------------------------------------------------------------------------------
//  Tests: useOllamaHealth Hook
// ---------------------------------------------------------------------------------------------------------------------

describe("useOllamaHealth", () => {
  const originalConsoleError = console.error;

  beforeEach(() => {
    jest.clearAllMocks();
    mockIsAxiosError.mockClear();
    console.error = jest.fn(); // Mock console.error to avoid noise in test output
  });

  afterEach(() => {
    console.error = originalConsoleError;
  });

  it("should return loading true initially", () => {
    mockedAxios.get.mockImplementation(
      () =>
        new Promise(() => {
          // Never resolves to keep loading state
        })
    );

    const { result } = renderHook(() => useOllamaHealth());

    expect(result.current.loading).toBe(true);
    expect(result.current.available).toBe(null);
  });

  it("should set available to true when Ollama is available", async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        success: true,
        available: true,
        message: "Ollama is running and accessible",
      },
    } as any);

    const { result } = renderHook(() => useOllamaHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.available).toBe(true);
    expect(result.current.message).toBe("Ollama is running and accessible");
    expect(result.current.error).toBe(null);
  });

  it("should set available to false when Ollama is not available", async () => {
    mockedAxios.get.mockResolvedValue({
      data: {
        success: false,
        available: false,
        message: "Ollama is not running or not accessible",
        error: "Connection refused",
      },
    } as any);

    const { result } = renderHook(() => useOllamaHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.available).toBe(false);
    expect(result.current.message).toBe(
      "Ollama is not running or not accessible"
    );
    expect(result.current.error).toBe("Connection refused");
  });

  it("should handle axios errors", async () => {
    const axiosError = {
      response: {
        data: {
          error: "Network error",
        },
      },
    };
    mockIsAxiosError.mockReturnValue(true);
    mockedAxios.get.mockRejectedValue(axiosError);

    const { result } = renderHook(() => useOllamaHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.available).toBe(false);
    expect(result.current.error).toBe("Network error");
    expect(result.current.message).toBe("Unable to check Ollama status");
  });

  it("should handle non-axios errors", async () => {
    const error = new Error("Unknown error");
    mockIsAxiosError.mockReturnValue(false);
    mockedAxios.get.mockRejectedValue(error);

    const { result } = renderHook(() => useOllamaHealth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.available).toBe(false);
    expect(result.current.error).toBe("Error checking Ollama status");
    expect(result.current.message).toBe("Unable to check Ollama status");
  });
});
