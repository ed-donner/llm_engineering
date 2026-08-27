import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Input, List, Space } from "antd";
import { useState } from "react";

// ---------------------------------------------------------------------------------------------------------------------
//  Component: TextInputsList
// ---------------------------------------------------------------------------------------------------------------------

export const TextInputsList = ({
  onPromptsChange,
}: {
  onPromptsChange?: (prompts: string[]) => void;
}) => {
  const [inputs, setInputs] = useState<string[]>([""]);

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleAdd
  // -------------------------------------------------------------------------------------------------------------------

  const handleAdd = () => {
    const newInputs = [...inputs, ""];
    setInputs(newInputs);
    onPromptsChange?.(newInputs.filter((input) => input.trim() !== ""));
  };

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleChange
  // -------------------------------------------------------------------------------------------------------------------

  const handleChange = (index: number, value: string) => {
    const newInputs = [...inputs];
    newInputs[index] = value;
    setInputs(newInputs);
    onPromptsChange?.(newInputs.filter((input) => input.trim() !== ""));
  };

  // -------------------------------------------------------------------------------------------------------------------
  //  Function: handleDelete
  // -------------------------------------------------------------------------------------------------------------------

  const handleDelete = (index: number) => {
    if (inputs.length > 1) {
      const newInputs = inputs.filter((_, i) => i !== index);
      setInputs(newInputs);
      onPromptsChange?.(newInputs.filter((input) => input.trim() !== ""));
    }
  };

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="middle">
      <List
        dataSource={inputs}
        renderItem={(input, index) => (
          <List.Item
            actions={[
              <Button
                key="delete"
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() => handleDelete(index)}
                disabled={inputs.length === 1}
              >
                Remove
              </Button>,
            ]}
          >
            <Input
              value={input}
              onChange={(e) => handleChange(index, e.target.value)}
              placeholder="Enter text..."
              status={input.trim() === "" ? "error" : ""}
              style={{ width: "100%" }}
            />
          </List.Item>
        )}
      />
      <Button type="dashed" icon={<PlusOutlined />} onClick={handleAdd} block>
        Add System Prompt
      </Button>
    </Space>
  );
};
