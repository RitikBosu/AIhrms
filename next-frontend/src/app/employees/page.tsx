"use client";

import AppLayout from "@/components/AppLayout";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/auth-context";

export default function EmployeesPage() {
  const { token, user } = useAuth();
  const [employees, setEmployees] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Pagination & Filtering
  const [skip, setSkip] = useState(0);
  const [limit] = useState(10);
  const [includeDeleted, setIncludeDeleted] = useState(false);

  // Form State
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [department, setDepartment] = useState("");
  const [designation, setDesignation] = useState("");
  const [salary, setSalary] = useState("");
  const [joiningDate, setJoiningDate] = useState("");

  const fetchEmployees = async () => {
    try {
      const res = await fetch(`/api/employees?skip=${skip}&limit=${limit}&include_deleted=${includeDeleted}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEmployees(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchEmployees();
  }, [token, skip, includeDeleted]);

  const handleAddEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    try {
      const res = await fetch("/api/employees", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({
          name, email, department, designation, salary: Number(salary), joiningDate
        })
      });

      if (res.ok) {
        // Reset form
        setName(""); setEmail(""); setDepartment(""); setDesignation(""); setSalary(""); setJoiningDate("");
        fetchEmployees();
      } else {
        const err = await res.json();
        alert(err.detail || "Error adding employee");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to soft delete this employee?")) return;
    try {
      const res = await fetch(`/api/employees/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) fetchEmployees();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRestore = async (id: string) => {
    try {
      const res = await fetch(`/api/employees/${id}/restore`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) fetchEmployees();
    } catch (e) {
      console.error(e);
    }
  };

  const formatMoney = (val: number) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
  };

  if (loading) return <AppLayout title="Employees" subtitle="Manage employee records, departments, and compensation."><p>Loading...</p></AppLayout>;

  return (
    <AppLayout title="Employees" subtitle="Manage employee records, departments, and compensation.">
      {(user?.role === "admin" || user?.role === "hr") && (
        <section className="section">
          <h2>Add Employee</h2>
          <form onSubmit={handleAddEmployee} className="form-grid">
            <label>Name<input value={name} onChange={e => setName(e.target.value)} required /></label>
            <label>Email<input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
            <label>Department<input value={department} onChange={e => setDepartment(e.target.value)} required /></label>
            <label>Designation<input value={designation} onChange={e => setDesignation(e.target.value)} required /></label>
            <label>Salary<input type="number" min="0" value={salary} onChange={e => setSalary(e.target.value)} required /></label>
            <label>Joining Date<input type="date" value={joiningDate} onChange={e => setJoiningDate(e.target.value)} required /></label>
            <div className="form-actions full"><button type="submit" className="primary">Add Employee</button></div>
          </form>
        </section>
      )}

      <section className="section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h2>Employee List</h2>
          {user?.role === "admin" && (
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="checkbox" checked={includeDeleted} onChange={e => { setIncludeDeleted(e.target.checked); setSkip(0); }} />
              Show Soft Deleted
            </label>
          )}
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Department</th><th>Designation</th><th>Salary</th><th>Joined</th>
                {user?.role === "admin" && <th>Action</th>}
              </tr>
            </thead>
            <tbody>
              {employees.map(emp => (
                <tr key={emp.id}>
                  <td>{emp.name}</td>
                  <td>{emp.email}</td>
                  <td>{emp.department}</td>
                  <td>{emp.designation}</td>
                  <td>{formatMoney(emp.salary)}</td>
                  <td>{emp.joiningDate}</td>
                  {user?.role === "admin" && (
                    <td>
                      {emp.isDeleted ? (
                        <button className="primary" onClick={() => handleRestore(emp.id)}>Restore</button>
                      ) : (
                        <button className="danger" onClick={() => handleDelete(emp.id)}>Delete</button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
              {employees.length === 0 && (
                <tr><td colSpan={user?.role === "admin" ? 7 : 6} style={{ textAlign: "center" }}>No employees found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
          <button className="secondary" disabled={skip === 0} onClick={() => setSkip(skip - limit)}>Previous</button>
          <span>Showing {skip + 1} to {skip + employees.length}</span>
          <button className="secondary" disabled={employees.length < limit} onClick={() => setSkip(skip + limit)}>Next</button>
        </div>
      </section>
    </AppLayout>
  );
}
