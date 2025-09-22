import React, { useEffect, useState, useCallback } from 'react';
import { Box, AppBar, Toolbar, Typography, Button, CircularProgress } from '@mui/material';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import ChatSidebar from './ChatSidebar';
import ChatWindow from './ChatWindow';
import FileUpload from './FileUpload';
import MapSidebar from './MapSidebar';
import MapDisplay from './MapDisplay';
import UrbanAreaCharts from './UrbanAreaCharts';
import UrbanAreaComprehensiveCharts from './UrbanAreaComprehensiveCharts';
import InfrastructureExposure from './InfrastructureExposure';
import TopicModeling from './TopicModeling';
import { getChats, createChat, getMessages, sendMessage, uploadFile, getMe, updateChatTitle, createChatWithFirstMessage, generateAIResponse } from '../api';

function ChatPage({ token, onLogout }) {
  const [chats, setChats] = useState([]);
  const [selectedChatId, setSelectedChatId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loadingChats, setLoadingChats] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [aiThinking, setAiThinking] = useState(false);
  const [user, setUser] = useState(null);
  const [isComposingNewChat, setIsComposingNewChat] = useState(false);
  const [justCreatedChatId, setJustCreatedChatId] = useState(null);
  const [params, setParams] = useState(null);
  const [isSending, setIsSending] = useState(false);
  
  const handleAnalyze = (selectedParams) => {
    console.log('🔍 [ChatPage] handleAnalyze called with:', selectedParams);
    console.log('🔍 [ChatPage] Setting params to:', selectedParams);
    setParams(selectedParams);
    console.log('🔍 [ChatPage] Params state updated');
  };

  useEffect(() => {
    const fetchChats = async () => {
      setLoadingChats(true);
      const data = await getChats(token);
      setChats(data);
      // Do NOT auto-select any chat after login
      setLoadingChats(false);
    };
    const fetchUser = async () => {
      try {
        const userData = await getMe(token);
        setUser(userData);
      } catch {}
    };
    fetchChats();
    fetchUser();
  }, [token]);

  useEffect(() => {
    if (!selectedChatId) return;
    
    const fetchMessages = async () => {
      console.log('🔍 [fetchMessages] Fetching messages for chat:', selectedChatId);
      setLoadingMessages(true);
      try {
        const data = await getMessages(selectedChatId, token);
        setMessages(data);
      } finally {
        setLoadingMessages(false);
      }
    };
    
    fetchMessages();
  }, [selectedChatId, token]);

  const handleSelectChat = (chatId) => {
    setSelectedChatId(chatId);
  };

  const handleCreateChat = async () => {
    if (isComposingNewChat) {
      console.log('⚠️ [handleCreateChat] Chat creation already in progress, ignoring duplicate request');
      return;
    }
    
    console.log('🚀 [handleCreateChat] Starting new chat creation');
    setIsComposingNewChat(true);
    setSelectedChatId(null);
    setMessages([]);
    
    try {
      // Create empty chat without any message
      const title = 'New Chat';
      console.log('🚀 [handleCreateChat] Creating chat with title:', title);
      console.log('🚀 [handleCreateChat] Using token:', token ? 'present' : 'missing');
      const response = await createChat(title, token);
      console.log('🔍 [handleCreateChat] Full response:', response);
      const chat = response.chat || response; // Handle different response formats
      console.log('✅ [handleCreateChat] Chat created:', chat.id);
      setChats(prev => [chat, ...prev]);
      setSelectedChatId(chat.id);
      setIsComposingNewChat(false);
      
      // Don't generate AI greeting here - let user send first message
      console.log('✅ [handleCreateChat] Chat created, waiting for user message');
    } catch (e) {
      console.error('❌ [handleCreateChat] Error creating chat:', e);
      console.error('❌ [handleCreateChat] Error details:', e.response?.data);
      setIsComposingNewChat(false);
    }
  };

  // Helper to truncate title
  const truncateTitle = (title, maxLen = 30) => {
    return title.length > maxLen ? title.slice(0, maxLen) + '...' : title;
  };

  // Simplified message sending logic
  const handleSendMessage = async (content, file) => {
    if (isSending) {
      console.log('⚠️ [handleSendMessage] Message already being sent, ignoring duplicate request');
      return;
    }
    
    console.log('🚀 [handleSendMessage] Starting message send:', content);
    setIsSending(true);
    
    if (!selectedChatId) {
      console.log('No selected chat, ignoring message');
      setIsSending(false);
      return;
    }
    
    // Handle file upload if present
    let fileInfo = null;
    if (file) {
      try {
        fileInfo = await uploadFile(file, token);
      } catch (e) {
        fileInfo = { filename: file.name, error: true };
      }
    }
    
    // Add user message to UI
    const userMsg = {
      id: `user-${Date.now()}`,
      sender: 'user',
      content: content || (fileInfo ? `[File: ${fileInfo.filename}]` : ''),
      created_at: new Date().toISOString(),
      file: fileInfo,
    };
    setMessages(prev => [...prev, userMsg]);
    
    // Send message and get AI response
    setAiThinking(true);
    try {
      const aiMsg = await sendMessage(selectedChatId, content, token);
      console.log('🔍 [ChatPage] Full AI Message received:', aiMsg);
      console.log('🔍 [ChatPage] AI Message keys:', Object.keys(aiMsg));
      console.log('🔍 [ChatPage] dashboard_updates in AI message:', aiMsg.dashboard_updates);
      setMessages(prev => [...prev, aiMsg]);
      
      // Handle ADK response
      if (aiMsg.redirect_to_manual && aiMsg.manual_analysis_params) {
        console.log('✅ ADK parameters collected, redirecting to manual analysis:', aiMsg.manual_analysis_params);
        
        // Convert ADK parameters to manual analysis format
        const taskMapping = {
          'sea_level_rise': 'slr-risk',
          'urban_analysis': 'urban-area-comprehensive',
          'infrastructure_analysis': 'infrastructure-exposure',
          'topic_modeling': 'topic-modeling'
        };
        
        const manualParams = {
          task: taskMapping[aiMsg.manual_analysis_params.task] || aiMsg.manual_analysis_params.task,
          country: aiMsg.manual_analysis_params.country,
          city: aiMsg.manual_analysis_params.city,
          year1: aiMsg.manual_analysis_params.year1,
          mapOption: 'OpenStreetMap'
        };
        
        // urban_analysis의 경우 year2 추가
        if (aiMsg.manual_analysis_params.task === 'urban_analysis') {
          manualParams.year2 = aiMsg.manual_analysis_params.year2;
        }
        
        // threshold가 필요한 분석 유형에만 추가
        if (aiMsg.manual_analysis_params.task === 'sea_level_rise' || 
            aiMsg.manual_analysis_params.task === 'infrastructure_analysis' ||
            aiMsg.manual_analysis_params.task === 'urban_analysis') {
          manualParams.threshold = aiMsg.manual_analysis_params.threshold;
        }
        
        console.log('🔍 [ChatPage] Calling handleAnalyze with manual params:', manualParams);
        handleAnalyze(manualParams);
        console.log('🔍 [ChatPage] Manual analysis params set');
      }
      // Handle dashboard updates if present
      else if (aiMsg.dashboard_updates && aiMsg.dashboard_updates.length > 0) {
        console.log('✅ Dashboard updates received:', aiMsg.dashboard_updates);
        
        // Check if it's an auto-execute analysis
        const autoExecuteUpdate = aiMsg.dashboard_updates.find(update => update.type === 'analysis_triggered' && update.auto_execute);
        if (autoExecuteUpdate) {
          console.log('🚀 Auto-executing analysis:', autoExecuteUpdate);
          
          // Convert ADK parameters to manual analysis format
          const taskMapping = {
            'sea_level_rise': 'slr-risk',
            'urban_analysis': 'urban-area-comprehensive',
            'infrastructure_analysis': 'infrastructure-exposure',
            'topic_modeling': 'topic-modeling'
          };
          
          // 각 분석 유형별로 필요한 파라미터만 포함
          const manualParams = {
            task: taskMapping[autoExecuteUpdate.analysis_type] || autoExecuteUpdate.analysis_type,
            country: autoExecuteUpdate.params.country,
            city: autoExecuteUpdate.params.city,
            year1: autoExecuteUpdate.params.year1,
            mapOption: 'OpenStreetMap'
          };
          
          // urban_analysis의 경우 year2 추가
          if (autoExecuteUpdate.analysis_type === 'urban_analysis') {
            manualParams.year2 = autoExecuteUpdate.params.year2;
          }
          
          // threshold가 필요한 분석 유형에만 추가
          if (autoExecuteUpdate.analysis_type === 'sea_level_rise' || 
              autoExecuteUpdate.analysis_type === 'infrastructure_analysis' ||
              autoExecuteUpdate.analysis_type === 'urban_analysis') {
            manualParams.threshold = autoExecuteUpdate.params.threshold;
          }
          
          // topic_modeling의 경우 특별한 파라미터들 추가
          if (autoExecuteUpdate.analysis_type === 'topic_modeling') {
            manualParams.method = autoExecuteUpdate.params.method || 'lda';
            manualParams.nTopics = autoExecuteUpdate.params.nTopics || 10;
            manualParams.minDf = autoExecuteUpdate.params.minDf || 2.0;
            manualParams.maxDf = autoExecuteUpdate.params.maxDf || 0.95;
            manualParams.ngramRange = autoExecuteUpdate.params.ngramRange || '1,1';
            manualParams.inputType = autoExecuteUpdate.params.inputType || 'text';
            manualParams.textInput = autoExecuteUpdate.params.textInput || '';
            manualParams.files = autoExecuteUpdate.params.files || [];
          }
          
          console.log('🔍 [ChatPage] Auto-executing with manual params:', manualParams);
          handleAnalyze(manualParams);
        } else {
          console.log('🔍 [ChatPage] Calling handleAnalyze with:', {
            type: 'chat_triggered',
            updates: aiMsg.dashboard_updates,
            analysis_type: aiMsg.analysis_type || 'sea_level_rise'
          });
          handleAnalyze({
            type: 'chat_triggered',
            updates: aiMsg.dashboard_updates,
            analysis_type: aiMsg.analysis_type || 'sea_level_rise'
          });
        }
        console.log('🔍 [ChatPage] handleAnalyze called, params should be updated');
      } else {
        console.log('❌ [ChatPage] No dashboard updates or manual redirect in AI message');
      }
    } catch (e) {
      console.error('Error sending message:', e);
      setMessages(prev => [...prev, { 
        id: `ai-error-${Date.now()}`, 
        sender: 'ai', 
        content: '[AI Error]', 
        created_at: new Date().toISOString() 
      }]);
    } finally {
      setAiThinking(false);
      setIsSending(false);
    }
  };

  return (
    <PanelGroup direction="horizontal" style={{ height: '100vh' }}>
      {/* Left: Analysis Sidebar */}
      <Panel defaultSize={25} minSize={20} maxSize={40}>
        <MapSidebar onAnalyze={handleAnalyze} initialParams={params} />
      </Panel>
      
      <PanelResizeHandle className="resize-handle" />
      
      {/* Center: Chat Sidebar + Chat Window */}
      <Panel defaultSize={35} minSize={30} maxSize={50}>
        <Box display="flex" height="100%">
          <ChatSidebar
            chats={chats}
            selectedChatId={selectedChatId}
            onSelect={handleSelectChat}
            onCreate={handleCreateChat}
          />
          <Box flex={1} display="flex" flexDirection="column" minHeight={0}>
            {loadingChats ? (
              <Box flex={1} display="flex" alignItems="center" justifyContent="center"><CircularProgress /></Box>
            ) : isComposingNewChat ? (
              <ChatWindow messages={[]} onSend={handleSendMessage} loading={aiThinking} />
            ) : selectedChatId ? (
              <ChatWindow messages={messages} onSend={handleSendMessage} loading={aiThinking} />
            ) : (
              <Box flex={1} display="flex" flexDirection="column" alignItems="center" justifyContent="center" bgcolor="#f7f8fa">
                <Box textAlign="center">
                  <Typography variant="h4" fontWeight={700} mb={2}>
                    Welcome to AI Assistant
                  </Typography>
                  <Typography variant="subtitle1" color="text.secondary" mb={4}>
                    Start a new conversation to get help with your questions, analyze documents, or just chat!
                  </Typography>
                  <Button variant="contained" size="large" onClick={handleCreateChat} sx={{ fontWeight: 600, fontSize: 18, px: 4, py: 1.5 }}>
                    Start New Chat
                  </Button>
                </Box>
              </Box>
            )}
          </Box>
        </Box>
      </Panel>
      
      <PanelResizeHandle className="resize-handle" />
      
      {/* Right: Visualization/Analytics */}
      <Panel defaultSize={40} minSize={30} maxSize={50}>
        <Box height="100%" bgcolor="#fafbfc" p={2} style={{ overflowY: 'auto', borderLeft: '1px solid #eee' }}>
          {/* Show analytics based on params */}
          {!params && <div style={{ color: '#888', textAlign: 'center', marginTop: 100 }}>Select analysis options and click "Analyze it" to view analytics.</div>}
          {params && (params.task === 'slr-risk' || params.analysis_type === 'sea_level_rise') && <MapDisplay params={params} />}
          {params && params.task === 'urban-area-comprehensive' && <><MapDisplay params={params} /><UrbanAreaComprehensiveCharts startYear={params.year1} endYear={params.year2} /></>}
          {params && params.task === 'infrastructure-exposure' && <InfrastructureExposure year={params.year1} threshold={params.threshold} city={params.city} />}
          {params && params.task === 'topic-modeling' && <TopicModeling params={params} />}
        </Box>
      </Panel>
    </PanelGroup>
  );
}

export default ChatPage;
