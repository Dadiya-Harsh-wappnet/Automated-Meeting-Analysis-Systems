// src/pages/SignupPage.js
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardContent,
  Container,
  TextField,
  Typography,
  MenuItem
} from "@mui/material";
import axios from "axios";

function SignupPage() {
  // Form fields
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  // If you want a fixed default role, setRole("Employee"). Otherwise, let user choose.
  const [role, setRole] = useState("Employee");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();

    // Optional: Confirm password check
    if (password !== confirmPassword) {
      alert("Passwords do not match. Please try again.");
      return;
    }

    try {
      // Send all fields to your Flask backend
      await axios.post("http://localhost:5000/api/auth/register", {
        first_name: firstName,
        last_name: lastName,
        role,
        email,
        password
      });

      // After successful registration, navigate to login page
      navigate("/");
    } catch (error) {
      console.error("Signup failed", error);
      // Gracefully handle error response from the backend
      const msg = error.response?.data?.msg || "An error occurred during signup.";
      alert("Signup error: " + msg);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "linear-gradient(to right, #8e2de2, #4a00e0, #ffffff)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}
    >
      <Container maxWidth="sm">
        <Card sx={{ borderRadius: 3, boxShadow: 3 }}>
          <CardContent
            sx={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              p: 4
            }}
          >
            <Box sx={{ mb: 3, textAlign: "center" }}>
              <Typography variant="h5" fontWeight="bold">
                Sign Up
              </Typography>
            </Box>

            <Box
              component="form"
              onSubmit={handleSignup}
              sx={{ width: "100%", mt: 2 }}
            >
              {/* First Name */}
              <TextField
                label="First Name"
                variant="outlined"
                fullWidth
                sx={{ mb: 2 }}
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />

              {/* Last Name */}
              <TextField
                label="Last Name"
                variant="outlined"
                fullWidth
                sx={{ mb: 2 }}
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />

              {/* Role (optional dropdown example) */}
              <TextField
                select
                label="Role"
                variant="outlined"
                fullWidth
                sx={{ mb: 2 }}
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <MenuItem value="Employee">Employee</MenuItem>
                <MenuItem value="Manager">Manager</MenuItem>
                <MenuItem value="HR">HR</MenuItem>
              </TextField>

              {/* Email */}
              <TextField
                label="Email"
                variant="outlined"
                fullWidth
                sx={{ mb: 2 }}
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />

              {/* Password */}
              <TextField
                label="Password"
                variant="outlined"
                type="password"
                fullWidth
                sx={{ mb: 2 }}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />

              {/* Confirm Password */}
              <TextField
                label="Confirm Password"
                variant="outlined"
                type="password"
                fullWidth
                sx={{ mb: 2 }}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />

              <Button variant="contained" type="submit" fullWidth>
                SIGN UP
              </Button>
            </Box>

            <Typography variant="body2" sx={{ mt: 2 }}>
              Already have an account?{" "}
              <Link to="/" style={{ textDecoration: "none", color: "#1976d2" }}>
                Log In
              </Link>
            </Typography>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}

export default SignupPage;
