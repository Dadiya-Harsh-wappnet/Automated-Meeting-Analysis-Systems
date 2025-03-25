// src/pages/LoginPage.js
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  TextField,
  Typography
} from "@mui/material";
import axios from "axios";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post("http://localhost:5000/api/auth/login", {
        email,
        password
      });
      localStorage.setItem("token", res.data.token);
      navigate("/dashboard");
    } catch (error) {
      console.error("Login failed", error);
      alert("Invalid credentials");
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "linear-gradient(to right, #2980b9, #6dd5fa, #ffffff)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}
    >
      <Container maxWidth="sm">
        <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
          <CardContent sx={{ display: "flex", flexDirection: "column", alignItems: "center", p: 4 }}>
            <Box sx={{ mb: 3, textAlign: "center" }}>
              <img src="/logo192.png" alt="App Logo" style={{ width: 60, marginBottom: 8 }} />
              <Typography variant="h5" fontWeight="bold">Meeting Analysis System</Typography>
            </Box>
            <Box component="form" onSubmit={handleLogin} sx={{ width: "100%", mt: 2 }}>
              <TextField
                label="Email"
                variant="outlined"
                fullWidth
                sx={{ mb: 2 }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              <TextField
                label="Password"
                variant="outlined"
                type="password"
                fullWidth
                sx={{ mb: 2 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <Button variant="contained" type="submit" fullWidth>LOG IN</Button>
            </Box>
            <Typography variant="body2" sx={{ mt: 2 }}>
              Don’t have an account?{" "}
              <Link to="/signup" style={{ textDecoration: "none", color: "#1976d2" }}>Sign Up</Link>
            </Typography>
          </CardContent>
        </Card>
        <Typography variant="body2" align="center" sx={{ mt: 2, color: "#fff" }}>
          © {new Date().getFullYear()} Meeting Analysis System
        </Typography>
      </Container>
    </Box>
  );
}

export default LoginPage;
