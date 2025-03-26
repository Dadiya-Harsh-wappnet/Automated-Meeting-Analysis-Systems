// src/pages/ChatbotPage.js
import React, { useState, useEffect } from "react";
import { Container, Typography, TextField, Button, Box } from "@mui/material";
import axios from "axios";

function ChatbotPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [role, setRole] = useState("");

  // ✅ Fetch role from localStorage after login
  useEffect(() => {
    const userRole = localStorage.getItem("role");
    if (userRole) {
      setRole(userRole);
    } else {
      alert("Role not found. Please log in again.");
    }
  }, []);

  const handleAsk = async () => {
  const token = localStorage.getItem("token");
  if (!token) {
    alert("You must be logged in.");
    return;
  }

  try {
    const res = await axios.post(
      "http://localhost:5000/api/chatbot/",
      JSON.stringify({ role, query }),  // ✅ Explicitly convert to JSON string
      {
        headers: {
          "Content-Type": "application/json",  // ✅ Ensure JSON is sent
          Authorization: `Bearer ${token}`
        }
      }
    );
    setResponse(res.data.response);
  } catch (error) {
    console.error("Chatbot query failed", error);
    if (error.response) {
      alert(`Error: ${error.response.data.msg || "Something went wrong"}`);
    }
  }
};

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Chatbot</Typography>
      <Typography variant="subtitle1" sx={{ mb: 2 }}>Your Role: {role}</Typography>
      <Box sx={{ display: "flex", gap: 2 }}>
        <TextField
          label="Enter your query"
          fullWidth
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <Button variant="contained" onClick={handleAsk}>Ask</Button>
      </Box>
      {response && (
        <Box sx={{ mt: 2, p: 2, border: "1px solid #ccc" }}>
          <Typography variant="subtitle1">Response:</Typography>
          <Typography variant="body1">{response}</Typography>
        </Box>
      )}
    </Container>
  );
}

export default ChatbotPage;
