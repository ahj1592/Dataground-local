import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography, TextField, IconButton, Paper, InputAdornment, Tooltip, Chip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';

function ChatWindow({ messages, onSend, loading }) {
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [file, setFile] = useState(null);
  const fileInputRef = useRef();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if ((input.trim() === '' && !file) || sending || loading) return;
    
    // 중복 요청 방지
    if (sending) {
      console.log('Message already being sent, ignoring duplicate request');
      return;
    }
    
    setSending(true);
    await onSend(input, file);
    setInput('');
    setFile(null);
    setSending(false);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      // 중복 요청 방지
      if (sending || loading) {
        console.log('Message already being sent, ignoring Enter key');
        return;
      }
      handleSend(e);
    }
  };

  const handleClipClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  return (
    <Box display="flex" flexDirection="column" height="100%" bgcolor="#fff">
      <Box flex={1} p={2} overflow="auto">
        {messages.map((msg, idx) => (
          <Box key={msg.id || idx} display="flex" justifyContent={msg.sender === 'user' ? 'flex-end' : 'flex-start'} mb={1}>
            <Paper sx={{
              bgcolor: msg.sender === 'user' ? '#e3f2fd' : '#f5f5f5',
              color: '#111',
              px: 2, py: 1, maxWidth: '70%',
              wordBreak: 'break-word',
            }}>
              <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>{msg.content}</Typography>
            </Paper>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>
      <Box component="form" onSubmit={handleSend} display="flex" alignItems="center" p={2} borderTop="1px solid #eee" bgcolor="#fafafa">
        <Tooltip title="Attach file">
          <span>
            <IconButton onClick={handleClipClick} disabled={sending || loading} sx={{ mr: 1 }}>
              <AttachFileIcon />
            </IconButton>
          </span>
        </Tooltip>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
        <TextField
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message..."
          fullWidth
          multiline
          minRows={1}
          maxRows={4}
          disabled={sending || loading}
          sx={{ flex: 1 }}
        />
        <IconButton type="submit" color="primary" disabled={(input.trim() === '' && !file) || sending || loading} sx={{ ml: 1 }}>
          <SendIcon />
        </IconButton>
      </Box>
      {file && (
        <Box px={2} pb={1}>
          <Chip label={file.name} onDelete={handleRemoveFile} color="primary" variant="outlined" />
        </Box>
      )}
    </Box>
  );
}

export default ChatWindow;
