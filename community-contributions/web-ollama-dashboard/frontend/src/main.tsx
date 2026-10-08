import { ConfigProvider } from "antd";
import enUS from "antd/locale/en_US";
import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App.tsx";
import "./index.css";

// ---------------------------------------------------------------------------------------------------------------------
//  Main entry point for the frontend
// ---------------------------------------------------------------------------------------------------------------------

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ConfigProvider locale={enUS}>
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
