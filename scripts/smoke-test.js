const { spawn } = require("child_process");

const PORT = 3100;
const BASE_URL = `http://127.0.0.1:${PORT}`;

function startServer() {
  return spawn(process.execPath, ["backend/server.js"], {
    cwd: process.cwd(),
    env: { ...process.env, PORT: String(PORT) },
    stdio: "pipe"
  });
}

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  const data = await response.json();
  if (!response.ok) throw new Error(`${path}: ${data.error || response.statusText}`);
  return data;
}

async function login(email) {
  const data = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password: "password123" })
  });
  return data.token;
}

async function waitForServer() {
  for (let attempt = 0; attempt < 20; attempt += 1) {
    try {
      await request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: "admin@fwc.demo", password: "password123" })
      });
      return;
    } catch (error) {
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error("Server did not start in time.");
}

async function run() {
  const server = startServer();
  try {
    await waitForServer();

    const adminToken = await login("admin@fwc.demo");
    const adminHeaders = { Authorization: `Bearer ${adminToken}` };
    const dashboard = await request("/api/dashboard", { headers: adminHeaders });
    const questions = await request("/api/ai/interview-questions", {
      method: "POST",
      headers: adminHeaders,
      body: JSON.stringify({ skills: "React, Node.js, Python" })
    });

    const employeeToken = await login("employee@fwc.demo");
    const employeeHeaders = { Authorization: `Bearer ${employeeToken}` };
    const employeeAttendance = await request("/api/attendance", { headers: employeeHeaders });
    const employeeCandidates = await request("/api/candidates", { headers: employeeHeaders });

    if (dashboard.employeeCount < 1) throw new Error("Dashboard employee count is invalid.");
    if (questions.questions.length !== 6) throw new Error("Interview question generator failed.");
    if (employeeAttendance.some((row) => row.employeeId !== "emp-1")) {
      throw new Error("Employee attendance filtering failed.");
    }
    if (employeeCandidates.length !== 0) throw new Error("Employee candidate privacy filtering failed.");

    console.log("Smoke tests passed.");
  } finally {
    server.kill();
  }
}

run().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
