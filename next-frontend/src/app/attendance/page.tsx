"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { toast } from "@/components/toast";

export default function AttendancePage() {
  const { token, user } = useAuth();
  const [attendance, setAttendance] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Form State
  const [selectedEmp, setSelectedEmp] = useState("");
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [ipAddress, setIpAddress] = useState("");

  const getClientIP = async () => {
    try {
      const res = await fetch("https://api.ipify.org?format=json");
      const data = await res.json();
      setIpAddress(data.ip);
      return data.ip;
    } catch (e) {
      console.error("Could not fetch IP", e);
      return "0.0.0.0";
    }
  };

  const fetchData = async () => {
    try {
      const attRes = await fetch("/api/attendance", { headers: { Authorization: `Bearer ${token}` } });
      if (attRes.ok) setAttendance(await attRes.json());
      
      if (user?.role !== "employee") {
        const empRes = await fetch("/api/employees", { headers: { Authorization: `Bearer ${token}` } });
        if (empRes.ok) setEmployees(await empRes.json());
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchData();
  }, [token]);

  const handleClockAction = async (action: "in" | "out") => {
    try {
      const ip = await getClientIP();
      const now = new Date();
      const todayStr = now.toISOString().split("T")[0];
      
      const payload: any = {
        employeeId: user?.role === "employee" ? undefined : selectedEmp,
        date: todayStr,
        status: "Present",
        ip_address: ip
      };

      if (action === "in") {
        payload.clock_in = now.toISOString();
      } else {
        payload.clock_out = now.toISOString();
      }

      const res = await fetch("/api/attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast.success(`Successfully clocked ${action}!`);
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || err.error || `Error clocking ${action}`);
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error");
    }
  };

  if (loading) return <AppLayout title="Attendance" subtitle="Track daily attendance and work hours."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Attendance" subtitle="Track daily attendance and work hours.">
      <section className="section" style={{ position: "relative" }}>
        <h2>Daily Time Tracking</h2>
        <div style={{ backgroundColor: "rgba(255, 165, 0, 0.1)", color: "var(--amber)", padding: "12px", borderRadius: "8px", marginBottom: "20px", fontSize: "0.9rem" }}>
          <strong>Notice: IP Logging for Audit</strong><br />
          By clocking in, you consent to your IP address being recorded to verify on-site attendance and prevent time-theft.
        </div>
        
        <div className="form-grid" style={{ alignItems: "flex-end" }}>
          {user?.role !== "employee" && (
            <label>Select Employee to Clock In/Out (Admin/Manager Override)
              <select value={selectedEmp} onChange={e => setSelectedEmp(e.target.value)} required>
                <option value="" disabled>Select Employee</option>
                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name} ({emp.department})</option>)}
              </select>
            </label>
          )}
          
          <div className="form-actions" style={{ gap: "10px", display: "flex" }}>
            <button type="button" className="primary" onClick={() => handleClockAction("in")}>
              Clock In
            </button>
            <button type="button" className="secondary" onClick={() => handleClockAction("out")}>
              Clock Out
            </button>
          </div>
        </div>
      </section>

      <section className="section">
        <h2>Attendance Records</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {user?.role !== "employee" && <th>Employee ID</th>}
                <th>Date</th>
                <th>Clock In</th>
                <th>Clock Out</th>
                <th>IP Address</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {attendance.sort((a,b) => new Date(b.date).getTime() - new Date(a.date).getTime()).map(att => (
                <tr key={att.id}>
                  {user?.role !== "employee" && <td>{att.employeeId}</td>}
                  <td>{att.date}</td>
                  <td>{att.clock_in ? new Date(att.clock_in).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "-"}</td>
                  <td>{att.clock_out ? new Date(att.clock_out).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : "-"}</td>
                  <td>{att.ip_address || "-"}</td>
                  <td><span className={`status-badge ${att.status.toLowerCase()}`}>{att.status}</span></td>
                </tr>
              ))}
              {attendance.length === 0 && (
                <tr><td colSpan={user?.role !== "employee" ? 6 : 5} style={{ textAlign: "center" }}>No records found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}
