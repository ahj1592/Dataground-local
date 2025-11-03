import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography, TextField, IconButton, Paper, InputAdornment, Tooltip, Chip } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ReactMarkdown from 'react-markdown';
import StreamingText from './StreamingText';

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
        {messages.map((msg, idx) => {
          const isLoading = msg.content === "...";
          const isAssistant = msg.sender === 'assistant' || msg.sender === 'ai';
          const isLatestAssistant = isAssistant && idx === messages.length - 1 && !isLoading;
          
          return (
            <Box key={msg.id || idx} display="flex" justifyContent={msg.sender === 'user' ? 'flex-end' : 'flex-start'} mb={1}>
              <Paper sx={{
                bgcolor: msg.sender === 'user' ? '#e3f2fd' : '#f5f5f5',
                color: '#111',
                px: 2, py: 1, maxWidth: '70%',
                wordBreak: 'break-word',
              }}>
                {isLoading ? (
                  <Box display="flex" alignItems="center" gap={0.5}>
                    <Typography variant="body1" sx={{ 
                      animation: 'pulse 1.5s ease-in-out infinite',
                      '@keyframes pulse': {
                        '0%, 100%': { opacity: 0.5 },
                        '50%': { opacity: 1 },
                      }
                    }}>
                      ...
                    </Typography>
                  </Box>
                ) : isLatestAssistant ? (
                  // Show streaming effect for the latest assistant message
                  <StreamingText 
                    text={msg.content} 
                    speed={2.5}
                    startImmediately={true}
                    messageId={msg.id}
                  />
                ) : (
                  // Show full text for older messages with markdown rendering
                  <Box sx={{ 
                    '& p': { margin: 0, marginBottom: '0.5em' },
                    '& p:last-child': { marginBottom: 0 },
                    '& h1, & h2, & h3, & h4, & h5, & h6': { marginTop: '0.5em', marginBottom: '0.5em' },
                    '& h1:first-child, & h2:first-child, & h3:first-child': { marginTop: 0 },
                    '& ul, & ol': { marginTop: '0.5em', marginBottom: '0.5em', paddingLeft: '1.5em' },
                    '& code': { 
                      backgroundColor: 'rgba(0, 0, 0, 0.05)', 
                      padding: '0.2em 0.4em', 
                      borderRadius: '3px',
                      fontSize: '0.9em'
                    },
                    '& pre': {
                      backgroundColor: 'rgba(0, 0, 0, 0.05)',
                      padding: '0.5em',
                      borderRadius: '4px',
                      overflow: 'auto',
                      marginTop: '0.5em',
                      marginBottom: '0.5em'
                    },
                    '& pre code': {
                      backgroundColor: 'transparent',
                      padding: 0
                    },
                    '& blockquote': {
                      borderLeft: '3px solid #ddd',
                      paddingLeft: '1em',
                      marginLeft: 0,
                      color: '#666',
                      fontStyle: 'italic'
                    },
                    '& a': {
                      color: '#1976d2',
                      textDecoration: 'none'
                    },
                    '& a:hover': {
                      textDecoration: 'underline'
                    }
                  }}>
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </Box>
                )}
              </Paper>
            </Box>
          );
        })}
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
