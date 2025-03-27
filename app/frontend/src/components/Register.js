import React, { useState } from 'react';
import axios from 'axios';

const Register = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('');
  const [department, setDepartment] = useState('');
  const [message, setMessage] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/auth/register', {
        first_name: firstName,
        last_name: lastName,
        name,
        email,
        password,
        role,
        department
      });
      setMessage("Registration successful! Please login.");
    } catch (err) {
      setMessage("Registration failed: " + err.response.data.msg);
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <form onSubmit={handleRegister}>
        <input type="text" placeholder="First Name" value={firstName} onChange={(e)=>setFirstName(e.target.value)} required />
        <input type="text" placeholder="Last Name" value={lastName} onChange={(e)=>setLastName(e.target.value)} required />
        <input type="text" placeholder="Name" value={name} onChange={(e)=>setName(e.target.value)} required />
        <input type="email" placeholder="Email" value={email} onChange={(e)=>setEmail(e.target.value)} required />
        <input type="password" placeholder="Password" value={password} onChange={(e)=>setPassword(e.target.value)} required />
        <input type="text" placeholder="Role (employee, manager, hr)" value={role} onChange={(e)=>setRole(e.target.value)} required />
        <input type="text" placeholder="Department (optional)" value={department} onChange={(e)=>setDepartment(e.target.value)} />
        <button type="submit">Register</button>
      </form>
      { message && <p>{message}</p> }
    </div>
  );
};

export default Register;
