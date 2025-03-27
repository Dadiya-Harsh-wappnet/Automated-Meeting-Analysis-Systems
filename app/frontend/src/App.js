import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import Login from './components/Login';
import Register from './components/Register';

function App() {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [showRegister, setShowRegister] = useState(false);

  if (!token) {
    return (
      <div style={{ margin: '20px' }}>
        { showRegister ? <Register /> : <Login setToken={setToken} setUser={setUser} /> }
        <button onClick={() => setShowRegister(!showRegister)}>
          { showRegister ? "Have an account? Login" : "Don't have an account? Register" }
        </button>
      </div>
    );
  }

  return (
    <div style={{ margin: '20px' }}>
      <h1>Welcome, {user.name}</h1>
      <ChatWindow user={user} token={token} />
    </div>
  );
}

export default App;
