import { Alert, Card, Layout, Space, Spin } from "antd";
import { useState } from "react";
import "./App.css";
import { ChatInterface } from "./components/ChatInterface";
import { Header } from "./components/Header";
import { ModelsSelect } from "./components/ModelsSelect";
import { OllamaModel } from "./components/ModelsSelect/hooks/useOllamaModels";
import { TextInputsList } from "./components/TextInputsList";
import { useOllamaHealth } from "./hooks/useOllamaHealth";

// ---------------------------------------------------------------------------------------------------------------------
//  Component: App
// ---------------------------------------------------------------------------------------------------------------------

export const App = () => {
  const [selectedModel, setSelectedModel] = useState<OllamaModel | null>(null);
  const [systemPrompts, setSystemPrompts] = useState<string[]>([]);
  const { available, loading, error, message } = useOllamaHealth();

  return (
    <Layout className="app-layout">
      <Header />
      <Layout.Content className="app-content">
        <Space
          direction="vertical"
          size="large"
          style={{ width: "100%", maxWidth: "1200px" }}
        >
          {loading && (
            <Card>
              <div style={{ textAlign: "center", padding: "20px" }}>
                <Spin size="large" />
                <p style={{ marginTop: "10px" }}>Checking Ollama status...</p>
              </div>
            </Card>
          )}

          {!loading && available === false && (
            <Alert
              message="Ollama Not Available"
              description={
                <div>
                  <p>{message || "Ollama is not running or not accessible."}</p>
                  {error && (
                    <p style={{ marginTop: "8px", fontSize: "12px" }}>
                      {error}
                    </p>
                  )}
                  <p style={{ marginTop: "8px" }}>
                    Please make sure Ollama is installed and running on your
                    machine.
                  </p>
                </div>
              }
              type="error"
              showIcon
              closable
            />
          )}

          {!loading && available === true && (
            <Alert
              message="Ollama Available"
              description={message || "Ollama is running and accessible."}
              type="success"
              showIcon
              closable
            />
          )}

          <Card>
            <ModelsSelect onModelSelect={setSelectedModel} />
          </Card>
          <Card>
            <TextInputsList onPromptsChange={setSystemPrompts} />
          </Card>
          <Card>
            <ChatInterface
              selectedModel={selectedModel}
              systemPrompts={systemPrompts}
            />
          </Card>
        </Space>
      </Layout.Content>
    </Layout>
  );
};
