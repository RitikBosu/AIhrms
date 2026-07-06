"use client";

import { useState, useEffect } from "react";

type ToastType = "success" | "error" | "info";

interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
}

// Global emitter
let toastListeners: ((toasts: ToastMessage[]) => void)[] = [];
let currentToasts: ToastMessage[] = [];

const emitChange = () => {
  toastListeners.forEach(l => l([...currentToasts]));
};

export const toast = {
  success: (msg: string) => addToast("success", msg),
  error: (msg: string) => addToast("error", msg),
  info: (msg: string) => addToast("info", msg),
};

const addToast = (type: ToastType, message: string) => {
  const id = Math.random().toString(36).substring(2, 9);
  currentToasts.push({ id, type, message });
  emitChange();

  setTimeout(() => {
    currentToasts = currentToasts.filter(t => t.id !== id);
    emitChange();
  }, 4000);
};

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    toastListeners.push(setToasts);
    return () => {
      toastListeners = toastListeners.filter(l => l !== setToasts);
    };
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast ${t.type}`}>
          <div className="toast-icon">
            {t.type === "success" && "✓"}
            {t.type === "error" && "✕"}
            {t.type === "info" && "ℹ"}
          </div>
          <div className="toast-message">{t.message}</div>
        </div>
      ))}
    </div>
  );
}
