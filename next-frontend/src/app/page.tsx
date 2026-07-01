"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function DashboardPage() {
  const { token, user } = useAuth();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (token) {
      fetch("/api/dashboard", {
        headers: { Authorization: `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(d => setData(d))
      .catch(console.error);
    }
  }, [token]);

  if (!data) return <AppLayout title="Dashboard" subtitle="Real-time company overview with AI-powered insights."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Dashboard" subtitle="Real-time company overview with AI-powered insights.">
      <div className="stats">
        <div className="stat">
          <div className="stat-header">
            <div className="stat-icon green">📋</div>
          </div>
          <div className="stat-label">Personal Attendance</div>
          <div className="stat-value">{data.myActivity?.myAttendanceRate || 100}%</div>
        </div>
        <div className="stat">
          <div className="stat-header">
            <div className="stat-icon amber">📄</div>
          </div>
          <div className="stat-label">Leave Balance</div>
          <div className="stat-value">{(data.myActivity?.myLeaveBalance?.total || 18) - (data.myActivity?.myLeaveBalance?.used || 0)} days</div>
        </div>
        <div className="stat">
          <div className="stat-header">
            <div className="stat-icon purple">⏳</div>
          </div>
          <div className="stat-label">Pending Leaves</div>
          <div className="stat-value">{data.myActivity?.myLeaveBalance?.pending || 0}</div>
        </div>
        <div className="stat">
          <div className="stat-header">
            <div className="stat-icon cyan">🔔</div>
          </div>
          <div className="stat-label">Announcements</div>
          <div className="stat-value">{data.announcements?.length || 0}</div>
        </div>
      </div>

      {user?.role === "admin" && data.companyOverview && (
        <section className="section" style={{ marginBottom: 20, border: "1px solid var(--cyan)", background: "rgba(0, 212, 255, 0.05)" }}>
          <h2 style={{ color: "var(--cyan)" }}>🏢 Company Overview (Admin)</h2>
          <div className="stats" style={{ marginTop: 10 }}>
            <div className="stat">
              <div className="stat-label">Total Employees</div>
              <div className="stat-value">{data.companyOverview.totalEmployees}</div>
            </div>
            <div className="stat">
              <div className="stat-label">Overall Attendance</div>
              <div className="stat-value">{data.companyOverview.overallAttendanceRate}%</div>
            </div>
            <div className="stat">
              <div className="stat-label">Open Positions</div>
              <div className="stat-value">{data.companyOverview.totalOpenPositions}</div>
            </div>
          </div>
        </section>
      )}
    </AppLayout>
  );
}
