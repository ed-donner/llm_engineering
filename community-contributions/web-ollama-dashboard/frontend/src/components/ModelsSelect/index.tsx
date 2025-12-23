import { SettingOutlined } from "@ant-design/icons";
import { Alert, Button, Space, Spin, Tag, Typography } from "antd";
import { useState } from "react";
import { OllamaModel, useOllamaModels } from "./hooks/useOllamaModels";
import { ModelsPanel } from "./ModelsPanel";

// ---------------------------------------------------------------------------------------------------------------------
//  Component: ModelSelect
// ---------------------------------------------------------------------------------------------------------------------

export const ModelsSelect = ({
  onModelSelect,
}: {
  onModelSelect?: (model: OllamaModel | null) => void;
}) => {
  const { models: installedModels, loading, error } = useOllamaModels();
  const [selectedModel, setSelectedModel] = useState<OllamaModel | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleSelectModel
  // -------------------------------------------------------------------------------------------------------------------

  const handleSelectModel = (model: OllamaModel | null) => {
    setSelectedModel(model);
    onModelSelect?.(model);
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: "20px" }}>
        <Spin size="large" />
        <Typography.Text
          type="secondary"
          style={{ display: "block", marginTop: "10px" }}
        >
          Loading models...
        </Typography.Text>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error loading models"
        description={error}
        type="error"
        showIcon
      />
    );
  }

  return (
    <>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Space
          align="center"
          style={{ width: "100%", justifyContent: "space-between" }}
        >
          <div>
            <Typography.Text
              strong
              style={{ display: "block", marginBottom: "4px" }}
            >
              Current Model:
            </Typography.Text>
            {selectedModel ? (
              <Space>
                <Typography.Text>{selectedModel.name}</Typography.Text>
                <Tag color="blue">In Use</Tag>
              </Space>
            ) : (
              <Typography.Text type="secondary">
                No model selected
              </Typography.Text>
            )}
          </div>
          <Button
            type="default"
            icon={<SettingOutlined />}
            onClick={() => setPanelOpen(true)}
          >
            Manage Models
          </Button>
        </Space>
      </Space>

      <ModelsPanel
        open={panelOpen}
        onClose={() => setPanelOpen(false)}
        selectedModel={selectedModel?.name || null}
        onSelectModel={handleSelectModel}
      />
    </>
  );
};
