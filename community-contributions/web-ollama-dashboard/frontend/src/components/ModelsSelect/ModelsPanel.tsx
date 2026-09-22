import { DeleteOutlined, DownloadOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Drawer,
  List,
  Modal,
  Progress,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";
import { useState } from "react";
import { useDeleteModel } from "./hooks/useDeleteModel";
import { useInstallModel } from "./hooks/useInstallModel";
import {
  OllamaAvailableModel,
  useOllamaAvailableModels,
} from "./hooks/useOllamaAvailableModels";
import { OllamaModel, useOllamaModels } from "./hooks/useOllamaModels";

// ---------------------------------------------------------------------------------------------------------------------
//  Component: ModelsPanel
// ---------------------------------------------------------------------------------------------------------------------

export const ModelsPanel = ({
  open,
  onClose,
  selectedModel,
  onSelectModel,
}: {
  open: boolean;
  onClose: () => void;
  selectedModel: string | null;
  onSelectModel: (model: OllamaModel | null) => void;
}) => {
  const {
    models: installedModels,
    loading: loadingInstalled,
    error: errorInstalled,
    refetch: refetchInstalled,
  } = useOllamaModels();
  const {
    models: availableModels,
    loading: loadingAvailable,
    error: errorAvailable,
    refetch: refetchAvailable,
  } = useOllamaAvailableModels();
  const {
    installModel,
    installing,
    error: installError,
    progress,
  } = useInstallModel();
  const { deleteModel, deleting, error: deleteError } = useDeleteModel();
  const [installingModel, setInstallingModel] = useState<string | null>(null);
  const [deletingModel, setDeletingModel] = useState<string | null>(null);

  const loading = loadingInstalled || loadingAvailable;
  const error = errorInstalled || errorAvailable;

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: formatSize
  // -------------------------------------------------------------------------------------------------------------------

  const formatSize = (sizeInBytes: number): string => {
    if (sizeInBytes === 0) return "";

    const gb = sizeInBytes / (1024 * 1024 * 1024);
    if (gb >= 1) {
      return `${gb.toFixed(1)} GB`;
    }

    const mb = sizeInBytes / (1024 * 1024);
    if (mb >= 1) {
      return `${mb.toFixed(1)} MB`;
    }

    return `${sizeInBytes} B`;
  };

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: formatSizeGB
  // -------------------------------------------------------------------------------------------------------------------

  const formatSizeGB = (sizeInBytes: number): string => {
    if (sizeInBytes === 0) return "";

    const gb = sizeInBytes / (1024 * 1024 * 1024);
    return `${gb.toFixed(2)} GB`;
  };

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleInstall
  // -------------------------------------------------------------------------------------------------------------------

  const handleInstall = async (modelName: string) => {
    setInstallingModel(modelName);
    const success = await installModel(modelName);
    if (success) {
      await Promise.all([refetchInstalled(), refetchAvailable()]);
    }
    setInstallingModel(null);
  };

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleSelectInstalled
  // -------------------------------------------------------------------------------------------------------------------

  const handleSelectInstalled = (model: OllamaModel) => {
    onSelectModel(model);
    onClose();
  };

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleDelete
  // -------------------------------------------------------------------------------------------------------------------

  const handleDelete = (model: OllamaModel, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent selecting the model when clicking delete

    Modal.confirm({
      title: "Delete Model",
      content: `Are you sure you want to delete "${model.name}"? This action cannot be undone.`,
      okText: "Delete",
      okType: "danger",
      cancelText: "Cancel",
      onOk: async () => {
        setDeletingModel(model.name);
        const success = await deleteModel(model.name);
        if (success) {
          // If deleted model was selected, clear selection
          if (selectedModel === model.name) {
            onSelectModel(null);
          }
          await Promise.all([refetchInstalled(), refetchAvailable()]);
        }
        setDeletingModel(null);
      },
    });
  };

  return (
    <Drawer
      title="Models"
      placement="right"
      onClose={onClose}
      open={open}
      width={500}
    >
      {loading && (
        <div style={{ textAlign: "center", padding: "20px" }}>
          <Spin size="large" />
          <Typography.Text
            type="secondary"
            style={{ display: "block", marginTop: "10px" }}
          >
            Loading models...
          </Typography.Text>
        </div>
      )}

      {error && (
        <Alert
          message="Error loading models"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: "16px" }}
        />
      )}

      {installError && (
        <Alert
          message="Installation Error"
          description={installError}
          type="error"
          showIcon
          closable
          style={{ marginBottom: "16px" }}
        />
      )}

      {deleteError && (
        <Alert
          message="Deletion Error"
          description={deleteError}
          type="error"
          showIcon
          closable
          style={{ marginBottom: "16px" }}
        />
      )}

      {installing && progress && installingModel && (
        <Alert
          message={`Installing ${installingModel}`}
          description={
            <Space direction="vertical" style={{ width: "100%" }}>
              <Typography.Text>{progress.status}</Typography.Text>
              <Progress percent={progress.progress} status="active" showInfo />
              {progress.total > 0 && (
                <Typography.Text type="secondary" style={{ fontSize: "12px" }}>
                  {formatSize(progress.completed)} /{" "}
                  {formatSize(progress.total)}
                </Typography.Text>
              )}
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: "16px" }}
        />
      )}

      {!loading && (
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          {installedModels.length > 0 && (
            <div>
              <Typography.Title level={4}>Installed Models</Typography.Title>
              <List
                dataSource={installedModels}
                renderItem={(model: OllamaModel) => (
                  <List.Item
                    style={{
                      backgroundColor:
                        selectedModel === model.name
                          ? "#e6f7ff"
                          : "transparent",
                      cursor: "pointer",
                    }}
                    onClick={() => handleSelectInstalled(model)}
                    actions={[
                      <Button
                        key="delete"
                        type="text"
                        danger
                        icon={<DeleteOutlined />}
                        loading={deleting && deletingModel === model.name}
                        onClick={(e) => handleDelete(model, e)}
                        disabled={deleting}
                      >
                        Delete
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Typography.Text strong>{model.name}</Typography.Text>
                          {selectedModel === model.name && (
                            <Tag color="blue">In Use</Tag>
                          )}
                          {model.size > 0 && (
                            <Typography.Text type="secondary">
                              ({formatSize(model.size)})
                            </Typography.Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </div>
          )}

          {availableModels.length > 0 && (
            <div>
              <Typography.Title level={4}>Available Models</Typography.Title>
              <List
                dataSource={availableModels}
                renderItem={(model: OllamaAvailableModel) => (
                  <List.Item
                    actions={[
                      <Button
                        key="install"
                        type="primary"
                        icon={<DownloadOutlined />}
                        loading={installing && installingModel === model.name}
                        onClick={() => handleInstall(model.name)}
                        disabled={installing}
                      >
                        Install
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={
                        <Space>
                          <Typography.Text strong>{model.name}</Typography.Text>
                          {model.size > 0 && (
                            <Typography.Text type="secondary">
                              ({formatSizeGB(model.size)})
                            </Typography.Text>
                          )}
                        </Space>
                      }
                      description={
                        model.size > 0 ? (
                          <Typography.Text type="secondary">
                            Size: {formatSizeGB(model.size)}
                          </Typography.Text>
                        ) : null
                      }
                    />
                  </List.Item>
                )}
              />
            </div>
          )}

          {!loading &&
            installedModels.length === 0 &&
            availableModels.length === 0 && (
              <Alert
                message="No models available"
                description="No models were found in Ollama."
                type="info"
                showIcon
              />
            )}
        </Space>
      )}
    </Drawer>
  );
};
