import { SendOutlined } from "@ant-design/icons";
import { Alert, Button, Input, Space, Spin, Typography } from "antd";
import { useEffect, useRef, useState } from "react";
import { OllamaModel } from "../ModelsSelect/hooks/useOllamaModels";
import { useChat } from "./hooks/useChat";

const { TextArea } = Input;

// ---------------------------------------------------------------------------------------------------------------------
//  Types
// ---------------------------------------------------------------------------------------------------------------------

export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

// ---------------------------------------------------------------------------------------------------------------------
//  Component: ChatInterface
// ---------------------------------------------------------------------------------------------------------------------

export const ChatInterface = ({
  selectedModel,
  systemPrompts,
  onHistoryChange,
}: {
  selectedModel: OllamaModel | null;
  systemPrompts: string[];
  onHistoryChange?: (history: ChatMessage[]) => void;
}) => {
  const [message, setMessage] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const [messageHistory, setMessageHistory] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendMessage, loading, error } = useChat();

  // -------------------------------------------------------------------------------------------------------------------
  //  Effect: Scroll to bottom when new messages arrive
  // -------------------------------------------------------------------------------------------------------------------

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messageHistory, isSending]);

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

    const userMessage: ChatMessage = {
      role: "user",
      content: message.trim(),
    };

    // Add user message to history immediately for better UX
    const updatedHistory = [...messageHistory, userMessage];
    setMessageHistory(updatedHistory);
    setIsSending(true);
    const currentMessage = message.trim();
    setMessage("");

    // Build messages array: system prompts first, then message history, then new user message
    const messages: ChatMessage[] = [
      ...systemPrompts.map((prompt) => ({
        role: "system" as const,
        content: prompt.trim(),
      })),
      ...messageHistory,
      userMessage,
    ];

    const response = await sendMessage({
      model: selectedModel.name,
      messages,
    });

    setIsSending(false);

    if (response) {
      // Add assistant response to history
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: response,
      };
      const newHistory = [...updatedHistory, assistantMessage];
      setMessageHistory(newHistory);
      onHistoryChange?.(newHistory);
    } else {
      // Remove user message if request failed
      setMessageHistory(messageHistory);
      setMessage(currentMessage);
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "600px",
        border: "1px solid #d9d9d9",
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      {/* Messages Area */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px",
          backgroundColor: "#fafafa",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        {!selectedModel && (
          <Alert
            message="No model selected"
            description="Please select a model from the models card above."
            type="info"
            showIcon
            style={{ marginBottom: "8px" }}
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
            style={{ marginBottom: "8px" }}
          />
        )}

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            closable
            style={{ marginBottom: "8px" }}
          />
        )}

        {messageHistory.length === 0 && !isSending && (
          <div
            style={{
              textAlign: "center",
              padding: "40px 20px",
              color: "#8c8c8c",
            }}
          >
            <Typography.Text type="secondary" style={{ fontStyle: "italic" }}>
              No messages yet. Start a conversation!
            </Typography.Text>
          </div>
        )}

        {messageHistory.map((msg, index) => (
          <div
            key={index}
            style={{
              display: "flex",
              justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              marginBottom: "8px",
            }}
          >
            <div
              style={{
                maxWidth: "70%",
                padding: "12px 16px",
                borderRadius: "12px",
                backgroundColor:
                  msg.role === "user" ? "#1890ff" : "#ffffff",
                color: msg.role === "user" ? "#ffffff" : "#000000",
                boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                wordWrap: "break-word",
                whiteSpace: "pre-wrap",
              }}
            >
              <Typography.Text
                style={{
                  color: msg.role === "user" ? "#ffffff" : "#000000",
                  fontSize: "14px",
                }}
              >
                {msg.content}
              </Typography.Text>
            </div>
          </div>
        ))}

        {isSending && (
          <div
            style={{
              display: "flex",
              justifyContent: "flex-start",
              marginBottom: "8px",
            }}
          >
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "12px",
                backgroundColor: "#ffffff",
                boxShadow: "0 1px 2px rgba(0,0,0,0.1)",
                display: "flex",
                alignItems: "center",
                gap: "8px",
              }}
            >
              <Spin size="small" />
              <Typography.Text type="secondary" style={{ fontSize: "14px" }}>
                Thinking...
              </Typography.Text>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div
        style={{
          borderTop: "1px solid #d9d9d9",
          padding: "12px",
          backgroundColor: "#ffffff",
        }}
      >
        <Space.Compact style={{ width: "100%" }}>
          <TextArea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={!selectedModel || loading || isSending}
            autoSize={{ minRows: 1, maxRows: 4 }}
            onPressEnter={(e) => {
              if (!e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            style={{ resize: "none" }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleSend}
            disabled={
              message.trim() === "" || !selectedModel || loading || isSending
            }
            loading={loading || isSending}
            style={{ height: "auto" }}
          >
            Send
          </Button>
        </Space.Compact>
      </div>
    </div>
  );
};
