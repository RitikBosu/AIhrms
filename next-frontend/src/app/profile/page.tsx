"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function ProfilePage() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [payroll, setPayroll] = useState<any>(null);
  const [leaves, setLeaves] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any[]>([]);
  const [shifts, setShifts] = useState<any[]>([]);
  const [colleagues, setColleagues] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Shift Swap State
  const [swapShiftId, setSwapShiftId] = useState<number | null>(null);
  const [swapTargetId, setSwapTargetId] = useState<string>("");

  const fetchProfileData = async () => {
    try {
      // Get dates for upcoming shifts (today onwards)
      const today = new Date().toISOString().split("T")[0];
      
      const [empRes, payRes, leaveRes, perfRes, shiftsRes, allEmpRes] = await Promise.all([
        fetch("/api/employees", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/payroll", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/leaves", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/performance", { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`/api/shifts?start_date=${today}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/employees", { headers: { Authorization: `Bearer ${token}` } }) // To get colleagues for swap
      ]);

      if (empRes.ok) {
        const empData = await empRes.json();
        if (empData.length > 0) setProfile(empData[0]);
      }
      if (payRes.ok) {
        const payData = await payRes.json();
        if (payData.length > 0) setPayroll(payData[0]);
      }
      if (leaveRes.ok) setLeaves(await leaveRes.json());
      if (perfRes.ok) setPerformance(await perfRes.json());
      if (shiftsRes.ok) setShifts(await shiftsRes.json());
      if (allEmpRes.ok) {
        const all = await allEmpRes.json();
        // Filter out self
        const me = await empRes.clone().json();
        const myId = me.length > 0 ? me[0].id : null;
        setColleagues(all.filter((e:any) => e.id !== myId));
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchProfileData();
  }, [token]);

  const formatMoney = (val: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val || 0);
  };

  const handleRequestSwap = async (shiftId: number) => {
    if (!swapTargetId) {
      alert("Please select a colleague to swap with.");
      return;
    }
    try {
      const res = await fetch("/api/swaps", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ shift_id: shiftId, target_id: parseInt(swapTargetId) })
      });
      if (res.ok) {
        alert("Swap request sent successfully!");
        setSwapShiftId(null);
        setSwapTargetId("");
        fetchProfileData();
      } else {
        const err = await res.json();
        alert(err.detail || "Error requesting swap");
      }
    } catch (e) {
      alert("Network error");
    }
  };

  if (loading) return <AppLayout title="My Profile" subtitle="Manage your personal details and records."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="My Profile" subtitle="Manage your personal details and records.">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        
        <section className="section">
          <h2>Personal Details</h2>
          {profile ? (
            <div style={{ background: "var(--bg-card)", padding: "20px", borderRadius: "12px", border: "1px solid var(--border)" }}>
              <p><strong>Name:</strong> {profile.name}</p>
              <p><strong>Email:</strong> {profile.email}</p>
              <p><strong>Department:</strong> {profile.department}</p>
              <p><strong>Designation:</strong> {profile.designation}</p>
              <p><strong>Joining Date:</strong> {profile.joiningDate}</p>
            </div>
          ) : (
            <p>Profile details not found.</p>
          )}
        </section>

        <section className="section">
          <h2>Current Payslip</h2>
          {payroll ? (
            <div style={{ background: "var(--bg-card)", padding: "20px", borderRadius: "12px", border: "1px solid var(--border)" }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span>Basic Salary</span>
                <strong>{formatMoney(payroll.basicSalary)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: "var(--green)" }}>
                <span>Allowances (+10%)</span>
                <strong>+{formatMoney(payroll.allowance)}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', color: "var(--coral)" }}>
                <span>Deductions ({payroll.absentDays} days)</span>
                <strong>-{formatMoney(payroll.deduction)}</strong>
              </div>
              <hr style={{ borderTop: "1px solid var(--border)", marginBottom: '16px' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', color: "var(--cyan)" }}>
                <span>Net Payable</span>
                <strong>{formatMoney(payroll.netSalary)}</strong>
              </div>
            </div>
          ) : (
            <p>Payroll details not available.</p>
          )}
        </section>

        <section className="section" style={{ gridColumn: "1 / -1" }}>
          <h2>My Upcoming Shifts</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Shift Title</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {shifts.map(s => (
                  <tr key={s.id}>
                    <td>{new Date(s.start_time).toLocaleString()} - {new Date(s.end_time).toLocaleTimeString()}</td>
                    <td>{s.title}</td>
                    <td><span className={`status-badge ${s.status.toLowerCase()}`}>{s.status}</span></td>
                    <td>
                      {s.status === "Scheduled" && (
                        swapShiftId === s.id ? (
                          <div style={{ display: "flex", gap: "5px" }}>
                            <select value={swapTargetId} onChange={e => setSwapTargetId(e.target.value)} style={{ padding: "5px" }}>
                              <option value="">Select Colleague</option>
                              {colleagues.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                            </select>
                            <button className="primary" style={{ padding: "5px 10px" }} onClick={() => handleRequestSwap(s.id)}>Send</button>
                            <button className="secondary" style={{ padding: "5px 10px" }} onClick={() => setSwapShiftId(null)}>Cancel</button>
                          </div>
                        ) : (
                          <button className="secondary" style={{ padding: "5px 10px" }} onClick={() => setSwapShiftId(s.id)}>Request Swap</button>
                        )
                      )}
                      {s.status === "SwapRequested" && <span style={{ color: "var(--amber)", fontSize: "0.85rem" }}>Swap Pending...</span>}
                    </td>
                  </tr>
                ))}
                {shifts.length === 0 && (
                  <tr><td colSpan={4} style={{ textAlign: "center" }}>No upcoming shifts.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="section">
          <h2>My Leave History</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date Range</th>
                  <th>Type</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {leaves.map(l => (
                  <tr key={l.id}>
                    <td>{l.fromDate} to {l.toDate}</td>
                    <td>{l.type}</td>
                    <td><span className={`status-badge ${l.status.toLowerCase()}`}>{l.status}</span></td>
                  </tr>
                ))}
                {leaves.length === 0 && (
                  <tr><td colSpan={3} style={{ textAlign: "center" }}>No leaves requested.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="section">
          <h2>My Performance Reviews</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {performance.map(p => (
              <div key={p.id} style={{ background: "var(--bg-card)", padding: "16px", borderRadius: "12px", border: "1px solid var(--border)" }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <strong>Rating: {p.rating}/5</strong>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {[1,2,3,4,5].map(star => (
                      <span key={star} style={{ color: star <= p.rating ? "var(--cyan)" : "var(--border)" }}>★</span>
                    ))}
                  </div>
                </div>
                <p style={{ margin: 0, color: "var(--ink-muted)", fontSize: '0.9rem' }}>{p.feedback}</p>
                {p.aiSummary && (
                  <div style={{ marginTop: '12px', padding: '12px', background: "rgba(0, 212, 255, 0.05)", borderLeft: "3px solid var(--cyan)", borderRadius: "4px" }}>
                    <small style={{ color: "var(--cyan)", display: 'block', marginBottom: '4px' }}>AI Summary</small>
                    <span style={{ fontSize: '0.85rem' }}>{p.aiSummary}</span>
                  </div>
                )}
              </div>
            ))}
            {performance.length === 0 && (
              <div style={{ background: "var(--bg-card)", padding: "20px", borderRadius: "12px", textAlign: "center", border: "1px solid var(--border)" }}>
                No performance reviews available.
              </div>
            )}
          </div>
        </section>

      </div>
    </AppLayout>
  );
}
