import React from "react";
import ReactDOM from "react-dom/client";
import { MantineProvider } from "@mantine/core";
import "@mantine/core/styles.css";
import { AppRoutes } from "@/app/routes";
import { appTheme } from "@/app/theme";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <MantineProvider defaultColorScheme="light" theme={appTheme}>
      <AppRoutes />
    </MantineProvider>
  </React.StrictMode>
);
