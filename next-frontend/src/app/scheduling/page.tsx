"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState, Fragment } from "react";
import { useAuth } from "@/context/auth-context";
import { toast } from "@/components/toast";

export default function SchedulingPage() {
  const { token, user } = useAuth();
  
  const [activeTab, setActiveTab] = useState<"calendar" | "marketplace">("calendar");

  // Date Range (default: Monday to Sunday of current week)
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  
  // Data
  const [shifts, setShifts] = useState<any[]>([]);
  const [openShifts, setOpenShifts] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // AI Prompt State (For Managers)
  const [prompt, setPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [draftShifts, setDraftShifts] = useState<any[]>([]);
  const [violations, setViolations] = useState<any[]>([]);
  const [showDraft, setShowDraft] = useState(false);

  // Marketplace State
  const [newOpenShift, setNewOpenShift] = useState({ title: "", start_time: "", end_time: "" });
  const [bidsByShift, setBidsByShift] = useState<Record<number, any[]>>({});
  const [recommendationsByShift, setRecommendationsByShift] = useState<Record<number, any>>({});
  const [fetchingBids, setFetchingBids] = useState(false);

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
      
      // Fetch normal scheduled shifts
      const res = await fetch(`/api/shifts?start_date=${startDate}&end_date=${endDate}T23:59:59`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) setShifts(await res.json());

      // Fetch open shifts
      const openRes = await fetch(`/api/open-shifts`, { headers: { Authorization: `Bearer ${token}` } });
      if (openRes.ok) setOpenShifts(await openRes.json());

      // Fetch employees if manager
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

  // --- Marketplace Handlers ---

  const handleCreateOpenShift = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/open-shifts", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify(newOpenShift)
      });
      if (res.ok) {
        toast.success("Open shift created!");
        setNewOpenShift({ title: "", start_time: "", end_time: "" });
        fetchData();
      } else {
        toast.error("Failed to create open shift.");
      }
    } catch (e) {
      toast.error("Network error");
    }
  };

  const handleBid = async (shiftId: number) => {
    try {
      const res = await fetch(`/api/open-shifts/${shiftId}/bid`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Bid submitted successfully!");
      } else {
        const d = await res.json();
        toast.error(d.detail || "Failed to submit bid");
      }
    } catch (e) {
      toast.error("Network error");
    }
  };

  const loadBids = async (shiftId: number, shiftTitle: string, shiftStart: string, shiftEnd: string) => {
    setFetchingBids(true);
    try {
      const res = await fetch(`/api/open-shifts/${shiftId}/bids`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const bids = await res.json();
        setBidsByShift(prev => ({ ...prev, [shiftId]: bids }));
        
        // Also call AI to get recommendation if there are bidders
        if (bids.length > 0) {
          const bidders = bids.map((b: any) => ({
            id: b.employee.id,
            name: b.employee.name,
            department: b.employee.department,
            max_weekly_hours: b.employee.max_weekly_hours,
            performance_rating: b.employee.performance_rating,
            current_scheduled_hours: 30 // hardcoded for MVP, can be calculated
          }));

          const aiRes = await fetch(process.env.NEXT_PUBLIC_AI_API + "/api/bidding/recommend", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              shift_title: shiftTitle,
              shift_start: shiftStart,
              shift_end: shiftEnd,
              bidders: bidders
            })
          });

          if (aiRes.ok) {
            const recommendation = await aiRes.json();
            setRecommendationsByShift(prev => ({ ...prev, [shiftId]: recommendation }));
          }
        }
      }
    } catch (e) {
      toast.error("Error loading bids");
    } finally {
      setFetchingBids(false);
    }
  };

  const handleApproveBid = async (bidId: number) => {
    try {
      const res = await fetch(`/api/open-shifts/bids/${bidId}/approve`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        toast.success("Bid approved and shift assigned!");
        fetchData();
      } else {
        toast.error("Failed to approve bid");
      }
    } catch (e) {
      toast.error("Network error");
    }
  };

  const getEmpName = (id: number) => employees.find(e => e.id === id)?.name || `ID:${id}`;

  if (loading || !user) return <AppLayout title="Scheduling" subtitle="Shift Management"><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Scheduling" subtitle="Shift Management & Open Marketplace">
      
      {/* Tabs */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', borderBottom: '1px solid var(--border)', paddingBottom: '12px' }}>
        <button 
          className={activeTab === 'calendar' ? 'primary' : 'secondary'} 
          onClick={() => setActiveTab('calendar')}
        >
          Scheduled Shifts
        </button>
        <button 
          className={activeTab === 'marketplace' ? 'primary' : 'secondary'} 
          style={{ background: activeTab === 'marketplace' ? 'var(--purple)' : '', color: activeTab === 'marketplace' ? 'white' : '' }}
          onClick={() => setActiveTab('marketplace')}
        >
          Open Shift Marketplace
        </button>
      </div>

      {activeTab === 'calendar' && (
        <>
          {/* AI Generator for Managers */}
          {(user.role === "admin" || user.role === "manager" || user.role === "hr") && (
            <div style={{ display: "flex", gap: "20px", marginBottom: "20px" }}>
              <section className="section" style={{ flex: 1 }}>
                <h2>AI Auto-Rostering</h2>
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
                      rows={3}
                      required
                    />
                  </label>
                  <button type="submit" className="primary" disabled={aiLoading}>
                    {aiLoading ? "Generating AI Draft..." : "Generate Roster"}
                  </button>
                </form>
              </section>

              {showDraft && (
                <section className="section" style={{ flex: 1, border: "2px solid var(--cyan)" }}>
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
                  
                  <div className="table-wrap" style={{ maxHeight: "200px" }}>
                    <table>
                      <thead><tr><th>Employee</th><th>Shift</th><th>Date/Time</th></tr></thead>
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
                    <button className="secondary" onClick={() => setShowDraft(false)}>Discard</button>
                    <button className="primary" onClick={handlePublishDraft} disabled={violations.some(v => v.blocking)}>
                      Publish Roster
                    </button>
                  </div>
                </section>
              )}
            </div>
          )}

          <section className="section">
            <h2>{user.role === "employee" ? "My Shifts" : "Published Shifts"}</h2>
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
                      <td>{user.role === "employee" ? user.name : getEmpName(shift.employee_id)}</td>
                      <td>{shift.title} {shift.is_ai_generated && <span style={{fontSize: "10px", padding: "2px 4px", background: "var(--cyan-dim)", color: "var(--cyan)", borderRadius: "4px", marginLeft: "5px"}}>AI</span>}</td>
                      <td>{new Date(shift.start_time).toLocaleString()}</td>
                      <td>{new Date(shift.end_time).toLocaleString()}</td>
                      <td><span className={`badge ${shift.status === 'Scheduled' ? 'good' : 'warn'}`}>{shift.status}</span></td>
                    </tr>
                  ))}
                  {shifts.length === 0 && (
                    <tr><td colSpan={5} style={{textAlign: "center"}}>No scheduled shifts found.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}

      {activeTab === 'marketplace' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {(user.role === "admin" || user.role === "manager" || user.role === "hr") && (
            <section className="section">
              <h2>Post an Open Shift</h2>
              <form onSubmit={handleCreateOpenShift} style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: "16px", alignItems: "end" }}>
                <label>Shift Title
                  <input type="text" value={newOpenShift.title} onChange={e => setNewOpenShift({...newOpenShift, title: e.target.value})} required placeholder="e.g. Weekend Coverage" />
                </label>
                <label>Start Date & Time
                  <input type="datetime-local" value={newOpenShift.start_time} onChange={e => setNewOpenShift({...newOpenShift, start_time: e.target.value})} required />
                </label>
                <label>End Date & Time
                  <input type="datetime-local" value={newOpenShift.end_time} onChange={e => setNewOpenShift({...newOpenShift, end_time: e.target.value})} required />
                </label>
                <button type="submit" className="primary" style={{ background: "var(--purple)", color: "white" }}>Post Open Shift</button>
              </form>
            </section>
          )}

          <section className="section">
            <h2>Available Open Shifts</h2>
            {openShifts.length === 0 ? (
              <p style={{ color: "var(--ink-muted)" }}>There are no open shifts available at the moment.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Shift</th>
                      <th>Time</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {openShifts.map(shift => (
                      <Fragment key={shift.id}>
                        <tr>
                          <td><strong>{shift.title}</strong></td>
                          <td>
                            <span style={{ color: "var(--cyan)" }}>{new Date(shift.start_time).toLocaleString()}</span><br/>
                            to {new Date(shift.end_time).toLocaleString()}
                          </td>
                          <td><span className="badge warn">Unassigned</span></td>
                          <td>
                            {user.role === "employee" ? (
                              <button className="primary" style={{ padding: "6px 12px", fontSize: "12px", background: "var(--purple)" }} onClick={() => handleBid(shift.id)}>
                                Bid on Shift
                              </button>
                            ) : (
                              <button className="secondary" style={{ padding: "6px 12px", fontSize: "12px" }} onClick={() => loadBids(shift.id, shift.title, shift.start_time, shift.end_time)}>
                                View Bids
                              </button>
                            )}
                          </td>
                        </tr>
                        {/* Bids Dropdown for Managers */}
                        {bidsByShift[shift.id] && user.role !== "employee" && (
                          <tr>
                            <td colSpan={4} style={{ padding: "0 14px 14px", borderTop: "none" }}>
                              <div style={{ background: "rgba(0,0,0,0.2)", padding: "16px", borderRadius: "8px", border: "1px solid var(--border)" }}>
                                <h4 style={{ margin: "0 0 12px", color: "var(--purple)" }}>Employee Bids</h4>
                                {bidsByShift[shift.id].length === 0 ? (
                                  <p style={{ margin: 0, fontSize: "13px", color: "var(--ink-muted)" }}>No bids placed yet.</p>
                                ) : (
                                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                                    {bidsByShift[shift.id].map(bid => {
                                      const isRecommended = recommendationsByShift[shift.id]?.recommended_employee_id === bid.employee_id;
                                      return (
                                        <div key={bid.id} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: isRecommended ? "var(--purple-dim)" : "var(--bg-card)", padding: "12px", borderRadius: "6px", border: isRecommended ? "1px solid var(--purple)" : "1px solid transparent" }}>
                                          <div>
                                            <strong>{bid.employee.name}</strong> <span style={{ color: "var(--ink-muted)", fontSize: "12px" }}>({bid.employee.department})</span>
                                            {isRecommended && (
                                              <div style={{ marginTop: "6px", fontSize: "12px", color: "var(--ink)", display: "flex", alignItems: "center", gap: "6px" }}>
                                                <span style={{ background: "var(--purple)", color: "white", padding: "2px 6px", borderRadius: "4px", fontWeight: "bold" }}>✨ AI Pick</span>
                                                <span>{recommendationsByShift[shift.id]?.justification}</span>
                                              </div>
                                            )}
                                          </div>
                                          <div>
                                            {bid.status === "Pending" ? (
                                              <button className="primary" style={{ padding: "6px 16px", background: "var(--green)", color: "var(--bg-deep)" }} onClick={() => handleApproveBid(bid.id)}>
                                                Approve
                                              </button>
                                            ) : (
                                              <span className="badge">{bid.status}</span>
                                            )}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      )}

    </AppLayout>
  );
}
