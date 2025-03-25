import React, { useState, useEffect } from "react";
import axios from "axios";

function App() {
  const [meetings, setMeetings] = useState([]);
  const [chatQuery, setChatQuery] = useState("");
  const [chatResponse, setChatResponse] = useState("");

  useEffect(() => {
    axios.get("http://localhost:5000/api/meetings")
      .then(response => setMeetings(response.data))
      .catch(err => console.error(err));
  }, []);

  const handleChatSubmit = () => {
    axios.post("http://localhost:5000/api/chatbot", {
      role: "Manager", // Change as needed: "HR", "Manager", or "Employee"
      query: chatQuery
    })
      .then(response => setChatResponse(response.data.response))
      .catch(err => console.error(err));
  };

  return (
    <div>
      <h1>Meetings</h1>
      <ul>
        {meetings.map(meeting => (
          <li key={meeting.meeting_id}>
            <strong>{meeting.title}</strong> - {meeting.description}
          </li>
        ))}
      </ul>
      <hr />
      <h2>Chatbot Query</h2>
      <input 
        type="text" 
        value={chatQuery} 
        onChange={e => setChatQuery(e.target.value)} 
        placeholder="Enter your query" 
      />
      <button onClick={handleChatSubmit}>Ask</button>
      {chatResponse && <p><strong>Response:</strong> {chatResponse}</p>}
    </div>
  );
}

export default App;
