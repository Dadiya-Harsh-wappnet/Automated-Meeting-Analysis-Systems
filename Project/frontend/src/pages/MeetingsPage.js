// src/pages/MeetingsPage.js
import React, { useState, useEffect } from "react";
import { Container, Typography, Box, Button, TextField } from "@mui/material";
import axios from "axios";

function MeetingsPage() {
  const [meetings, setMeetings] = useState([]);
  const [title, setTitle] = useState("");

  useEffect(() => {
    axios.get("http://localhost:5000/api/meetings/", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    })
      .then(res => setMeetings(res.data))
      .catch(err => console.error(err));
  }, []);

  const handleCreateMeeting = async () => {
    const newMeeting = {
      title,
      description: "New meeting",
      google_meet_link: "https://meet.google.com/fake-link",
      scheduled_start: new Date().toISOString(),
      scheduled_end: new Date(Date.now() + 3600000).toISOString() // 1 hour later
    };
    try {
      const res = await axios.post("http://localhost:5000/api/meetings/create", newMeeting, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
      });
      setMeetings([...meetings, { ...newMeeting, id: res.data.meeting_id }]);
      setTitle("");
    } catch (error) {
      console.error("Meeting creation failed", error);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h5" sx={{ mb: 2 }}>Meetings</Typography>
      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <TextField
          label="Meeting Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <Button variant="contained" onClick={handleCreateMeeting}>
          Create Meeting
        </Button>
      </Box>
      <Box>
        {meetings.map((m) => (
          <Box key={m.id} sx={{ mb: 2, p: 2, border: "1px solid #ccc" }}>
            <Typography variant="h6">{m.title}</Typography>
            <Typography variant="body2">{m.description}</Typography>
            {m.google_meet_link && (
              <Button variant="outlined" sx={{ mt: 1 }} href={m.google_meet_link} target="_blank">
                Join Google Meet
              </Button>
            )}
          </Box>
        ))}
      </Box>
    </Container>
  );
}

export default MeetingsPage;
