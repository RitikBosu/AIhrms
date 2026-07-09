"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { toast } from "@/components/toast";

export default function LeavesPage() {
  const { token, user } = useAuth();
  const [leaves, setLeaves] = useState<any[]>([]);
  const [balances, setBalances] = useState({ pto_balance_days: 0, sick_leave_balance_days: 0 });
  const [loading, setLoading] = useState(true);

  // Form State
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [type, setType] = useState("Sick");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchLeaves = async () => {
    try {
      const res = await fetch("/api/leaves", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setLeaves(await res.json());

      if (user?.role === "employee") {
        const balRes = await fetch("/api/leaves/balances", { headers: { Authorization: `Bearer ${token}` } });
        if (balRes.ok) setBalances(await balRes.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token && user) fetchLeaves();
  }, [token, user]);

  const handleRequestLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const res = await fetch("/api/leaves", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ fromDate, toDate, type, reason })
      });
      if (res.ok) {
        const data = await res.json();
        setFromDate(""); setToDate(""); setType("Sick"); setReason("");
        fetchLeaves();
        if (data.status === "Approved") {
          toast.success("AI Auto-Approved your leave! Balance updated.");
        } else {
          toast.success("Leave requested successfully. Sent for manual review.");
        }
      } else {
        const err = await res.json();
        toast.error(err.detail?.[0]?.msg || err.detail || "Error requesting leave");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleProcess = async (id: string, action: string) => {
    try {
      const res = await fetch(`/api/leaves/${id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ action })
      });
      if (res.ok) {
        toast.success(`Leave ${action}d successfully`);
        fetchLeaves();
      } else {
        toast.error("Failed to process leave");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error");
    }
  };

  if (loading || !user) return <AppLayout title="Leaves" subtitle="Manage leave requests and approvals."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Leaves" subtitle="Manage leave requests and approvals.">
      {user.role === "employee" && (
        <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
          <div className="stat-card" style={{ flex: 1, background: "var(--purple-dim)", border: "1px solid var(--purple)" }}>
            <h3>PTO Balance</h3>
            <p className="big-number">{balances.pto_balance_days} <span style={{fontSize: "14px", color: "var(--light-text)"}}>days</span></p>
          </div>
          <div className="stat-card" style={{ flex: 1, background: "var(--cyan-dim)", border: "1px solid var(--cyan)" }}>
            <h3>Sick Leave Balance</h3>
            <p className="big-number">{balances.sick_leave_balance_days} <span style={{fontSize: "14px", color: "var(--light-text)"}}>days</span></p>
          </div>
        </div>
      )}

      <section className="section">
        <h2>Request Leave</h2>
        <form onSubmit={handleRequestLeave} className="form-grid">
          <label>From Date<input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} required /></label>
          <label>To Date<input type="date" value={toDate} onChange={e => setToDate(e.target.value)} required /></label>
          <label>Leave Type
            <select value={type} onChange={e => setType(e.target.value)}>
              <option value="Sick">Sick Leave</option>
              <option value="Casual">Casual Leave</option>
              <option value="Earned">Earned Leave (PTO)</option>
              <option value="Unpaid">Unpaid Leave</option>
            </select>
          </label>
          <label className="full">Reason<textarea value={reason} onChange={e => setReason(e.target.value)} rows={3} required></textarea></label>
          <div className="form-actions full">
            <button type="submit" className="primary" disabled={isSubmitting}>
              {isSubmitting ? "AI is analyzing coverage & balances..." : "Submit Request"}
            </button>
          </div>
        </form>
      </section>

      <section className="section">
        <h2>Leave History & Approvals</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {user.role !== "employee" && <th>Employee ID</th>}
                <th>Date Range</th>
                <th>Type</th>
                <th>Reason</th>
                <th>Status</th>
                <th>AI Insight</th>
                {(user.role === "admin" || user.role === "hr") && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {leaves.sort((a,b) => new Date(b.requestedOn).getTime() - new Date(a.requestedOn).getTime()).map(l => (
                <tr key={l.id}>
                  {user.role !== "employee" && <td>{l.employeeId}</td>}
                  <td>{l.fromDate} to {l.toDate}</td>
                  <td>{l.type}</td>
                  <td>{l.reason}</td>
                  <td><span className={`status-badge ${l.status.toLowerCase()}`}>{l.status}</span></td>
                  <td style={{ fontSize: "12px", color: "var(--ink-muted)", maxWidth: "250px" }}>
                    {l.aiJustification ? (
                      <div>
                        {l.status === "Approved" && <span style={{ background: "var(--purple)", color: "white", padding: "2px 6px", borderRadius: "4px", marginRight: "6px" }}>✨ Auto-Approved</span>}
                        {l.status === "Pending" && <span style={{ background: "var(--coral)", color: "white", padding: "2px 6px", borderRadius: "4px", marginRight: "6px" }}>⚠️ Manual Review</span>}
                        {l.aiJustification}
                      </div>
                    ) : "-"}
                  </td>
                  {(user.role === "admin" || user.role === "hr") && (
                    <td>
                      {l.status === "Pending" ? (
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="primary" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => handleProcess(l.id, "approve")}>Approve</button>
                          <button className="danger" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => handleProcess(l.id, "reject")}>Reject</button>
                        </div>
                      ) : "-"}
                    </td>
                  )}
                </tr>
              ))}
              {leaves.length === 0 && (
                <tr><td colSpan={user.role === "admin" || user.role === "hr" ? 7 : (user.role !== "employee" ? 6 : 5)} style={{ textAlign: "center" }}>No leave requests found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}
