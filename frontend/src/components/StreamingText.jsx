import React, { useState, useEffect, useRef } from 'react';
import { Typography, Box } from '@mui/material';
import ReactMarkdown from 'react-markdown';

/**
 * StreamingText component that displays text character by character
 * like a typewriter effect for assistant messages
 */
function StreamingText({ text, speed = 20, onComplete, startImmediately = true, messageId }) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const currentIndexRef = useRef(0);
  const timeoutRef = useRef(null);
  const startTimeRef = useRef(null);
  const previousTextRef = useRef('');

  useEffect(() => {
    // Cleanup any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    // If text is empty, reset and return
    if (!text) {
      setDisplayedText('');
      setIsComplete(false);
      currentIndexRef.current = 0;
      return;
    }

    // If text changed completely, reset
    if (previousTextRef.current !== text) {
      setDisplayedText('');
      setIsComplete(false);
      currentIndexRef.current = 0;
      previousTextRef.current = text;
    }

    // If already fully displayed, mark as complete
    if (displayedText === text && text.length > 0) {
      setIsComplete(true);
      return;
    }

    if (!startImmediately) {
      setDisplayedText(text);
      setIsComplete(true);
      return;
    }

    // Start streaming
    const stream = () => {
      if (currentIndexRef.current < text.length) {
        // Calculate dynamic speed based on character type
        let charSpeed = speed;
        const char = text[currentIndexRef.current];
        
        // Faster for spaces and punctuation
        if (char === ' ' || char === '\n') {
          charSpeed = speed * 0.3;
        } else if (/[.,!?;:]/.test(char)) {
          charSpeed = speed * 1.5;
        }

        const nextIndex = currentIndexRef.current + 1;
        setDisplayedText(text.slice(0, nextIndex));
        currentIndexRef.current = nextIndex;

        // Use dynamic speed for next character
        timeoutRef.current = setTimeout(stream, charSpeed);
      } else {
        setIsComplete(true);
        if (onComplete) {
          onComplete();
        }
      }
    };

    // Start streaming after a short delay
    timeoutRef.current = setTimeout(stream, 50);

    // Cleanup on unmount or text change
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [text, speed, onComplete, startImmediately, messageId]);

  // Markdown styles
  const markdownStyles = {
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
  };

  // If not streaming, show full text immediately with markdown
  if (!startImmediately || !text) {
    return (
      <Box sx={markdownStyles}>
        <ReactMarkdown>{text}</ReactMarkdown>
      </Box>
    );
  }

  // Show streaming text with cursor and markdown rendering
  return (
    <Box sx={markdownStyles}>
      <ReactMarkdown>{displayedText}</ReactMarkdown>
      {!isComplete && (
        <span
          style={{
            display: 'inline-block',
            width: '2px',
            height: '1em',
            backgroundColor: 'currentColor',
            marginLeft: '2px',
            animation: 'blink 1s infinite',
            verticalAlign: 'baseline',
          }}
        >
          <style>{`
            @keyframes blink {
              0%, 50% { opacity: 1; }
              51%, 100% { opacity: 0; }
            }
          `}</style>
        </span>
      )}
    </Box>
  );
}

export default StreamingText;

