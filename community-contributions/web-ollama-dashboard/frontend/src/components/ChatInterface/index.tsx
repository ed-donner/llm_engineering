import { SendOutlined } from "@ant-design/icons";
import { Alert, Button, Input, Space, Spin, Typography } from "antd";
import { useState } from "react";
import { OllamaModel } from "../ModelsSelect/hooks/useOllamaModels";
import { useChat } from "./hooks/useChat";

const { TextArea } = Input;

// ---------------------------------------------------------------------------------------------------------------------
//  Component: ChatInterface
// ---------------------------------------------------------------------------------------------------------------------

export const ChatInterface = ({
  selectedModel,
  systemPrompts,
}: {
  selectedModel: OllamaModel | null;
  systemPrompts: string[];
}) => {
  const [message, setMessage] = useState("");
  const [output, setOutput] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const { sendMessage, loading, error } = useChat();

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleSend
  // -------------------------------------------------------------------------------------------------------------------

  const handleSend = async () => {
    if (!selectedModel) {
      setValidationError("Please select a model first.");
      return;
    }

    if (
      systemPrompts.length === 0 ||
      systemPrompts.every((p) => p.trim() === "")
    ) {
      setValidationError("At least one system prompt is required.");
      return;
    }

    if (message.trim() === "") {
      setValidationError("Message cannot be empty.");
      return;
    }

    setValidationError(null);
    setOutput("");

    // Build messages array: system prompts first, then user message
    const messages = [
      ...systemPrompts.map((prompt) => ({
        role: "system" as const,
        content: prompt.trim(),
      })),
      {
        role: "user" as const,
        content: message.trim(),
      },
    ];

    const response = await sendMessage({
      model: selectedModel.name,
      messages,
    });

    if (response) {
      setOutput(response);
    }
    setMessage("");
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      {!selectedModel && (
        <Alert
          message="No model selected"
          description="Please select a model from the models card above."
          type="info"
          showIcon
        />
      )}

      {validationError && (
        <Alert
          message="Validation Error"
          description={validationError}
          type="error"
          showIcon
          closable
          onClose={() => setValidationError(null)}
        />
      )}

      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
          closable
        />
      )}

      <div>
        <Typography.Text
          strong
          style={{ display: "block", marginBottom: "8px" }}
        >
          Message:
        </Typography.Text>
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your message..."
          onPressEnter={handleSend}
          disabled={!selectedModel || loading}
          suffix={
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSend}
              disabled={message.trim() === "" || !selectedModel || loading}
              loading={loading}
            >
              Send
            </Button>
          }
          size="large"
        />
      </div>

      <div>
        <Typography.Text
          strong
          style={{ display: "block", marginBottom: "8px" }}
        >
          Response:
        </Typography.Text>
        {loading && !output ? (
          <div style={{ textAlign: "center", padding: "20px" }}>
            <Spin size="large" />
            <Typography.Text
              type="secondary"
              style={{ display: "block", marginTop: "10px" }}
            >
              Waiting for response...
            </Typography.Text>
          </div>
        ) : (
          <TextArea
            value={output}
            readOnly
            placeholder="LLM response will appear here..."
            rows={10}
            style={{ resize: "none" }}
          />
        )}
      </div>
    </Space>
  );
};
