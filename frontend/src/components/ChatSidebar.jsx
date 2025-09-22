import React from 'react';
import { List, ListItem, ListItemButton, ListItemText, Button, Box, Typography } from '@mui/material';

function formatDateTime(dt) {
  const d = new Date(dt);
  return d.toLocaleString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function ChatSidebar({ chats, selectedChatId, onSelect, onCreate }) {
  return (
    <Box width={260} bgcolor="#f0f0f0" height="100vh" display="flex" flexDirection="column">
      <Box p={2} borderBottom="1px solid #ddd">
        <Typography variant="h6">Chats</Typography>
        <Button variant="contained" color="primary" fullWidth sx={{ mt: 1 }} onClick={() => onCreate()}>
          New Chat
        </Button>
      </Box>
      <List sx={{ flex: 1, overflowY: 'auto' }}>
        {chats.map(chat => (
          <ListItem key={chat.id} disablePadding>
            <ListItemButton selected={chat.id === selectedChatId} onClick={() => onSelect(chat.id)} alignItems="flex-start">
              <ListItemText
                primary={<Typography fontWeight={600} fontSize={16} noWrap>{chat.title}</Typography>}
                secondary={<Typography fontSize={12} color="text.secondary">{formatDateTime(chat.created_at)}</Typography>}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );
}

export default ChatSidebar;
