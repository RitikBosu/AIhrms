"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { toast } from "@/components/toast";

export default function LeavesPage() {
  const { token, user } = useAuth();
  const [leaves, setLeaves] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [type, setType] = useState("Sick Leave");
  const [reason, setReason] = useState("");

  const fetchLeaves = async () => {
    try {
      const res = await fetch("/api/leaves", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setLeaves(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchLeaves();
  }, [token]);

  const handleRequestLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/leaves", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ fromDate, toDate, type, reason })
      });
      if (res.ok) {
        setFromDate(""); setToDate(""); setType("Sick Leave"); setReason("");
        fetchLeaves();
        toast.success("Leave requested successfully.");
      } else {
        const err = await res.json();
        toast.error(err.detail?.[0]?.msg || err.detail || "Error requesting leave");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error");
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

  if (loading) return <AppLayout title="Leaves" subtitle="Manage leave requests and approvals."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Leaves" subtitle="Manage leave requests and approvals.">
      <section className="section">
        <h2>Request Leave</h2>
        <form onSubmit={handleRequestLeave} className="form-grid">
          <label>From Date<input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} required /></label>
          <label>To Date<input type="date" value={toDate} onChange={e => setToDate(e.target.value)} required /></label>
          <label>Leave Type
            <select value={type} onChange={e => setType(e.target.value)}>
              <option value="Sick Leave">Sick Leave</option>
              <option value="Casual Leave">Casual Leave</option>
              <option value="Earned Leave">Earned Leave</option>
              <option value="Unpaid Leave">Unpaid Leave</option>
            </select>
          </label>
          <label className="full">Reason<textarea value={reason} onChange={e => setReason(e.target.value)} rows={3} required></textarea></label>
          <div className="form-actions full"><button type="submit" className="primary">Submit Request</button></div>
        </form>
      </section>

      <section className="section">
        <h2>Leave History & Approvals</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {user?.role !== "employee" && <th>Employee ID</th>}
                <th>Date Range</th>
                <th>Type</th>
                <th>Reason</th>
                <th>Status</th>
                {(user?.role === "admin" || user?.role === "hr") && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {leaves.sort((a,b) => new Date(b.requestedOn).getTime() - new Date(a.requestedOn).getTime()).map(l => (
                <tr key={l.id}>
                  {user?.role !== "employee" && <td>{l.employeeId}</td>}
                  <td>{l.fromDate} to {l.toDate}</td>
                  <td>{l.type}</td>
                  <td>{l.reason}</td>
                  <td><span className={`status-badge ${l.status.toLowerCase()}`}>{l.status}</span></td>
                  {(user?.role === "admin" || user?.role === "hr") && (
                    <td>
                      {l.status === "Pending" ? (
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="primary" onClick={() => handleProcess(l.id, "approve")}>Approve</button>
                          <button className="danger" onClick={() => handleProcess(l.id, "reject")}>Reject</button>
                        </div>
                      ) : "-"}
                    </td>
                  )}
                </tr>
              ))}
              {leaves.length === 0 && (
                <tr><td colSpan={user?.role === "admin" || user?.role === "hr" ? 6 : (user?.role !== "employee" ? 5 : 4)} style={{ textAlign: "center" }}>No leave requests found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}
