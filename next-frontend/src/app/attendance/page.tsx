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
  const [status, setStatus] = useState("Present");

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

  const handleMarkAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/attendance", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          employeeId: user?.role === "employee" ? undefined : selectedEmp,
          date,
          status
        })
      });
      if (res.ok) {
        toast.success("Attendance marked successfully");
        fetchData();
      } else {
        const err = await res.json();
        toast.error(err.detail || err.error || "Error marking attendance");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error");
    }
  };

  if (loading) return <AppLayout title="Attendance" subtitle="Track daily attendance and work hours."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Attendance" subtitle="Track daily attendance and work hours.">
      <section className="section">
        <h2>Mark Attendance</h2>
        <form onSubmit={handleMarkAttendance} className="form-grid">
          {user?.role !== "employee" && (
            <label>Employee
              <select value={selectedEmp} onChange={e => setSelectedEmp(e.target.value)} required>
                <option value="" disabled>Select Employee</option>
                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name} ({emp.department})</option>)}
              </select>
            </label>
          )}
          <label>Date<input type="date" value={date} onChange={e => setDate(e.target.value)} required max={new Date().toISOString().split("T")[0]} /></label>
          <label>Status
            <select value={status} onChange={e => setStatus(e.target.value)}>
              <option value="Present">Present</option>
              <option value="Absent">Absent</option>
            </select>
          </label>
          <div className="form-actions"><button type="submit" className="primary">Mark Attendance</button></div>
        </form>
      </section>

      <section className="section">
        <h2>Attendance Records</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                {user?.role !== "employee" && <th>Employee ID</th>}
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {attendance.sort((a,b) => new Date(b.date).getTime() - new Date(a.date).getTime()).map(att => (
                <tr key={att.id}>
                  {user?.role !== "employee" && <td>{att.employeeId}</td>}
                  <td>{att.date}</td>
                  <td><span className={`status-badge ${att.status.toLowerCase()}`}>{att.status}</span></td>
                </tr>
              ))}
              {attendance.length === 0 && (
                <tr><td colSpan={user?.role !== "employee" ? 3 : 2} style={{ textAlign: "center" }}>No records found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}
