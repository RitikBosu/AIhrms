"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function CandidatesPage() {
  const { token, user } = useAuth();
  const [candidates, setCandidates] = useState<any[]>([]);
  const [jd, setJd] = useState("");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const fetchData = async () => {
    try {
      if (user?.role !== "hr" && user?.role !== "admin") {
        setLoading(false);
        return;
      }
      const [candRes, jdRes] = await Promise.all([
        fetch("/api/candidates", { headers: { Authorization: `Bearer ${token}` } }),
        fetch("/api/jd", { headers: { Authorization: `Bearer ${token}` } })
      ]);
      if (candRes.ok) setCandidates(await candRes.json());
      if (jdRes.ok) {
        const jdData = await jdRes.json();
        setJd(jdData.jdText);
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

  const handleUpdateJD = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch("/api/jd", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ jdText: jd })
      });
      if (res.ok) alert("Job description updated successfully.");
    } catch (err) {
      console.error(err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    setUploading(true);
    
    const files = Array.from(e.target.files);
    const resumes = await Promise.all(files.map(file => new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (ev) => resolve({ name: file.name, data: ev.target?.result });
      reader.readAsDataURL(file);
    })));

    try {
      const res = await fetch("/api/candidates", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ resumes })
      });
      if (res.ok) {
        alert("Resumes processed successfully.");
        fetchData();
      } else {
        const err = await res.json();
        alert(err.detail || "Error processing resumes.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  if (loading) return <AppLayout title="AI Screening" subtitle="AI-powered candidate resume parsing and scoring."><p>Loading...</p></AppLayout>;

  if (user?.role !== "hr" && user?.role !== "admin") {
    return <AppLayout title="AI Screening" subtitle="AI-powered candidate resume parsing and scoring."><p>You do not have access to this page.</p></AppLayout>;
  }

  return (
    <AppLayout title="AI Screening" subtitle="AI-powered candidate resume parsing and scoring.">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        <section className="section">
          <h2>Active Job Description</h2>
          <p style={{ marginBottom: "16px", color: "var(--zinc-400)", fontSize: "0.9rem" }}>
            The AI engine will evaluate all uploaded resumes against this job description.
          </p>
          <form onSubmit={handleUpdateJD}>
            <textarea
              style={{ width: "100%", height: "200px", background: "var(--input-bg)", color: "var(--foreground)", border: "1px solid var(--border)", padding: "12px", borderRadius: "8px", marginBottom: "16px" }}
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Paste the job description here..."
              required
            ></textarea>
            <button className="primary" style={{ width: "100%" }} type="submit">Save Target JD</button>
          </form>
        </section>

        <section className="section">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h2>Candidate Pool</h2>
            <div style={{ position: 'relative' }}>
              <input 
                type="file" 
                multiple 
                accept=".pdf" 
                onChange={handleFileUpload} 
                style={{ position: 'absolute', opacity: 0, top: 0, left: 0, right: 0, bottom: 0, cursor: 'pointer' }} 
              />
              <button className="primary" disabled={uploading}>
                {uploading ? "Analyzing Resumes..." : "Upload Resumes (.pdf)"}
              </button>
            </div>
          </div>
          
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Candidate</th>
                  <th>AI Match Score</th>
                  <th>Recommendation</th>
                  <th>Top Matched Skills</th>
                </tr>
              </thead>
              <tbody>
                {candidates.sort((a,b) => b.aiScore - a.aiScore).map((c) => (
                  <tr key={c.id}>
                    <td><strong>{c.name}</strong><br/><small className="text-zinc-500">{c.email}</small></td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ height: '8px', width: '60px', background: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${c.aiScore}%`, background: c.aiScore >= 80 ? 'var(--green)' : c.aiScore >= 50 ? 'var(--amber)' : 'var(--coral)' }}></div>
                        </div>
                        {c.aiScore}%
                      </div>
                    </td>
                    <td><span className={`status-badge ${c.aiDecision === "Shortlisted" ? "approved" : c.aiDecision === "Review manually" ? "pending" : "rejected"}`}>{c.aiDecision}</span></td>
                    <td><small>{c.matchedSkills?.join(", ") || "-"}</small></td>
                  </tr>
                ))}
                {candidates.length === 0 && (
                  <tr><td colSpan={4} style={{ textAlign: "center" }}>No candidates found. Upload resumes to begin screening.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
