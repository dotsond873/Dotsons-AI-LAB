import React from "react";
import { createRoot } from "react-dom/client";
import App from "../App.jsx";

const root = createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/shady-worker.js").catch(error => {
      console.warn("Shady app registration failed", error);
    });
  });
}
