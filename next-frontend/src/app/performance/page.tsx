"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { toast } from "@/components/toast";

export default function PerformancePage() {
  const { token, user } = useAuth();
  const [reviews, setReviews] = useState<any[]>([]);
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Form
  const [selectedEmp, setSelectedEmp] = useState("");
  const [rating, setRating] = useState(5);
  const [feedback, setFeedback] = useState("");

  const fetchData = async () => {
    try {
      const revRes = await fetch("/api/performance", { headers: { Authorization: `Bearer ${token}` } });
      if (revRes.ok) setReviews(await revRes.json());

      if (user?.role === "admin" || user?.role === "manager") {
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/performance", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ employeeId: selectedEmp, rating, feedback })
      });
      if (res.ok) {
        setSelectedEmp(""); setRating(5); setFeedback("");
        fetchData();
        toast.success("Performance review submitted successfully.");
      } else {
        const err = await res.json();
        toast.error(err.detail?.[0]?.msg || err.detail || "Error submitting review");
      }
    } catch (err) {
      console.error(err);
      toast.error("Network error");
    }
  };

  if (loading) return <AppLayout title="Performance Reviews" subtitle="Track and evaluate employee goals and achievements."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Performance Reviews" subtitle="Track and evaluate employee goals and achievements.">
      {(user?.role === "admin" || user?.role === "manager") && (
        <section className="section">
          <h2>Submit Review</h2>
          <form onSubmit={handleSubmit} className="form-grid">
            <label>Employee
              <select value={selectedEmp} onChange={e => setSelectedEmp(e.target.value)} required>
                <option value="" disabled>Select Employee</option>
                {employees.map(emp => <option key={emp.id} value={emp.id}>{emp.name}</option>)}
              </select>
            </label>
            <label>Rating (1-5)
              <input type="number" min="1" max="5" value={rating} onChange={e => setRating(Number(e.target.value))} required />
            </label>
            <label className="full">Feedback
              <textarea value={feedback} onChange={e => setFeedback(e.target.value)} rows={3} required placeholder="Detailed manager feedback..."></textarea>
            </label>
            <div className="form-actions full"><button className="primary" type="submit">Submit Review (Generates AI Summary)</button></div>
          </form>
        </section>
      )}

      <div style={{ display: 'grid', gap: '24px' }}>
        {reviews.map(rev => {
          const emp = employees.find(e => e.id === rev.employeeId) || { name: rev.employeeId };
          return (
            <div key={rev.id} className="perf-card" style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: "12px", padding: "24px" }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{user?.role === "employee" ? "Your Review" : emp.name}</h3>
                  <div style={{ color: "var(--zinc-400)", fontSize: '0.9rem', marginTop: '4px' }}>Rating: {rev.rating}/5</div>
                </div>
                <div style={{ display: 'flex', gap: '4px' }}>
                  {[1,2,3,4,5].map(star => (
                    <span key={star} style={{ color: star <= rev.rating ? "var(--cyan)" : "var(--border)" }}>★</span>
                  ))}
                </div>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <strong style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: "var(--zinc-400)" }}>Manager Feedback</strong>
                <p style={{ margin: 0, lineHeight: 1.5 }}>"{rev.feedback}"</p>
              </div>
              <div style={{ background: "rgba(0, 212, 255, 0.05)", borderLeft: "3px solid var(--cyan)", padding: "16px", borderRadius: "0 8px 8px 0" }}>
                <strong style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem', color: "var(--cyan)" }}>✨ AI Executive Summary</strong>
                <p style={{ margin: 0, lineHeight: 1.5 }}>{rev.aiSummary}</p>
              </div>
            </div>
          );
        })}
        {reviews.length === 0 && (
          <div style={{ textAlign: "center", padding: "40px", background: "var(--card-bg)", borderRadius: "12px", border: "1px solid var(--border)" }}>
            No performance reviews found.
          </div>
        )}
      </div>
    </AppLayout>
  );
}
