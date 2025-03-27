import React, { useState } from 'react';
import axios from 'axios';

const ChatWindow = ({ user, token }) => {
  const [sessionId, setSessionId] = useState('');
  const [inputMessage, setInputMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;
    try {
      const response = await axios.post('http://localhost:5000/chat', {
        user_name: user.name,
        message: inputMessage,
        session_id: sessionId,
        role: user.role
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const { session_id, bot_response } = response.data;
      setSessionId(session_id);
      setChatHistory(prev => [
        ...prev,
        { sender: 'User', message: inputMessage },
        { sender: 'Bot', message: bot_response }
      ]);
      setInputMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '10px', maxWidth: '600px' }}>
      <div style={{ minHeight: '300px', marginBottom: '10px' }}>
        {chatHistory.map((chat, index) => (
          <div key={index} style={{ margin: '5px 0' }}>
            <strong>{chat.sender}:</strong> {chat.message}
          </div>
        ))}
      </div>
      <div>
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          style={{ width: '80%', padding: '8px' }}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage} style={{ padding: '8px 12px', marginLeft: '5px' }}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
