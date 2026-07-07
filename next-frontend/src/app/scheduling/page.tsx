"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { toast } from "@/components/toast";

export default function SchedulingPage() {
  const { token, user } = useAuth();
  
  // Date Range (default: Monday to Sunday of current week)
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  
  // Data
  const [shifts, setShifts] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // AI Prompt State
  const [prompt, setPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [draftShifts, setDraftShifts] = useState<any[]>([]);
  const [violations, setViolations] = useState<any[]>([]);
  const [showDraft, setShowDraft] = useState(false);

  useEffect(() => {
    // Set default dates to current week (Monday-Sunday)
    const curr = new Date();
    const first = curr.getDate() - curr.getDay() + 1; // Monday
    const start = new Date(curr.setDate(first));
    const end = new Date(curr.setDate(start.getDate() + 6));
    setStartDate(start.toISOString().split("T")[0]);
    setEndDate(end.toISOString().split("T")[0]);
  }, []);

  const fetchData = async () => {
    try {
      if (!startDate || !endDate) return;
      const res = await fetch(`/api/shifts?start_date=${startDate}&end_date=${endDate}T23:59:59`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setShifts(await res.json());

      const empRes = await fetch("/api/employees", { headers: { Authorization: `Bearer ${token}` } });
      if (empRes.ok) setEmployees(await empRes.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token && startDate && endDate) fetchData();
  }, [token, startDate, endDate]);

  const handleGenerateRoster = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt) return;
    setAiLoading(true);
    setViolations([]);
    setShowDraft(false);

    try {
      const res = await fetch("/api/generate-roster", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ prompt, start_date: startDate, end_date: endDate })
      });
      const data = await res.json();
      
      if (res.ok) {
        setDraftShifts(data.approved_shifts);
        setViolations(data.violations);
        setShowDraft(true);
        if (data.violations.some((v: any) => v.blocking)) {
          toast.error("Draft contains blocking violations.");
        } else {
          toast.success("AI generated a clean draft roster!");
        }
      } else {
        toast.error(data.detail || "Failed to generate AI roster");
      }
    } catch (e) {
      console.error(e);
      toast.error("Network error talking to AI service");
    } finally {
      setAiLoading(false);
    }
  };

  const handlePublishDraft = async () => {
    const hasBlocking = violations.some(v => v.blocking);
    if (hasBlocking) {
      toast.error("Cannot publish schedule with blocking violations.");
      return;
    }
    
    try {
      // Save each shift individually (or create a bulk endpoint later)
      for (const shift of draftShifts) {
        await fetch("/api/shifts", {
          method: "POST",
          headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({
            employee_id: shift.employee_id,
            title: shift.title,
            start_time: shift.start_time,
            end_time: shift.end_time,
            is_ai_generated: true
          })
        });
      }
      toast.success("Roster published successfully!");
      setShowDraft(false);
      setDraftShifts([]);
      setViolations([]);
      setPrompt("");
      fetchData();
    } catch (e) {
      toast.error("Failed to publish schedule");
    }
  };

  const getEmpName = (id: number) => employees.find(e => e.id === id)?.name || `ID:${id}`;

  if (loading) return <AppLayout title="Scheduling" subtitle="AI Auto-Rostering & Shift Management"><p>Loading...</p></AppLayout>;

  // Only managers/admins should access this page based on AppLayout rules
  return (
    <AppLayout title="Scheduling" subtitle="AI Auto-Rostering & Shift Management">
      <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
        {/* Left Col: AI Prompt */}
        <section className="section" style={{ flex: 1 }}>
          <h2>Zira-Killer AI Scheduling</h2>
          <p style={{ color: "var(--light-text)", fontSize: "0.9rem", marginBottom: "15px" }}>
            The AI engine automatically enforces maximum weekly hours, prevents double-booking, and avoids scheduling employees on approved leave.
          </p>
          <form onSubmit={handleGenerateRoster} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <div style={{ display: "flex", gap: "10px" }}>
              <label style={{ flex: 1 }}>Start Date
                <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required />
              </label>
              <label style={{ flex: 1 }}>End Date
                <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required />
              </label>
            </div>
            <label>Natural Language Command
              <textarea 
                value={prompt} 
                onChange={e => setPrompt(e.target.value)} 
                placeholder="e.g. 'Schedule 3 developers for the morning shift this weekend.'"
                rows={4}
                required
              />
            </label>
            <button type="submit" className="primary" disabled={aiLoading}>
              {aiLoading ? "Generating AI Draft..." : "Generate Roster"}
            </button>
          </form>
        </section>

        {/* Right Col: Review Draft */}
        {showDraft && (
          <section className="section" style={{ flex: 1, border: "2px solid var(--primary)" }}>
            <h2>Review AI Draft</h2>
            {violations.length > 0 && (
              <div style={{ padding: "10px", background: "rgba(255,100,100,0.1)", color: "var(--coral)", borderRadius: "4px", marginBottom: "10px" }}>
                <strong>Compliance Violations Found:</strong>
                <ul style={{ margin: "5px 0 0 20px" }}>
                  {violations.map((v, idx) => (
                    <li key={idx}>
                      [{v.blocking ? "BLOCKING" : "WARN"}] {getEmpName(v.employee_id)} - {v.type}: {v.detail}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="table-wrap" style={{ maxHeight: "300px" }}>
              <table>
                <thead>
                  <tr>
                    <th>Employee</th>
                    <th>Shift</th>
                    <th>Date/Time</th>
                  </tr>
                </thead>
                <tbody>
                  {draftShifts.map((s, idx) => {
                    const isViolating = violations.some(v => v.shift_index === idx);
                    return (
                      <tr key={idx} style={{ background: isViolating ? "rgba(255,100,100,0.1)" : "transparent" }}>
                        <td>{getEmpName(s.employee_id)}</td>
                        <td>{s.title}</td>
                        <td>{new Date(s.start_time).toLocaleString()} - {new Date(s.end_time).toLocaleTimeString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            
            <div style={{ marginTop: "15px", display: "flex", gap: "10px", justifyContent: "flex-end" }}>
              <button className="secondary" onClick={() => setShowDraft(false)}>Discard Draft</button>
              <button 
                className="primary" 
                onClick={handlePublishDraft}
                disabled={violations.some(v => v.blocking)}
              >
                Publish Roster
              </button>
            </div>
          </section>
        )}
      </div>

      {/* Main Calendar View (Published Shifts) */}
      <section className="section">
        <h2>Published Shifts ({startDate} to {endDate})</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Shift</th>
                <th>Start Time</th>
                <th>End Time</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {shifts.sort((a,b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()).map(shift => (
                <tr key={shift.id}>
                  <td>{getEmpName(shift.employee_id)}</td>
                  <td>{shift.title} {shift.is_ai_generated && <span style={{fontSize: "10px", padding: "2px 4px", background: "var(--primary)", borderRadius: "4px", marginLeft: "5px"}}>AI</span>}</td>
                  <td>{new Date(shift.start_time).toLocaleString()}</td>
                  <td>{new Date(shift.end_time).toLocaleString()}</td>
                  <td><span className={`status-badge ${shift.status.toLowerCase()}`}>{shift.status}</span></td>
                </tr>
              ))}
              {shifts.length === 0 && (
                <tr><td colSpan={5} style={{textAlign: "center"}}>No published shifts in this range.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppLayout>
  );
}
