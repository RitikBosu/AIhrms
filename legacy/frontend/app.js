/* ═══════════════════════════════════════════════════════
   FWC AI-HRMS — Frontend Application
   ═══════════════════════════════════════════════════════ */

const state = {
  token: localStorage.getItem("fwcToken") || "",
  user: JSON.parse(localStorage.getItem("fwcUser") || "null"),
  page: "dashboard",
  sidebarOpen: false,
  notifOpen: false,
  data: {
    dashboard: null,
    employees: [],
    attendance: [],
    leaves: [],
    payroll: [],
    candidates: [],
    performance: [],
    notifications: [],
    announcements: []
  }
};

const app = document.querySelector("#app");

/* ── SVG Icons ── */
const icons = {
  dashboard: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>`,
  employees: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
  attendance: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><path d="M9 16l2 2 4-4"/></svg>`,
  leaves: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="9" y1="15" x2="15" y2="15"/></svg>`,
  payroll: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
  candidates: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>`,
  performance: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`,
  chatbot: `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a8 8 0 0 0-8 8c0 3.4 2.1 6.3 5 7.4V20a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2.6c2.9-1.1 5-4 5-7.4a8 8 0 0 0-8-8z"/><line x1="9" y1="10" x2="9" y2="10"/><line x1="15" y1="10" x2="15" y2="10"/></svg>`,
  bell: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>`,
  hamburger: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>`,
  brain: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a8 8 0 0 0-8 8c0 3.4 2.1 6.3 5 7.4V20a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2v-2.6c2.9-1.1 5-4 5-7.4a8 8 0 0 0-8-8z"/></svg>`,
  statEmployees: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>`,
  statCandidates: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>`,
  statLeaves: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`,
  statPresent: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`
};

const ROLE_LABELS = {
  admin: "Management Admin",
  manager: "Senior Manager",
  hr: "HR Recruiter",
  employee: "Employee"
};

const navItems = [
  ["dashboard",   "Dashboard",   icons.dashboard],
  ["employees",   "Employees",   icons.employees],
  ["attendance",  "Attendance",  icons.attendance],
  ["leaves",      "Leaves",      icons.leaves],
  ["payroll",     "Payroll",     icons.payroll],
  ["candidates",  "AI Screening",  icons.candidates],
  ["performance", "Performance", icons.performance],
  ["chatbot",     "AI Recruiter",  icons.chatbot]
];

/* ═══════════════════════════════════════
   AUTH HELPERS
   ═══════════════════════════════════════ */

function canManagePeople() {
  return ["admin", "hr"].includes(state.user?.role);
}

function canApprove() {
  return ["admin", "manager"].includes(state.user?.role);
}

function canReview() {
  return ["admin", "manager"].includes(state.user?.role);
}

/* ═══════════════════════════════════════
   TOAST
   ═══════════════════════════════════════ */

function showToast(message) {
  const oldToast = document.querySelector(".toast");
  if (oldToast) oldToast.remove();
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

/* ═══════════════════════════════════════
   API HELPER
   ═══════════════════════════════════════ */

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: state.token ? `Bearer ${state.token}` : "",
      ...(options.headers || {})
    }
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

/* ═══════════════════════════════════════
   SESSION
   ═══════════════════════════════════════ */

function setSession(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem("fwcToken", token);
  localStorage.setItem("fwcUser", JSON.stringify(user));
}

function clearSession() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("fwcToken");
  localStorage.removeItem("fwcUser");
}

/* ═══════════════════════════════════════
   LOGIN SCREEN
   ═══════════════════════════════════════ */

function renderLogin() {
  app.innerHTML = `
    <section class="login-shell">
      <div class="login-panel">
        <h1>FWC AI-HRMS</h1>
        <p>Intelligent Human Resource Management powered by AI. Login to access your personalised dashboard.</p>
        <form id="loginForm" class="login-grid">
          <label>Email
            <input id="email" type="email" value="admin@fwc.demo" required />
          </label>
          <label>Password
            <input id="password" type="password" value="password123" required />
          </label>
          <button type="submit">Sign In</button>
        </form>
        <div class="demo-users">
          <button data-email="admin@fwc.demo">⚡ Management Admin</button>
          <button data-email="hr@fwc.demo">👤 HR Recruiter</button>
          <button data-email="manager@fwc.demo">📊 Senior Manager</button>
          <button data-email="employee@fwc.demo">🧑‍💻 Employee</button>
        </div>
      </div>
    </section>
  `;

  document.querySelector("#loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const btn = event.target.querySelector("button[type='submit']");
    btn.textContent = "Signing in...";
    btn.disabled = true;
    try {
      const data = await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: document.querySelector("#email").value,
          password: document.querySelector("#password").value
        })
      });
      setSession(data.token, data.user);
      await loadAllData();
      renderApp();
    } catch (error) {
      showToast(error.message);
      btn.textContent = "Sign In";
      btn.disabled = false;
    }
  });

  document.querySelectorAll("[data-email]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelector("#email").value = button.dataset.email;
      document.querySelector("#password").value = "password123";
    });
  });
}

/* ═══════════════════════════════════════
   DATA LOADING
   ═══════════════════════════════════════ */

async function loadAllData() {
  const [dashboard, employees, attendance, leaves, payroll, candidates, performance, notifications, announcements] =
    await Promise.all([
      api("/api/dashboard"),
      api("/api/employees"),
      api("/api/attendance"),
      api("/api/leaves"),
      api("/api/payroll"),
      api("/api/candidates"),
      api("/api/performance"),
      api("/api/notifications"),
      api("/api/announcements")
    ]);
  state.data = { dashboard, employees, attendance, leaves, payroll, candidates, performance, notifications, announcements };
}

/* ═══════════════════════════════════════
   APP SHELL
   ═══════════════════════════════════════ */

function renderApp() {
  const notifCount = state.data.notifications?.length || 0;

  app.innerHTML = `
    <button class="hamburger" id="hamburgerBtn">${icons.hamburger}</button>
    <div class="sidebar-overlay ${state.sidebarOpen ? "open" : ""}" id="sidebarOverlay"></div>
    <section class="app-shell">
      <aside class="sidebar ${state.sidebarOpen ? "open" : ""}" id="sidebar">
        <div class="brand">
          <div class="brand-mark">FWC</div>
          <div>
            <strong>AI-HRMS</strong><br />
            <small>${state.user.name} (${ROLE_LABELS[state.user.role]})</small>
          </div>
        </div>
        <nav class="nav">
          ${navItems
            .map(
              ([id, label, icon]) =>
                `<button class="${state.page === id ? "active" : ""}" data-page="${id}">${icon}<span>${label}</span></button>`
            )
            .join("")}
        </nav>
        <div class="sidebar-logout">
          <button class="secondary" id="logoutBtnSidebar" style="width:100%">Logout</button>
        </div>
      </aside>
      <section class="main">
        <div class="topbar">
          <div class="page-title">
            <h1>${pageTitle()}</h1>
            <p>${pageSubtitle()}</p>
          </div>
          <div class="topbar-actions">
            <div class="notif-wrapper">
              <button class="notif-bell" id="notifBellBtn">
                ${icons.bell}
                ${notifCount > 0 ? `<span class="notif-count">${notifCount}</span>` : ""}
              </button>
              <div class="notif-dropdown" id="notifDropdown">
                <div class="notif-dropdown-header">Notifications</div>
                ${notifCount > 0
                  ? state.data.notifications.slice(0, 5).map(n => `
                    <div class="notif-item">
                      <div class="notif-title">${escHtml(n.title)}</div>
                      <div class="notif-msg">${escHtml(n.message)}</div>
                    </div>
                  `).join("")
                  : `<div class="notif-empty">No new notifications</div>`
                }
              </div>
            </div>
            <span class="role-pill">${ROLE_LABELS[state.user.role]}</span>
            <button class="secondary" id="logoutBtn">Logout</button>
          </div>
        </div>
        <div id="pageContent"></div>
      </section>
    </section>
  `;

  /* ── Event bindings ── */
  document.querySelectorAll("[data-page]").forEach((button) => {
    button.addEventListener("click", () => {
      state.page = button.dataset.page;
      state.sidebarOpen = false;
      renderApp();
    });
  });

  document.querySelector("#logoutBtn")?.addEventListener("click", logout);
  document.querySelector("#logoutBtnSidebar")?.addEventListener("click", logout);

  /* Hamburger */
  document.querySelector("#hamburgerBtn")?.addEventListener("click", () => {
    state.sidebarOpen = !state.sidebarOpen;
    document.querySelector("#sidebar")?.classList.toggle("open", state.sidebarOpen);
    document.querySelector("#sidebarOverlay")?.classList.toggle("open", state.sidebarOpen);
  });

  document.querySelector("#sidebarOverlay")?.addEventListener("click", () => {
    state.sidebarOpen = false;
    document.querySelector("#sidebar")?.classList.remove("open");
    document.querySelector("#sidebarOverlay")?.classList.remove("open");
  });

  /* Notification bell */
  document.querySelector("#notifBellBtn")?.addEventListener("click", (e) => {
    e.stopPropagation();
    const dd = document.querySelector("#notifDropdown");
    dd?.classList.toggle("open");
  });

  document.addEventListener("click", () => {
    document.querySelector("#notifDropdown")?.classList.remove("open");
  }, { once: true });

  renderPageContent();
}

function logout() {
  clearSession();
  renderLogin();
}

/* ═══════════════════════════════════════
   PAGE META
   ═══════════════════════════════════════ */

function pageTitle() {
  const item = navItems.find(([id]) => id === state.page);
  return item ? item[1] : "Dashboard";
}

function pageSubtitle() {
  const subtitles = {
    dashboard: "Real-time company overview with AI-powered insights.",
    employees: "Manage employee records, departments, and compensation.",
    attendance: "Track and mark daily attendance records.",
    leaves: "Apply for leave and manage approval workflows.",
    payroll: "Automated salary calculation with allowances and deductions.",
    candidates: "Autonomous AI-powered resume screening pipeline.",
    performance: "Performance reviews with AI summaries and attrition prediction.",
    chatbot: "Conversational AI for candidate screening and HR queries."
  };
  return subtitles[state.page];
}

/* ═══════════════════════════════════════
   PAGE ROUTER
   ═══════════════════════════════════════ */

function renderPageContent() {
  const container = document.querySelector("#pageContent");
  const pages = {
    dashboard: renderDashboard,
    employees: renderEmployees,
    attendance: renderAttendance,
    leaves: renderLeaves,
    payroll: renderPayroll,
    candidates: renderCandidates,
    performance: renderPerformance,
    chatbot: renderChatbot
  };
  container.innerHTML = pages[state.page]();
  attachPageEvents();

  /* Animate stat counters */
  document.querySelectorAll(".stat-value[data-target]").forEach(animateCounter);
}

/* ═══════════════════════════════════════
   DASHBOARD
   ═══════════════════════════════════════ */

function renderDashboard() {
  const dash = state.data.dashboard;
  const anns = state.data.announcements || [];
  const myAct = dash.myActivity;

  let html = `
    <div class="stats">
      ${statCard("Personal Attendance", (myAct?.myAttendanceRate || 100) + "%", icons.statPresent, "green")}
      ${statCard("Leave Balance", ((myAct?.myLeaveBalance?.total || 18) - (myAct?.myLeaveBalance?.used || 0)) + " days", icons.statLeaves, "amber")}
      ${statCard("Pending Leaves", myAct?.myLeaveBalance?.pending || 0, icons.leaves, "purple")}
      ${statCard("Announcements", anns.length, icons.bell, "cyan")}
    </div>
  `;

  if (state.user.role === "admin" && dash.companyOverview) {
    const co = dash.companyOverview;
    html += `
      <section class="section" style="margin-bottom:20px; border: 1px solid var(--cyan); background: rgba(0, 212, 255, 0.05)">
        <h2 style="color: var(--cyan)">🏢 Company Overview (Admin)</h2>
        <div class="stats" style="margin-top: 10px">
          ${statCard("Total Employees", co.totalEmployees, icons.statEmployees, "cyan")}
          ${statCard("Overall Attendance", co.overallAttendanceRate + "%", icons.statPresent, "green")}
          ${statCard("Open Positions", co.totalOpenPositions, icons.candidates, "amber")}
          ${statCard("High Risk Attrition", co.attritionRiskSummary?.high || 0, icons.performance, "coral")}
        </div>
      </section>
    `;
  }

  if (state.user.role === "hr" && dash.screeningStats) {
    const ss = dash.screeningStats;
    html += `
      <section class="section" style="margin-bottom:20px; border: 1px solid var(--purple); background: rgba(168, 85, 247, 0.05)">
        <h2 style="color: var(--purple)">🎯 Screening Pipeline (HR)</h2>
        <div class="stats" style="margin-top: 10px">
          ${statCard("Shortlisted", ss.shortlisted, icons.statPresent, "green")}
          ${statCard("Under Review", ss.underReview, icons.leaves, "amber")}
          ${statCard("Rejected", ss.rejected, icons.performance, "coral")}
        </div>
      </section>
    `;
  }

  html += `
    ${state.user.role === "admin" ? `
      <section class="section" style="margin-bottom:20px">
        <h2>📢 Post Announcement</h2>
        <form id="announcementForm" class="form-grid">
          <label>Title<input name="title" placeholder="Announcement title" required /></label>
          <label>Content<input name="content" placeholder="Brief message for all employees" required /></label>
          <div class="form-actions full"><button type="submit">Publish Announcement</button></div>
        </form>
      </section>
    ` : ""}

    ${anns.length > 0 ? `
      <section class="section" style="margin-bottom:20px">
        <h2>📢 Announcements</h2>
        <div class="announcements-feed">
          ${anns.slice().reverse().slice(0, 5).map(a => `
            <div class="announcement-item">
              <div class="ann-title">${escHtml(a.title)}</div>
              <div class="ann-content">${escHtml(a.content)}</div>
              <div class="ann-meta">By ${escHtml(a.createdBy)} · ${new Date(a.createdAt).toLocaleDateString()}</div>
            </div>
          `).join("")}
        </div>
      </section>
    ` : ""}

    <div class="content-grid">
      <section class="section">
        <h2>My Recent Attendance</h2>
        ${attendanceTable(dash.attendanceRows?.slice(-6) || [])}
      </section>
      <section class="section">
        <h2>My Leave Requests</h2>
        ${leaveList(dash.leaveRows?.slice(-5) || [])}
      </section>
    </div>
  `;

  return html;
}

function statCard(label, value, icon, color) {
  return `
    <div class="stat">
      <div class="stat-header">
        <div class="stat-icon ${color}">${icon}</div>
      </div>
      <div class="stat-label">${label}</div>
      <div class="stat-value" data-target="${value}">0</div>
    </div>
  `;
}

/* ── Counter animation ── */
function animateCounter(el) {
  const target = parseInt(el.dataset.target, 10) || 0;
  if (target === 0) { el.textContent = "0"; return; }
  const duration = 600;
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(eased * target);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/* ═══════════════════════════════════════
   EMPLOYEES
   ═══════════════════════════════════════ */

function renderEmployees() {
  return `
    ${canManagePeople() ? employeeForm() : ""}
    <section class="section">
      <h2>Employee List</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Email</th><th>Department</th><th>Designation</th><th>Salary</th><th>Joined</th>
              ${state.user.role === "admin" ? "<th>Action</th>" : ""}
            </tr>
          </thead>
          <tbody>
            ${state.data.employees
              .map(
                (employee) => `
                  <tr>
                    <td>${escHtml(employee.name)}</td>
                    <td>${escHtml(employee.email)}</td>
                    <td>${escHtml(employee.department)}</td>
                    <td>${escHtml(employee.designation)}</td>
                    <td>${money(employee.salary)}</td>
                    <td>${employee.joiningDate}</td>
                    ${state.user.role === "admin" ? `<td><button class="danger" data-delete-emp="${employee.id}">Delete</button></td>` : ""}
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function employeeForm() {
  return `
    <section class="section">
      <h2>Add Employee</h2>
      <form id="employeeForm" class="form-grid">
        <label>Name<input name="name" required /></label>
        <label>Email<input name="email" type="email" required /></label>
        <label>Department<input name="department" required /></label>
        <label>Designation<input name="designation" required /></label>
        <label>Salary<input name="salary" type="number" min="0" required /></label>
        <label>Joining Date<input name="joiningDate" type="date" required /></label>
        <div class="form-actions full"><button type="submit">Add Employee</button></div>
      </form>
    </section>
  `;
}

/* ═══════════════════════════════════════
   ATTENDANCE
   ═══════════════════════════════════════ */

function renderAttendance() {
  if (!state.attendanceFilterDate) state.attendanceFilterDate = today();
  const filteredRecords = state.data.attendance.filter(r => r.date === state.attendanceFilterDate);

  return `
    <section class="section">
      <h2>Mark Attendance</h2>
      <form id="attendanceForm" class="form-grid">
        ${employeeSelect("employeeId", state.user.role === "employee")}
        <label>Date<input name="date" type="date" value="${today()}" max="${today()}" required /></label>
        <label>Status
          <select name="status">
            <option>Present</option>
            <option>Absent</option>
          </select>
        </label>
        <div class="form-actions full">
          <button type="submit">Save Attendance</button>
          ${canManagePeople() ? `<button type="button" class="secondary" id="bulkUploadBtn">Bulk Upload</button>` : ""}
        </div>
      </form>
    </section>
    <section class="section">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 12px;">
        <h2 style="margin: 0;">Attendance Records</h2>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="color: var(--ink-muted); font-size: 14px;">Filter by Date:</span>
          <input type="date" id="attFilterDate" value="${state.attendanceFilterDate}" max="${today()}" style="padding: 8px 12px; border-radius: var(--radius-pill); border: 1px solid var(--glass-border); background: var(--bg-card); color: var(--ink); width: auto;" />
        </div>
      </div>
      ${attendanceTable(filteredRecords)}
    </section>
  `;
}

function attendanceTable(rows) {
  if (!rows.length) return `<div class="empty-state"><div class="empty-icon">📋</div>No attendance records found.</div>`;
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Employee</th><th>Date</th><th>Status</th></tr></thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr>
                  <td>${employeeName(row.employeeId)}</td>
                  <td>${row.date}</td>
                  <td><span class="badge ${row.status === "Present" ? "good" : "bad"}">${row.status}</span></td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

/* ═══════════════════════════════════════
   LEAVES
   ═══════════════════════════════════════ */

function renderLeaves() {
  return `
    <section class="section">
      <h2>Apply Leave</h2>
      <form id="leaveForm" class="form-grid">
        ${employeeSelect("employeeId", state.user.role === "employee")}
        <label>From Date<input name="fromDate" type="date" required /></label>
        <label>To Date<input name="toDate" type="date" required /></label>
        <label class="full">Reason<textarea name="reason" required></textarea></label>
        <div class="form-actions full"><button type="submit">Submit Leave</button></div>
      </form>
    </section>
    <section class="section">
      <h2>Leave Requests</h2>
      ${leaveList(state.data.leaves)}
    </section>
  `;
}

function leaveList(leaves) {
  if (!leaves.length) return `<div class="empty-state"><div class="empty-icon">📄</div>No leave requests found.</div>`;
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Employee</th><th>Dates</th><th>Reason</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>
          ${leaves
            .map(
              (leave) => `
                <tr>
                  <td>${employeeName(leave.employeeId)}</td>
                  <td>${leave.fromDate} → ${leave.toDate}</td>
                  <td>${escHtml(leave.reason)}</td>
                  <td><span class="badge ${leave.status === "Pending" ? "warn" : leave.status === "Approved" ? "good" : "bad"}">${leave.status}</span></td>
                  <td>
                    ${
                      canApprove() && leave.status === "Pending"
                        ? `<button class="secondary" data-leave="${leave.id}" data-status="Approved">Approve</button>
                           <button class="danger" data-leave="${leave.id}" data-status="Rejected">Reject</button>`
                        : "—"
                    }
                  </td>
                </tr>
              `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

/* ═══════════════════════════════════════
   PAYROLL
   ═══════════════════════════════════════ */

function renderPayroll() {
  return `
    <section class="section">
      <h2>Payroll Calculation</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Employee</th><th>Basic</th><th>Present</th><th>Absent</th><th>Allowance</th><th>Deduction</th><th>Net Salary</th>
            </tr>
          </thead>
          <tbody>
            ${state.data.payroll
              .map(
                (row) => `
                  <tr>
                    <td>${escHtml(row.name)}</td>
                    <td>${money(row.basicSalary)}</td>
                    <td><span class="badge good">${row.presentDays}</span></td>
                    <td><span class="badge ${row.absentDays > 0 ? 'bad' : ''}">${row.absentDays}</span></td>
                    <td>${money(row.allowance)}</td>
                    <td>${money(row.deduction)}</td>
                    <td><strong>${money(row.netSalary)}</strong></td>
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

/* ═══════════════════════════════════════
   CANDIDATES
   ═══════════════════════════════════════ */

function renderProgressBar(score) {
  const s = Number(score) || 0;
  const blocks = Math.round(s / 10);
  const bar = "█".repeat(blocks) + "░".repeat(10 - blocks);
  const color = s >= 70 ? "var(--green)" : s >= 45 ? "var(--amber)" : "var(--coral)";
  return `<span style="font-family: monospace; color: ${color}; letter-spacing: -1px; white-space: nowrap;">[${bar}] ${s}</span>`;
}

function renderDecisionBadge(decision) {
  if (decision === "Shortlisted") return `<span class="badge" style="background:#1a3a2a; color:#4ade80; border:1px solid #4ade80">Shortlisted</span>`;
  if (decision === "Review manually") return `<span class="badge" style="background:#3a2e0a; color:#fbbf24; border:1px solid #fbbf24">Review manually</span>`;
  if (decision === "Needs improvement") return `<span class="badge" style="background:#3a1a0a; color:#fb923c; border:1px solid #fb923c">Needs improvement</span>`;
  return `<span class="badge" style="background:#1e1e2e; color:#6b7280; border:1px solid #374151">Pending</span>`;
}

function renderSkills(candidate) {
  const arr = candidate.matchedKeywords || [];
  if (!arr.length) return escHtml(candidate.skills || "");
  const top = arr.slice(0, 5);
  let html = top.map(s => `<span class="badge" style="background:var(--bg-surface); margin-bottom:4px; display:inline-block;">${escHtml(s)}</span>`).join(" ");
  if (arr.length > 5) html += ` <span style="color:var(--text-muted); font-size:12px; white-space:nowrap;">+${arr.length - 5} more</span>`;
  return html;
}

function renderJustification(justification, id) {
  const text = justification || "No justification provided.";
  if (text.length <= 90) return escHtml(text);
  const short = escHtml(text.substring(0, 90));
  const full = escHtml(text);
  return `
    <span id="just-short-${id}">${short}... <button class="ghost" style="padding:0; margin:0; min-width:auto; display:inline; font-size:12px; height:auto;" onclick="document.getElementById('just-short-${id}').style.display='none';document.getElementById('just-full-${id}').style.display='inline';">[+]</button></span>
    <span id="just-full-${id}" style="display:none;">${full} <button class="ghost" style="padding:0; margin:0; min-width:auto; display:inline; font-size:12px; height:auto;" onclick="document.getElementById('just-full-${id}').style.display='none';document.getElementById('just-short-${id}').style.display='inline';">[-]</button></span>
  `;
}

function renderName(candidate) {
  let html = candidate.name === 'Unknown Candidate' 
    ? `<span style="color:var(--text-muted);font-style:italic">Unknown Candidate</span>` 
    : `<strong>${escHtml(candidate.name)}</strong>`;
  if (candidate.redFlags && candidate.redFlags.length > 0) {
    const title = escHtml(candidate.redFlags.map(f => "• " + f).join("\\n"));
    html += ` <span title="${title}" style="cursor:help;">⚠️</span>`;
  }
  return html;
}

function renderOverallScore(score) {
  const s = Number(score) || 0;
  const color = s >= 70 ? "var(--green)" : s >= 45 ? "var(--amber)" : "var(--coral)";
  return `<span class="badge" style="background:transparent; border:1px solid ${color}; color:${color}; font-weight:bold;">${s}</span>`;
}

function jdConfigPanel() {
  return `
    <details class="section" id="jdPanel" style="margin-bottom: 20px; border: 1px solid var(--border); border-radius: 8px; background: var(--bg-card); cursor: pointer;">
      <summary style="padding: 15px; font-weight: 600; outline: none; list-style: none; display: flex; justify-content: space-between;">
        <span>📋 Job Description for AI Screening</span>
        <span id="jdStatus" style="font-weight:normal; font-size: 13px; color: var(--text-muted);">[▼ Configure]</span>
      </summary>
      <div style="padding: 0 15px 15px 15px; cursor: default; border-top: 1px solid var(--border); padding-top: 15px;">
        <p style="margin-bottom: 10px; font-size: 13px; color: var(--text-muted);">Paste the full Job Description here. The AI will use this to score every resume submitted to this pipeline.<br>Leave blank to use the default FWC AI/ML JD.</p>
        <textarea id="jdTextarea" style="width: 100%; height: 120px; margin-bottom: 10px; padding: 10px; border-radius: 6px; background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: var(--text);"></textarea>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <button type="button" id="saveJdBtn" class="primary">💾 Save JD</button>
          <span id="jdSaveResult" style="font-size: 13px;"></span>
        </div>
      </div>
    </details>
  `;
}

function renderCandidates() {
  return `
    ${canManagePeople() ? jdConfigPanel() + candidateForm() : ""}
    <section class="section">
      <h2>Autonomous Pipeline</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Name</th><th>Matched Skills</th><th>ATS Format</th><th>ATS Keywords</th><th>JD Relevancy</th><th>Overall Score</th><th>AI Decision</th><th>Justification</th></tr></thead>
          <tbody>
            ${state.data.candidates
              .map(
                (candidate) => `
                  <tr>
                    <td>${renderName(candidate)}</td>
                    <td style="max-width: 200px; white-space: normal;">${renderSkills(candidate)}</td>
                    <td>${renderProgressBar(candidate.atsFormalScore)}</td>
                    <td>${renderProgressBar(candidate.atsKeywordScore)}</td>
                    <td>${renderProgressBar(candidate.jdRelevancyScore)}</td>
                    <td>${renderOverallScore(candidate.aiScore)}</td>
                    <td>${renderDecisionBadge(candidate.recommendation)}</td>
                    <td style="max-width: 250px; white-space: normal; font-size: 13px;">${renderJustification(candidate.justification, candidate.id)}</td>
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function candidateForm() {
  return `
    <section class="section">
      <h2>Autonomous AI Screening Intake</h2>
      <form id="candidateForm" class="form-grid">
        <label class="full">Candidate Name (optional — AI will extract from resume)<input type="text" name="name" placeholder="Leave blank for auto-extraction"></label>
        
        <div class="full" style="margin-top: 10px; border-top: 1px solid var(--border); padding-top: 15px;">
          <h3>Batch Resume Upload</h3>
          <p style="margin-bottom: 10px; color: var(--text-muted); font-size: 14px;">Select multiple PDF or DOCX files. They will be parsed by our Python backend.</p>
          <input type="file" id="resumeUpload" multiple accept=".pdf,.docx" required style="padding: 10px; background: rgba(255,255,255,0.05); border-radius: 6px; width: 100%; border: 1px solid var(--border);" />
        </div>
        
        <div class="form-actions full" style="margin-top: 15px;">
          <button type="submit" id="screenBtn">Run Autonomous Screening</button>
        </div>
      </form>
    </section>
  `;
}

/* ═══════════════════════════════════════
   PERFORMANCE
   ═══════════════════════════════════════ */

function renderPerformance() {
  return `
    ${canReview() ? performanceForm() : ""}
    <section class="section">
      <h2>Performance Reviews</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Employee</th><th>Rating</th><th>Feedback</th><th>AI Summary</th>${canReview() ? "<th>Risk</th>" : ""}</tr></thead>
          <tbody>
            ${state.data.performance
              .map(
                (review) => `
                  <tr>
                    <td>${employeeName(review.employeeId)}</td>
                    <td>${ratingStars(review.rating)}</td>
                    <td>${escHtml(review.feedback)}</td>
                    <td><div class="ai-badge"><span class="pulse-dot"></span> AI</div><br/>${escHtml(review.aiSummary)}</td>
                    ${canReview() ? `<td><button class="secondary" data-attrition="${review.employeeId}">Attrition Risk</button></td>` : ""}
                  </tr>
                `
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function ratingStars(rating) {
  const full = "★".repeat(Math.min(5, Math.max(0, rating)));
  const empty = "☆".repeat(5 - full.length);
  const color = rating >= 4 ? "var(--green)" : rating >= 3 ? "var(--amber)" : "var(--coral)";
  return `<span style="color:${color};font-size:16px;letter-spacing:2px">${full}${empty}</span>`;
}

function performanceForm() {
  return `
    <section class="section">
      <h2>Add Review</h2>
      <form id="performanceForm" class="form-grid">
        ${employeeSelect("employeeId", false)}
        <label>Rating
          <select name="rating">
            <option value="5">5 — Excellent</option>
            <option value="4">4 — Good</option>
            <option value="3">3 — Average</option>
            <option value="2">2 — Needs Improvement</option>
            <option value="1">1 — Poor</option>
          </select>
        </label>
        <label class="full">Feedback<textarea name="feedback" required></textarea></label>
        <div class="form-actions full"><button type="submit">Create AI Review</button></div>
      </form>
    </section>
  `;
}

/* ═══════════════════════════════════════
   CHATBOT
   ═══════════════════════════════════════ */

function renderChatbot() {
  const isHR = canManagePeople();
  const options = state.data.candidates
    .filter(c => ['Shortlisted', 'Under Review'].includes(c.aiDecision))
    .map(c => `<option value="${c.id}">${escHtml(c.name)} (${c.aiDecision})</option>`)
    .join("");

  return `
    <section class="section">
      <h2>AI Recruiter & HR Assistant</h2>
      <form id="chatForm" class="form-grid">
        ${isHR ? `
        <label class="full">Mode / Candidate
          <select name="candidateId">
            <option value="">General HR Query Mode</option>
            ${options}
          </select>
        </label>` : ""}
        <label class="full">Message
          <input name="question" placeholder="Ask a question or start an interview..." required />
        </label>
        <div class="form-actions full">
          <button type="submit">Send to AI</button>
          <button type="button" class="secondary" id="voiceBtn">🎤 Voice Input</button>
        </div>
      </form>
      <div style="margin-top:16px">
        <div class="ai-badge"><span class="pulse-dot"></span> AI Response</div>
      </div>
      <div id="chatOutput" class="ai-output">Select a candidate to start an AI screening interview, or ask an HR question.</div>
    </section>
  `;
}

/* ═══════════════════════════════════════
   EVENT HANDLERS
   ═══════════════════════════════════════ */

function attachPageEvents() {
  const jdPanel = document.querySelector("#jdPanel");
  if (jdPanel) {
    jdPanel.addEventListener("toggle", async () => {
      if (jdPanel.open) {
        const statusSpan = document.querySelector("#jdStatus");
        statusSpan.textContent = "Loading...";
        try {
          const res = await api("/api/jd");
          document.querySelector("#jdTextarea").value = res.jdText || "";
          statusSpan.innerHTML = res.jdText ? "✅ Custom JD saved" : "ℹ️ Using default JD";
        } catch (err) {
          statusSpan.textContent = "Error loading JD";
        }
      } else {
        document.querySelector("#jdStatus").textContent = "[▼ Configure]";
      }
    });

    const saveJdBtn = document.querySelector("#saveJdBtn");
    if (saveJdBtn) {
      saveJdBtn.addEventListener("click", async () => {
        const btn = document.querySelector("#saveJdBtn");
        const resultSpan = document.querySelector("#jdSaveResult");
        btn.disabled = true;
        btn.textContent = "Saving...";
        try {
          await api("/api/jd", {
            method: "POST",
            body: JSON.stringify({ jdText: document.querySelector("#jdTextarea").value })
          });
          resultSpan.textContent = "✅ Saved!";
          resultSpan.style.color = "var(--green)";
          setTimeout(() => { resultSpan.textContent = ""; }, 3000);
        } catch (err) {
          resultSpan.textContent = "❌ Error saving";
          resultSpan.style.color = "var(--coral)";
        }
        btn.disabled = false;
        btn.textContent = "💾 Save JD";
      });
    }
  }

  const employeeFormElement = document.querySelector("#employeeForm");
  if (employeeFormElement) employeeFormElement.addEventListener("submit", handleEmployeeSubmit);

  const attendanceForm = document.querySelector("#attendanceForm");
  if (attendanceForm) attendanceForm.addEventListener("submit", handleAttendanceSubmit);

  const attFilter = document.querySelector("#attFilterDate");
  if (attFilter) {
    attFilter.addEventListener("change", (e) => {
      state.attendanceFilterDate = e.target.value;
      renderApp();
    });
  }

  const leaveForm = document.querySelector("#leaveForm");
  if (leaveForm) leaveForm.addEventListener("submit", handleLeaveSubmit);

  document.querySelectorAll("[data-leave]").forEach((button) => {
    button.addEventListener("click", () => updateLeave(button.dataset.leave, button.dataset.status));
  });

  const candidateFormElement = document.querySelector("#candidateForm");
  if (candidateFormElement) candidateFormElement.addEventListener("submit", handleCandidateSubmit);

  document.querySelectorAll("[data-interview-cand]").forEach((button) => {
    button.addEventListener("click", () => {
      state.page = "chatbot";
      renderApp();
      setTimeout(() => {
        const select = document.querySelector("select[name='candidateId']");
        if (select) {
          select.value = button.dataset.interviewCand;
          document.querySelector("#chatForm").dispatchEvent(new Event("submit"));
        }
      }, 100);
    });
  });

  const performanceFormElement = document.querySelector("#performanceForm");
  if (performanceFormElement) performanceFormElement.addEventListener("submit", handlePerformanceSubmit);

  const chatForm = document.querySelector("#chatForm");
  if (chatForm) chatForm.addEventListener("submit", handleChatSubmit);

  const voiceBtn = document.querySelector("#voiceBtn");
  if (voiceBtn) voiceBtn.addEventListener("click", startVoiceInput);

  /* Attrition risk buttons */
  document.querySelectorAll("[data-attrition]").forEach((button) => {
    button.addEventListener("click", () => showAttritionRisk(button.dataset.attrition));
  });

  /* Bulk upload button */
  const bulkBtn = document.querySelector("#bulkUploadBtn");
  if (bulkBtn) bulkBtn.addEventListener("click", showBulkUploadModal);

  /* Announcement form */
  const annForm = document.querySelector("#announcementForm");
  if (annForm) annForm.addEventListener("submit", handleAnnouncementSubmit);

  /* Delete employee */
  document.querySelectorAll("[data-delete-emp]").forEach((button) => {
    button.addEventListener("click", async () => {
      if (!confirm("Delete this employee?")) return;
      await api(`/api/employees/${button.dataset.deleteEmp}`, { method: "DELETE" });
      showToast("Employee deleted.");
      await refresh();
    });
  });
}

async function refresh() {
  await loadAllData();
  renderApp();
}

async function handleEmployeeSubmit(event) {
  event.preventDefault();
  const body = formBody(event.target);
  await api("/api/employees", { method: "POST", body: JSON.stringify(body) });
  showToast("Employee added successfully.");
  await refresh();
}

async function handleAttendanceSubmit(event) {
  event.preventDefault();
  const body = formBody(event.target);
  await api("/api/attendance", { method: "POST", body: JSON.stringify(body) });
  showToast("Attendance saved.");
  await refresh();
}

async function handleLeaveSubmit(event) {
  event.preventDefault();
  const body = formBody(event.target);
  await api("/api/leaves", { method: "POST", body: JSON.stringify(body) });
  showToast("Leave request submitted.");
  await refresh();
}

async function updateLeave(id, status) {
  await api(`/api/leaves/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
  showToast(`Leave ${status.toLowerCase()}.`);
  await refresh();
}

async function handleCandidateSubmit(event) {
  event.preventDefault();
  const form = event.target;
  const btn = form.querySelector("button[type='submit']");
  btn.innerHTML = `<span class="loading-spinner">Python Parsing & AI Screening...</span>`;
  btn.disabled = true;
  
  try {
    const nameInput = form.querySelector("[name='name']");
    const name = nameInput ? nameInput.value : "";
    const fileInput = form.querySelector("#resumeUpload");
    
    if (!fileInput.files.length) throw new Error("Please select at least one resume.");

    const resumes = await Promise.all(Array.from(fileInput.files).map(file => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = e => resolve({ name: file.name, data: e.target.result });
        reader.onerror = e => reject(new Error("File reading failed"));
        reader.readAsDataURL(file);
      });
    }));

    await api("/api/candidates", { 
      method: "POST", 
      body: JSON.stringify({ name, resumes }) 
    });
    
    showToast(`Screening completed for ${resumes.length} candidate(s).`);
    await refresh();
  } catch (e) {
    showToast(e.message);
    btn.textContent = "Run Autonomous Screening";
    btn.disabled = false;
  }
}

async function handlePerformanceSubmit(event) {
  event.preventDefault();
  const btn = event.target.querySelector("button[type='submit']");
  btn.innerHTML = `<span class="loading-spinner">Creating AI Review...</span>`;
  btn.disabled = true;
  try {
    const body = formBody(event.target);
    await api("/api/performance", { method: "POST", body: JSON.stringify(body) });
    showToast("Performance review created.");
    await refresh();
  } catch (e) {
    showToast(e.message);
    btn.textContent = "Create AI Review";
    btn.disabled = false;
  }
}

async function handleChatSubmit(event) {
  event.preventDefault();
  const output = document.querySelector("#chatOutput");
  output.innerHTML = `<span class="loading-spinner">AI is thinking...</span>`;
  try {
    const body = formBody(event.target);
    const data = await api("/api/ai/chatbot", { method: "POST", body: JSON.stringify(body) });
    typewriterEffect(output, data.answer);
  } catch (e) {
    output.textContent = "Sorry, something went wrong. Please try again.";
  }
}

function startVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showToast("Voice input is not supported in this browser.");
    return;
  }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-IN";
  recognition.onresult = (event) => {
    document.querySelector("[name='question']").value = event.results[0][0].transcript;
  };
  recognition.start();
  showToast("Listening... speak now.");
}

/* ═══════════════════════════════════════
   ANNOUNCEMENTS
   ═══════════════════════════════════════ */

async function handleAnnouncementSubmit(event) {
  event.preventDefault();
  const body = formBody(event.target);
  await api("/api/announcements", { method: "POST", body: JSON.stringify(body) });
  showToast("Announcement published.");
  await refresh();
}

/* ═══════════════════════════════════════
   ATTRITION RISK MODAL
   ═══════════════════════════════════════ */

async function showAttritionRisk(employeeId) {
  const empName = employeeName(employeeId);

  /* Show loading overlay */
  const overlay = document.createElement("div");
  overlay.className = "risk-overlay";
  overlay.innerHTML = `
    <div class="risk-card">
      <h3>Attrition Risk Analysis</h3>
      <p><span class="loading-spinner">Analysing ${escHtml(empName)} with AI...</span></p>
    </div>
  `;
  document.body.appendChild(overlay);

  try {
    const result = await api("/api/ai/attrition-risk", {
      method: "POST",
      body: JSON.stringify({ employeeId })
    });

    const riskClass = result.riskLevel.toLowerCase();
    const riskEmoji = riskClass === "high" ? "🔴" : riskClass === "medium" ? "🟡" : "🟢";

    overlay.innerHTML = `
      <div class="risk-card">
        <h3>${riskEmoji} Attrition Risk — ${escHtml(empName)}</h3>
        <div class="risk-badge ${riskClass}">${result.riskLevel} Risk</div>
        <div class="risk-confidence">Confidence: ${result.confidence}%</div>

        <strong style="color:var(--ink-muted);font-size:12px;text-transform:uppercase;letter-spacing:0.06em">Key Factors</strong>
        <ul class="risk-factors">
          ${result.factors.map(f => `<li>${escHtml(f)}</li>`).join("")}
        </ul>

        <div class="risk-action-label">Recommended Action</div>
        <div class="risk-action">${escHtml(result.retentionAction)}</div>

        <button class="secondary risk-close">Close</button>
      </div>
    `;
  } catch (e) {
    overlay.innerHTML = `
      <div class="risk-card">
        <h3>Error</h3>
        <p style="color:var(--coral)">${escHtml(e.message)}</p>
        <button class="secondary risk-close" style="margin-top:16px">Close</button>
      </div>
    `;
  }

  overlay.querySelector(".risk-close")?.addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });
}

/* ═══════════════════════════════════════
   BULK ATTENDANCE UPLOAD MODAL
   ═══════════════════════════════════════ */

function showBulkUploadModal() {
  const overlay = document.createElement("div");
  overlay.className = "bulk-modal";
  overlay.innerHTML = `
    <div class="bulk-card">
      <h3>Bulk Attendance Upload</h3>
      <p class="bulk-hint">Paste CSV data — one row per entry:<br/><code>employeeId,date,status</code><br/>Example: <code>emp-1,2026-06-05,Present</code></p>
      <textarea id="bulkCsvInput" placeholder="emp-1,2026-06-05,Present
emp-2,2026-06-05,Absent
emp-3,2026-06-05,Present"></textarea>
      <div id="bulkResult"></div>
      <div class="form-actions" style="margin-top:16px">
        <button id="bulkSubmitBtn">Upload Attendance</button>
        <button class="secondary" id="bulkCancelBtn">Cancel</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  overlay.querySelector("#bulkCancelBtn").addEventListener("click", () => overlay.remove());
  overlay.addEventListener("click", (e) => { if (e.target === overlay) overlay.remove(); });

  overlay.querySelector("#bulkSubmitBtn").addEventListener("click", async () => {
    const csv = document.querySelector("#bulkCsvInput").value.trim();
    if (!csv) { showToast("Please paste CSV data."); return; }

    const records = csv.split("\n").map(line => {
      const [employeeId, date, status] = line.split(",").map(s => s.trim());
      return { employeeId, date, status };
    }).filter(r => r.employeeId && r.date && r.status);

    if (!records.length) {
      showToast("No valid records found in the CSV.");
      return;
    }

    const btn = overlay.querySelector("#bulkSubmitBtn");
    btn.innerHTML = `<span class="loading-spinner">Uploading...</span>`;
    btn.disabled = true;

    try {
      const result = await api("/api/attendance/bulk", {
        method: "POST",
        body: JSON.stringify({ records })
      });

      const resultDiv = overlay.querySelector("#bulkResult");
      resultDiv.className = `bulk-result ${result.errors?.length ? "error" : "success"}`;
      resultDiv.innerHTML = `
        ✅ Inserted: ${result.inserted} &nbsp; ⏭ Skipped: ${result.skipped} &nbsp; ❌ Errors: ${result.errors?.length || 0}
        ${result.errors?.length ? `<br/><br/>${result.errors.map(e => `Row ${e.row}: ${escHtml(e.reason)}`).join("<br/>")}` : ""}
      `;

      btn.textContent = "Done";
      btn.disabled = false;
      btn.addEventListener("click", async () => {
        overlay.remove();
        await refresh();
      }, { once: true });
    } catch (e) {
      showToast(e.message);
      btn.textContent = "Upload Attendance";
      btn.disabled = false;
    }
  });
}

/* ═══════════════════════════════════════
   TYPEWRITER EFFECT
   ═══════════════════════════════════════ */

function typewriterEffect(element, text) {
  element.textContent = "";
  element.classList.add("typewriter-cursor");
  let i = 0;
  const speed = 12;
  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    } else {
      element.classList.remove("typewriter-cursor");
    }
  }
  type();
}

/* ═══════════════════════════════════════
   UTILITIES
   ═══════════════════════════════════════ */

function formBody(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function employeeSelect(name, disabled) {
  return `
    <label>Employee
      <select name="${name}" ${disabled ? "disabled" : ""}>
        ${state.data.employees.map((employee) => `<option value="${employee.id}">${escHtml(employee.name)}</option>`).join("")}
      </select>
    </label>
  `;
}

function employeeName(id) {
  return state.data.employees.find((employee) => employee.id === id)?.name || "Unknown";
}

function money(value) {
  return `₹${Number(value || 0).toLocaleString("en-IN")}`;
}

function today() {
  return new Date().toISOString().slice(0, 10);
}

function escHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

function escAttr(str) {
  return (str || "").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

/* ═══════════════════════════════════════
   BOOT
   ═══════════════════════════════════════ */

async function boot() {
  if (!state.token) {
    renderLogin();
    return;
  }
  try {
    await loadAllData();
    renderApp();
  } catch (error) {
    clearSession();
    renderLogin();
  }
}

boot();
