"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function PayrollPage() {
  const { token, user } = useAuth();
  const [payroll, setPayroll] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchPayroll = async () => {
    try {
      const res = await fetch("/api/payroll", { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setPayroll(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchPayroll();
  }, [token]);

  const formatMoney = (val: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) return <AppLayout title="Payroll" subtitle="Automated salary calculations based on attendance."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Payroll" subtitle="Automated salary calculations based on attendance.">
      <section className="section">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <h2>Current Month Payroll</h2>
          <button className="primary" onClick={handlePrint}>Print / Export</button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {user?.role !== "employee" && <th>Employee</th>}
                <th>Basic Salary</th>
                <th>Present Days</th>
                <th>Absent Days</th>
                <th>Allowance (+10%)</th>
                <th>Deduction (-₹500/absent)</th>
                <th>Net Salary</th>
              </tr>
            </thead>
            <tbody>
              {payroll.map(p => (
                <tr key={p.employeeId}>
                  {user?.role !== "employee" && <td>{p.name} <br/><small className="text-zinc-500">{p.employeeId}</small></td>}
                  <td>{formatMoney(p.basicSalary)}</td>
                  <td>{p.presentDays}</td>
                  <td><span className={p.absentDays > 0 ? "status-badge rejected" : ""}>{p.absentDays}</span></td>
                  <td style={{ color: "var(--cyan)" }}>+{formatMoney(p.allowance)}</td>
                  <td style={{ color: "var(--coral)" }}>-{formatMoney(p.deduction)}</td>
                  <td><strong>{formatMoney(p.netSalary)}</strong></td>
                </tr>
              ))}
              {payroll.length === 0 && (
                <tr><td colSpan={user?.role !== "employee" ? 7 : 6} style={{ textAlign: "center" }}>No payroll data found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}
