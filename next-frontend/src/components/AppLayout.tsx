"use client";

import { useAuth } from "@/context/auth-context";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { ToastContainer } from "./toast";

const ROLE_LABELS = {
  admin: "Management Admin",
  manager: "Senior Manager",
  hr: "HR Recruiter",
  employee: "Employee",
};

export default function AppLayout({ children, title, subtitle }: { children: React.ReactNode, title: string, subtitle: string }) {
  const { user, logout } = useAuth();
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  const [pendingLeaves, setPendingLeaves] = useState(0);

  useEffect(() => {
    if (!user) {
      router.push("/login");
    } else if (user.role === "admin" || user.role === "hr") {
      fetch("/api/dashboard", { headers: { Authorization: `Bearer ${localStorage.getItem("fwcToken")}` } })
        .then(res => res.json())
        .then(data => {
          if (data.pendingLeaves) setPendingLeaves(data.pendingLeaves);
        })
        .catch(console.error);
    }
  }, [user, router]);

  if (!user) return null;

  return (
    <>
      <button className="hamburger" id="hamburgerBtn" onClick={() => setSidebarOpen(!sidebarOpen)}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>

      <div 
        className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`} 
        onClick={() => setSidebarOpen(false)}
      ></div>

      <section className="app-shell">
        <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
          <div className="brand">
            <div className="brand-mark">FWC</div>
            <div>
              <strong>AI-HRMS</strong><br />
              <small>{user.name} ({ROLE_LABELS[user.role]})</small>
            </div>
          </div>
          <nav className="nav">
            <Link href="/"><button className={title === "Dashboard" ? "active" : ""}><span>Dashboard</span></button></Link>
            <Link href="/employees"><button className={title === "Employees" ? "active" : ""}><span>Employees</span></button></Link>
            <Link href="/attendance"><button className={title === "Attendance" ? "active" : ""}><span>Attendance</span></button></Link>
            <Link href="/leaves"><button className={title === "Leaves" ? "active" : ""}><span>Leaves</span></button></Link>
            <Link href="/payroll"><button className={title === "Payroll" ? "active" : ""}><span>Payroll</span></button></Link>
            {(user.role === "admin" || user.role === "hr" || user.role === "manager") && (
              <Link href="/scheduling"><button className={title === "Scheduling" ? "active" : ""}><span>Scheduling</span></button></Link>
            )}
            <Link href="/candidates"><button className={title === "AI Screening" ? "active" : ""}><span>AI Screening</span></button></Link>
            <Link href="/performance"><button className={title === "Performance" ? "active" : ""}><span>Performance</span></button></Link>
            <Link href="/profile"><button className={title === "My Profile" ? "active" : ""}><span>My Profile</span></button></Link>
            {user.role === "admin" && (
              <Link href="/audit"><button className={title === "Audit Logs" ? "active" : ""}><span>Audit Logs</span></button></Link>
            )}
          </nav>
          <div className="sidebar-logout">
            <button className="secondary" style={{ width: "100%" }} onClick={logout}>Logout</button>
          </div>
        </aside>

        <section className="main">
          <div className="topbar">
            <div className="page-title">
              <h1>{title}</h1>
              <p>{subtitle}</p>
            </div>
            <div className="topbar-actions">
              <div className="notif-wrapper">
                <button className="notif-bell" onClick={() => setNotifOpen(!notifOpen)} style={{ position: "relative" }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                  {pendingLeaves > 0 && (
                    <span style={{ position: "absolute", top: -5, right: -5, background: "var(--coral)", color: "white", borderRadius: "50%", padding: "2px 6px", fontSize: "10px", fontWeight: "bold" }}>
                      {pendingLeaves}
                    </span>
                  )}
                </button>
                {notifOpen && (
                  <div className="notif-dropdown open" style={{ display: 'block' }}>
                    <div className="notif-dropdown-header">Notifications</div>
                    {pendingLeaves > 0 ? (
                      <div className="notif-empty" style={{ color: "var(--amber)" }}>{pendingLeaves} pending leave requests</div>
                    ) : (
                      <div className="notif-empty">No new notifications</div>
                    )}
                  </div>
                )}
              </div>
              <span className="role-pill">{ROLE_LABELS[user.role]}</span>
              <button className="secondary" onClick={logout}>Logout</button>
            </div>
          </div>
          
          <div id="pageContent">{children}</div>
        </section>
      </section>
      <ToastContainer />
    </>
  );
}
