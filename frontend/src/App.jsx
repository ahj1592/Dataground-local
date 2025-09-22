import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import LoginPage from './components/LoginPage';
import SignupPage from './components/SignupPage';
import ChatPage from './components/ChatPage';
import ErrorBoundary from './components/ErrorBoundary';
import { getMe } from './api';

function App() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isValidating, setIsValidating] = useState(true);
  const navigate = useNavigate();

  // Validate token on app start
  useEffect(() => {
    const validateToken = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        try {
          await getMe(storedToken);
          setToken(storedToken);
        } catch (error) {
          console.log('Invalid token, clearing storage');
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setIsValidating(false);
    };

    validateToken();
  }, []);

  const handleLogin = (token) => {
    setToken(token);
    localStorage.setItem('token', token);
    navigate('/chat');
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
    navigate('/login');
  };

  // Show loading while validating token
  if (isValidating) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      Loading...
    </div>;
  }

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/chat" element={token ? <ChatPage token={token} onLogout={handleLogout} /> : <Navigate to="/login" />} />
        <Route path="*" element={<Navigate to={token ? "/chat" : "/login"} />} />
      </Routes>
    </ErrorBoundary>
  );
}

export default App;
