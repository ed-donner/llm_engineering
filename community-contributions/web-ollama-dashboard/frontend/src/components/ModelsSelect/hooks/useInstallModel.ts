import { useState } from "react";

interface ProgressEvent {
  type: "start" | "progress" | "complete" | "error";
  status?: string;
  digest?: string;
  total?: number;
  completed?: number;
  model?: string;
  success?: boolean;
  message?: string;
  error?: string;
  details?: string;
  code?: string;
}

interface InstallProgress {
  status: string;
  progress: number; // 0-100
  total: number;
  completed: number;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Hook: useInstallModel
// ---------------------------------------------------------------------------------------------------------------------

export function useInstallModel() {
  const [installing, setInstalling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<InstallProgress | null>(null);

  const installModel = async (
    modelName: string,
    onProgress?: (progress: InstallProgress) => void
  ): Promise<boolean> => {
    setInstalling(true);
    setError(null);
    setProgress(null);

    return new Promise((resolve) => {
      const eventSource = new EventSource(
        `/api/ollama/models/install?modelName=${encodeURIComponent(modelName)}`,
        {
          // Note: EventSource doesn't support POST, so we'll need to use a workaround
        }
      );

      // Since EventSource only supports GET, we'll use fetch with streaming
      fetch("/api/ollama/models/install", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ modelName }),
      })
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const reader = response.body?.getReader();
          const decoder = new TextDecoder();
          let buffer = "";

          if (!reader) {
            throw new Error("Response body is not readable");
          }

          const processStream = async () => {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n");
              buffer = lines.pop() || "";

              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  try {
                    const event: ProgressEvent = JSON.parse(
                      line.substring(6)
                    );

                    if (event.type === "start") {
                      setProgress({
                        status: "Starting installation...",
                        progress: 0,
                        total: 0,
                        completed: 0,
                      });
                    } else if (event.type === "progress") {
                      const progressValue =
                        event.total && event.total > 0
                          ? Math.round(
                              (event.completed! / event.total) * 100
                            )
                          : 0;

                      const progressData: InstallProgress = {
                        status: event.status || "Installing...",
                        progress: progressValue,
                        total: event.total || 0,
                        completed: event.completed || 0,
                      };

                      setProgress(progressData);
                      onProgress?.(progressData);
                    } else if (event.type === "complete") {
                      setProgress({
                        status: "Installation complete!",
                        progress: 100,
                        total: 0,
                        completed: 0,
                      });
                      setInstalling(false);
                      resolve(true);
                      return;
                    } else if (event.type === "error") {
                      setError(event.error || "Failed to install model");
                      setProgress(null);
                      setInstalling(false);
                      resolve(false);
                      return;
                    }
                  } catch (parseError) {
                    console.warn("Failed to parse progress event:", line);
                  }
                }
              }
            }
          };

          processStream().catch((streamError) => {
            setError(
              streamError instanceof Error
                ? streamError.message
                : "Error reading installation progress"
            );
            setInstalling(false);
            resolve(false);
          });
        })
        .catch((err) => {
          const errorMessage =
            err instanceof Error ? err.message : "Error installing model";
          setError(errorMessage);
          console.error("Error installing model:", err);
          setInstalling(false);
          resolve(false);
        });
    });
  };

  return { installModel, installing, error, progress };
}
