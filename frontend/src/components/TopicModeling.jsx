import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Paper, Grid, Chip, Button, CircularProgress, Alert } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B6B', '#4ECDC4', '#45B7D1'];

const TopicModeling = ({ params = {} }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(0);
  const isRunningRef = useRef(false);

  useEffect(() => {
    if (params && params.task === 'topic-modeling' && !isRunningRef.current) {
      runTopicModeling();
    }
  }, [params?.task, params?.method, params?.nTopics, params?.minDf, params?.maxDf, params?.ngramRange, params?.inputType, params?.textInput, params?.files?.length]);

  const runTopicModeling = async () => {
    if (isRunningRef.current) {
      console.log('Topic modeling already running, skipping...');
      return;
    }
    
    isRunningRef.current = true;
    setLoading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('method', params.method);
      formData.append('n_topics', params.nTopics);
      formData.append('min_df', params.minDf);
      formData.append('max_df', params.maxDf);
      formData.append('ngram_range', params.ngramRange);
      
      if (params.inputType === 'text' && params.textInput) {
        formData.append('text_input', params.textInput);
      } else if (params.inputType === 'files' && params.files) {
        params.files.forEach(file => {
          formData.append('files', file);
        });
      }

      const response = await fetch('http://localhost:8000/analysis/topic-modeling', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      // Check if there's a message indicating no topics found
      if (result.message) {
        setError(result.message);
        setData({ topics: [], document_topics: [], wordclouds: [] });
      } else {
        setData(result);
      }
    } catch (err) {
      console.error('Topic modeling error:', err);
      setError(`Error: ${err.message}`);
      setData({ topics: [], document_topics: [], wordclouds: [] });
    } finally {
      setLoading(false);
      isRunningRef.current = false;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error: {error}
      </Alert>
    );
  }

  if (!data) {
    return (
      <Box textAlign="center" py={4}>
        <Typography variant="h6" color="text.secondary">
          Select topic modeling parameters and click "Analyze it" to run the analysis.
        </Typography>
      </Box>
    );
  }

  const { 
    topics = [], 
    document_topics = [], 
    method = 'lda', 
    n_topics = 0, 
    total_documents = 0, 
    is_auto_topic_detection = false, 
    model_info = {} 
  } = data || {};

  // Prepare data for topic word charts
  const topicWordsData = topics[selectedTopic]?.words?.map((word, index) => ({
    word,
    weight: topics[selectedTopic].weights?.[index] || 0
  })) || [];

  // Prepare data for document-topic distribution
  const docTopicData = document_topics.slice(0, 10).map((doc, index) => ({
    document: doc.doc_name || doc.document || `Document ${index + 1}`,
    ...Object.fromEntries(
      Object.entries(doc.topic_distribution || {}).map(([key, value]) => [
        key.replace('topic_', 'Topic '),
        value
      ])
    )
  }));

  return (
    <Box p={3}>
      <Typography variant="h4" gutterBottom>
        Topic Modeling Results
      </Typography>
      
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Analysis Summary</Typography>
        <Grid container spacing={2}>
          <Grid item xs={6} md={3}>
            <Typography variant="body2" color="text.secondary">Method</Typography>
            <Typography variant="h6">{method.toUpperCase()}</Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="body2" color="text.secondary">Topics</Typography>
            <Typography variant="h6">
              {n_topics || 'Auto-detected'}
              {is_auto_topic_detection && (
                <Typography variant="caption" display="block" color="text.secondary">
                  (Auto-detected)
                </Typography>
              )}
            </Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="body2" color="text.secondary">Documents</Typography>
            <Typography variant="h6">{total_documents}</Typography>
          </Grid>
          <Grid item xs={6} md={3}>
            <Typography variant="body2" color="text.secondary">N-gram Range</Typography>
            <Typography variant="h6">{params.ngramRange}</Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Topic Selection */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Select Topic</Typography>
        <Box display="flex" flexWrap="wrap" gap={1}>
          {topics.map((topic, index) => (
            <Chip
              key={index}
              label={`Topic ${index + 1}`}
              onClick={() => setSelectedTopic(index)}
              color={selectedTopic === index ? "primary" : "default"}
              variant={selectedTopic === index ? "filled" : "outlined"}
              style={{ cursor: 'pointer' }}
            />
          ))}
        </Box>
      </Paper>

      {/* Selected Topic Words */}
      {topics[selectedTopic] && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Topic {selectedTopic + 1} - Top Words
          </Typography>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topicWordsData.slice(0, 15)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="word" angle={-45} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="weight" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </Paper>
      )}
      
      {/* Wordcloud for Selected Topic */}
      {topics[selectedTopic] && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Topic {selectedTopic + 1} - Wordcloud
          </Typography>
          <Box 
            display="flex" 
            justifyContent="center" 
            alignItems="center" 
            minHeight={400}
            border="1px solid #eee"
            borderRadius={2}
            bgcolor="#fafafa"
          >
            {data?.wordclouds && data.wordclouds[selectedTopic] ? (
              <img 
                src={data.wordclouds[selectedTopic].wordcloud_data} 
                alt={`Topic ${selectedTopic + 1} Wordcloud`}
                style={{ maxWidth: '100%', height: 'auto' }}
              />
            ) : (
              <CircularProgress />
            )}
          </Box>
        </Paper>
      )}

      {/* Document-Topic Distribution */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Document-Topic Distribution (Top 10 Documents)
        </Typography>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={docTopicData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="document" angle={-45} textAnchor="end" height={80} />
            <YAxis />
            <Tooltip />
            <Legend />
            {topics.slice(0, 5).map((_, index) => (
              <Bar 
                key={index} 
                dataKey={`Topic ${index + 1}`} 
                fill={COLORS[index % COLORS.length]}
                stackId="a"
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </Paper>

      {/* Topic Overview */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>All Topics Overview</Typography>
        <Grid container spacing={2}>
          {topics.map((topic, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Topic {index + 1}
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0.5}>
                  {topic.top_words.slice(0, 8).map((word, wordIndex) => (
                    <Chip
                      key={wordIndex}
                      label={word}
                      size="small"
                      variant="outlined"
                    />
                  ))}
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
};

export default TopicModeling;
