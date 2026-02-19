import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { RunProvider } from "@/context/RunContext";
import HomePage from "@/pages/HomePage";
import DashboardPage from "@/pages/DashboardPage";
import "@/index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <RunProvider>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/run/:runId" element={<DashboardPage />} />
        </Routes>
      </RunProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
