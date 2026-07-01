"use client";

import { useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function LoginPage() {
  const [email, setEmail] = useState("admin@fwc.demo");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Login failed");

      login(data.token, data.user);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="login-shell">
      <div className="login-panel">
        <h1>FWC AI-HRMS</h1>
        <p>
          Intelligent Human Resource Management powered by AI. Login to access
          your personalised dashboard.
        </p>
        
        {error && <div style={{ color: "var(--coral)", marginBottom: "16px" }}>{error}</div>}

        <form onSubmit={handleLogin} className="login-grid">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit" className="primary" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div className="demo-users">
          <button
            type="button"
            onClick={() => {
              setEmail("admin@fwc.demo");
              setPassword("password123");
            }}
          >
            ⚡ Management Admin
          </button>
          <button
            type="button"
            onClick={() => {
              setEmail("hr@fwc.demo");
              setPassword("password123");
            }}
          >
            👤 HR Recruiter
          </button>
          <button
            type="button"
            onClick={() => {
              setEmail("manager@fwc.demo");
              setPassword("password123");
            }}
          >
            📊 Senior Manager
          </button>
          <button
            type="button"
            onClick={() => {
              setEmail("employee@fwc.demo");
              setPassword("password123");
            }}
          >
            🧑‍💻 Employee
          </button>
        </div>
      </div>
    </section>
  );
}
