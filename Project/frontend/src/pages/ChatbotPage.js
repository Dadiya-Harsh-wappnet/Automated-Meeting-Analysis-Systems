// src/pages/ChatbotPage.js
import React, { useState } from "react";
import { Container, Typography, TextField, Button, Box } from "@mui/material";
import axios from "axios";

function ChatbotPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");

  const handleAsk = async () => {
    try {
      const res = await axios.post("http://localhost:5000/api/chatbot/", 
        { role: "Manager", query },
        { headers: { Authorization: `Bearer ${localStorage.getItem("token")}` } }
      );
      setResponse(res.data.response);
    } catch (error) {
      console.error("Chatbot query failed", error);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Chatbot</Typography>
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
