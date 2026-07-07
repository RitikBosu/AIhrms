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
  const [loading, setLoading] = useState(true);

  const fetchProfileData = async () => {
    try {
      const [empRes, payRes, leaveRes, perfRes] = await Promise.all([
        fetch("/api/employees", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/payroll", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/leaves", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/performance", { headers: { Authorization: `Bearer ${token}` } })
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
