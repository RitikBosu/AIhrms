"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";

const COLORS = ['#2ed573', '#ff4757', '#ffa502'];

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
              <div className="stat-value">{data.companyOverview.totalOpenPositions || 0}</div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginTop: "24px" }}>
            <div style={{ background: "var(--bg-card)", padding: "16px", borderRadius: "var(--radius)" }}>
              <h3 style={{ marginBottom: "16px", color: "var(--ink-muted)" }}>Average Salary by Department</h3>
              <div style={{ height: "250px" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.companyOverview.avgSalaryByDepartment || []}>
                    <XAxis dataKey="department" stroke="var(--ink-muted)" fontSize={12} />
                    <YAxis stroke="var(--ink-muted)" fontSize={12} tickFormatter={(val) => `₹${val/1000}k`} />
                    <Tooltip cursor={{ fill: "var(--bg-card-hover)" }} contentStyle={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: "8px" }} />
                    <Bar dataKey="avgSalary" fill="var(--cyan)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div style={{ background: "var(--bg-card)", padding: "16px", borderRadius: "var(--radius)" }}>
              <h3 style={{ marginBottom: "16px", color: "var(--ink-muted)" }}>Leave Approval Status</h3>
              <div style={{ height: "250px" }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={data.companyOverview.leaveApprovalRate ? [
                        { name: 'Approved', value: data.companyOverview.leaveApprovalRate.approved },
                        { name: 'Rejected', value: data.companyOverview.leaveApprovalRate.rejected },
                        { name: 'Pending', value: data.companyOverview.leaveApprovalRate.pending }
                      ] : []}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {data.companyOverview.leaveApprovalRate && [0, 1, 2].map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ background: "var(--bg-surface)", border: "1px solid var(--border)", borderRadius: "8px" }} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </section>
      )}
    </AppLayout>
  );
}
