// src/pages/ChatbotPage.js
import React, { useState, useEffect, useRef } from "react";
import { Container, TextField, IconButton, Box, Typography, CircularProgress } from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import axios from "axios";

function ChatbotPage() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!query.trim()) return;
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");  // ✅ Fetch role directly

    if (!token) {
      alert("You must be logged in.");
      return;
    }
    if (!role) {
      alert("Role is missing. Please log in again.");
      return;
    }

    const userMessage = { sender: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);
    
    try {
      const res = await axios.post(
        "http://localhost:5000/api/chatbot/",
        { role, query },  // ✅ Ensure role is sent in the request
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages((prev) => [...prev, { sender: "bot", text: res.data.response }]);
    } catch (error) {
      setMessages((prev) => [...prev, { sender: "bot", text: "Error fetching response." }]);
    }
    setLoading(false);
  };

  return (
    <Container maxWidth="md" sx={{ display: "flex", flexDirection: "column", height: "80vh" }}>
      <Typography variant="h5" sx={{ my: 2, textAlign: "center" }}>AI Chat Assistant</Typography>
      
      <Box sx={{ flex: 1, overflowY: "auto", p: 2, border: "1px solid #ccc", borderRadius: 2 }}>
        {messages.map((msg, index) => (
          <Box key={index} sx={{
            display: "flex",
            justifyContent: msg.sender === "user" ? "flex-end" : "flex-start",
            mb: 1
          }}>
            <Box sx={{
              p: 2,
              borderRadius: "12px",
              backgroundColor: msg.sender === "user" ? "#0078ff" : "#e0e0e0",
              color: msg.sender === "user" ? "#fff" : "#000",
              maxWidth: "70%"
            }}>
              {msg.text}
            </Box>
          </Box>
        ))}
        {loading && (
          <Box sx={{ display: "flex", justifyContent: "center", my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={chatEndRef} />
      </Box>
      
      <Box sx={{ display: "flex", mt: 2 }}>
        <TextField
          fullWidth
          label="Type a message..."
          variant="outlined"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === "Enter" && handleSend()}
        />
        <IconButton color="primary" onClick={handleSend} sx={{ ml: 1 }}>
          <SendIcon />
        </IconButton>
      </Box>
    </Container>
  );
}

export default ChatbotPage;
