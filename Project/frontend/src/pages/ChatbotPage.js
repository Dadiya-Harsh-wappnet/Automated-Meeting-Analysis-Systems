import React, { useState, useEffect, useRef } from "react";
import { Container, TextField, IconButton, Box, Typography, CircularProgress } from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function ChatbotPage() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem("session_id") || null);
  const chatEndRef = useRef(null);
  const navigate = useNavigate();

  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  const userId = localStorage.getItem("userId");

  useEffect(() => {
    if (!userId) {
      navigate("/login");
    } else {
      fetchChatHistory();
    }
  }, [userId, navigate]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const fetchChatHistory = async () => {
    if (!userId || !token) return;
    try {
      const res = await axios.get(`http://localhost:5000/api/chatbot/history/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(res.data.history || []);
      if (res.data.session_id) {
        setSessionId(res.data.session_id);
        localStorage.setItem("session_id", res.data.session_id);
      }
    } catch (error) {
      console.error("Error fetching chat history:", error);
    }
  };

  const handleSend = async () => {
    if (!query.trim()) return;
    if (!token || !role || !userId) {
      alert("Missing authentication details. Please log in again.");
      navigate("/login");
      return;
    }

    const userMessage = { sender: "user", text: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.post(
        "http://localhost:5000/api/chatbot/",
        { role, query, session_id: sessionId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const botMessage = { sender: "bot", text: res.data.response };
      setMessages((prev) => [...prev, botMessage]);
      if (res.data.session_id) {
        setSessionId(res.data.session_id);
        localStorage.setItem("session_id", res.data.session_id);
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      setMessages((prev) => [...prev, { sender: "bot", text: "Error fetching response." }]);
    }
    setLoading(false);
  };

  return (
    <Container maxWidth="md" sx={{ display: "flex", flexDirection: "column", height: "80vh" }}>
      <Typography variant="h5" sx={{ my: 2, textAlign: "center" }}>AI Chat Assistant</Typography>
      <Box sx={{ flex: 1, overflowY: "auto", p: 2, border: "1px solid #ccc", borderRadius: 2 }}>
        {messages.map((msg, index) => (
          <Box key={index} sx={{ display: "flex", justifyContent: msg.sender === "user" ? "flex-end" : "flex-start", mb: 1 }}>
            <Box sx={{ p: 2, borderRadius: "12px", backgroundColor: msg.sender === "user" ? "#0078ff" : "#e0e0e0", color: msg.sender === "user" ? "#fff" : "#000", maxWidth: "70%" }}>
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
        <TextField fullWidth label="Type a message..." variant="outlined" value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} />
        <IconButton color="primary" onClick={handleSend} sx={{ ml: 1 }}>
          <SendIcon />
        </IconButton>
      </Box>
    </Container>
  );
}

export default ChatbotPage;
