import { Layout, Typography } from "antd";

const { Header: AntHeader } = Layout;
const { Title, Text } = Typography;

// ---------------------------------------------------------------------------------------------------------------------
//  Component: Header
// ---------------------------------------------------------------------------------------------------------------------

export const Header = () => {
  return (
    <AntHeader className="app-header">
      <Title level={2} style={{ color: "#fff", margin: 0 }}>
        🤖 Ollama Dashboard
      </Title>
      <Text style={{ color: "#fff", opacity: 0.9 }}>
        Choose a model and interact with it
      </Text>
    </AntHeader>
  );
};
