"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";
import { useRouter } from "next/navigation";

export default function AuditPage() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Pagination
  const [skip, setSkip] = useState(0);
  const [limit] = useState(25);

  const fetchLogs = async () => {
    try {
      const res = await fetch(`/api/audit?skip=${skip}&limit=${limit}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user && user.role !== "admin") {
      router.push("/");
    }
    if (token) fetchLogs();
  }, [token, skip, user, router]);

  const formatDate = (dateStr: string) => {
    try {
      return new Intl.DateTimeFormat('en-US', { 
        dateStyle: 'medium', 
        timeStyle: 'medium' 
      }).format(new Date(dateStr));
    } catch (e) {
      return dateStr;
    }
  };

  if (loading) return <AppLayout title="Audit Logs" subtitle="Security and compliance records."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Audit Logs" subtitle="Security and compliance records.">
      <section className="section">
        <h2>System Activity</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Log ID</th>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Target ID</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id}>
                  <td><small className="text-zinc-500">#{log.id}</small></td>
                  <td>{formatDate(log.timestamp)}</td>
                  <td><strong>{log.username}</strong></td>
                  <td><span className="status-badge pending">{log.action}</span></td>
                  <td><small>{log.targetId}</small></td>
                  <td>{log.details}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: "center" }}>No audit logs found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
          <button className="secondary" disabled={skip === 0} onClick={() => setSkip(skip - limit)}>Previous</button>
          <span>Showing {skip + 1} to {skip + logs.length}</span>
          <button className="secondary" disabled={logs.length < limit} onClick={() => setSkip(skip + limit)}>Next</button>
        </div>
      </section>
    </AppLayout>
  );
}
