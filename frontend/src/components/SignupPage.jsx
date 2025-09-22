import React, { useState } from 'react';
import { TextField, Button, Box, Typography, Link, Paper } from '@mui/material';
import { signup } from '../api';
import { useNavigate } from 'react-router-dom';

function SignupPage() {
  const [userName, setUserName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    try {
      await signup(userName, email, password, confirmPassword);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 1000);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Signup failed');
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" bgcolor="#f5f5f5">
      <Paper elevation={3} sx={{ p: 4, minWidth: 320 }}>
        <Typography variant="h5" mb={2}>Sign Up</Typography>
        <form onSubmit={handleSubmit}>
          <TextField label="User Name" fullWidth margin="normal" value={userName} onChange={e => setUserName(e.target.value)} required />
          <TextField label="Email" type="email" fullWidth margin="normal" value={email} onChange={e => setEmail(e.target.value)} required />
          <TextField label="Password" type="password" fullWidth margin="normal" value={password} onChange={e => setPassword(e.target.value)} required />
          <TextField label="Confirm Password" type="password" fullWidth margin="normal" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
          {error && <Typography color="error" variant="body2">{error}</Typography>}
          {success && <Typography color="primary" variant="body2">Signup successful! Redirecting...</Typography>}
          <Button type="submit" variant="contained" color="primary" fullWidth sx={{ mt: 2 }}>Sign Up</Button>
        </form>
        <Box mt={2} textAlign="center">
          <Link href="#" onClick={() => navigate('/login')}>Already have an account? Login</Link>
        </Box>
      </Paper>
    </Box>
  );
}

export default SignupPage;
