import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Link, Paper } from '@mui/material';
import { login } from '../api';
import { useNavigate } from 'react-router-dom';
import datagroundLogo from '../images/dataground_logo.png';

function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      const token = await login(email, password);
      onLogin(token);
    } catch (err) {
      setError('Invalid email or password');
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
      <Paper elevation={3} sx={{ p: 4, minWidth: 320 }}>
        <Box display="flex" justifyContent="center" mb={2}>
          <img src={datagroundLogo} alt="DataGround Logo" style={{ maxWidth: 300, height: 'auto' }} />
        </Box>
        <Typography variant="h5" mb={2}>Login</Typography>
        <form onSubmit={handleSubmit}>
          <TextField label="Email" type="email" fullWidth margin="normal" value={email} onChange={e => setEmail(e.target.value)} required />
          <TextField label="Password" type="password" fullWidth margin="normal" value={password} onChange={e => setPassword(e.target.value)} required />
          {error && <Typography color="error" variant="body2">{error}</Typography>}
          <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>Login</Button>
        </form>
        <Box mt={2} textAlign="center">
          <Link href="#" onClick={() => navigate('/signup')}>Don't have an account? Sign up</Link>
        </Box>
      </Paper>
    </Box>
  );
}

export default LoginPage;
