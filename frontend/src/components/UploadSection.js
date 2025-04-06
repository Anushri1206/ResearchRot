import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  IconButton,
  InputAdornment,
  CircularProgress,
  Alert,
  ButtonGroup,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import LinkIcon from '@mui/icons-material/Link';
import CloseIcon from '@mui/icons-material/Close';
import SummarizeIcon from '@mui/icons-material/Summarize';
import PodcastsIcon from '@mui/icons-material/Podcasts';

const UploadSection = () => {
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);

  // converts the arxiv url to a pdf url 
  const convertArxivUrl = (inputUrl) => {
    const arxivRegex = /^https?:\/\/(?:www\.)?arxiv\.org\/(?:abs|pdf)\/(\d{4}\.\d{4,5})(?:\.pdf)?$/;
    const match = inputUrl.match(arxivRegex);
    
    if (match) {
      return `https://arxiv.org/pdf/${match[1]}`;
    }
    return inputUrl;
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      setResponse(null);
      setAudioUrl(null);
    }
  };

  const handleUrlSubmit = async (event, action = 'summarize') => {
    event.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setAudioUrl(null);

    try {
      const convertedUrl = convertArxivUrl(url);
      console.log('Sending URL to backend:', convertedUrl);

      const endpoint = action === 'summarize' ? '/query' : '/generate_podcast';
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: convertedUrl,
          is_arxiv: true
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process URL');
      }

      const data = await response.json();
      
      if (action === 'summarize') {
        setResponse(data.answer);
      } else {
        if (data.status === 'error') {
          throw new Error(data.error || 'Failed to generate podcast');
        }
        
        setResponse(data.transcript);
        if (data.audio_file) {
          // Create a data URL from the base64 audio data
          const audioDataUrl = `data:audio/mpeg;base64,${data.audio_file}`;
          setAudioUrl(audioDataUrl);
        } else {
          throw new Error('No audio data received');
        }
      }
    } catch (err) {
      console.error('Error processing URL:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (action = 'summarize') => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResponse(null);
    setAudioUrl(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const uploadResponse = await fetch('http://localhost:8000/upload_pdf', {
        method: 'POST',
        body: formData,
      });

      if (!uploadResponse.ok) {
        throw new Error('Failed to upload PDF');
      }

      const { pdf_path } = await uploadResponse.json();

      const endpoint = action === 'summarize' ? '/query' : '/generate_podcast';
      const response = await fetch(`http://localhost:8000${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          pdf_path: pdf_path
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to process file');
      }

      const data = await response.json();
      
      if (action === 'summarize') {
        setResponse(data.answer);
      } else {
        if (data.status === 'error') {
          throw new Error(data.error || 'Failed to generate podcast');
        }
        
        setResponse(data.transcript);
        if (data.audio_file) {
          // Create a data URL from the base64 audio data
          const audioDataUrl = `data:audio/mpeg;base64,${data.audio_file}`;
          setAudioUrl(audioDataUrl);
        } else {
          throw new Error('No audio data received');
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {response && (
        <Paper
          elevation={2}
          sx={{
            p: 2,
            mb: 3,
            bgcolor: '#f5f5f5',
          }}
        >
          <Typography variant="h6" sx={{ mb: 2 }}>
            {audioUrl ? 'Podcast Transcript:' : 'Summary:'}
          </Typography>
          <Typography variant="body1">{response}</Typography>
        </Paper>
      )}

      {audioUrl && (
        <Paper
          elevation={2}
          sx={{
            p: 2,
            mb: 3,
            bgcolor: '#f5f5f5',
          }}
        >
          <Typography variant="h6" sx={{ mb: 2 }}>Generated Audio:</Typography>
          <audio 
            controls 
            style={{ width: '100%' }}
            onError={(e) => {
              console.error('Audio playback error:', e);
              setError('Failed to play audio. Please try again.');
            }}
          >
            <source src={audioUrl} type="audio/mpeg" />
            Your browser does not support the audio element.
          </audio>
        </Paper>
      )}

      {/* URL Input Section */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          mb: 3,
          border: '2px dashed #e0e0e0',
          borderRadius: 2,
        }}
      >
        <form onSubmit={(e) => handleUrlSubmit(e, 'summarize')}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Enter URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <LinkIcon color="primary" />
                </InputAdornment>
              ),
              endAdornment: url && (
                <InputAdornment position="end">
                  <IconButton onClick={() => setUrl('')} size="small">
                    <CloseIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <ButtonGroup variant="contained" sx={{ mt: 2 }}>
            <Button
              type="submit"
              startIcon={<SummarizeIcon />}
              disabled={!url || loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Summarize'}
            </Button>
            <Button
              onClick={(e) => handleUrlSubmit(e, 'podcast')}
              startIcon={<PodcastsIcon />}
              disabled={!url || loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Generate Podcast'}
            </Button>
          </ButtonGroup>
        </form>
      </Paper>

      {/* File Upload Section */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          border: '2px dashed #e0e0e0',
          borderRadius: 2,
          textAlign: 'center',
        }}
      >
        <input
          accept=".pdf"
          style={{ display: 'none' }}
          id="file-upload"
          type="file"
          onChange={handleFileChange}
        />
        <label htmlFor="file-upload">
          <Button
            variant="outlined"
            component="span"
            startIcon={<CloudUploadIcon />}
            sx={{ mb: 2 }}
          >
            Choose PDF File
          </Button>
        </label>
        {selectedFile && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Selected: {selectedFile.name}
            </Typography>
            <ButtonGroup variant="contained" sx={{ mt: 2 }}>
              <Button
                onClick={() => handleFileUpload('summarize')}
                startIcon={<SummarizeIcon />}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Summarize'}
              </Button>
              <Button
                onClick={() => handleFileUpload('podcast')}
                startIcon={<PodcastsIcon />}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Generate Podcast'}
              </Button>
            </ButtonGroup>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default UploadSection; 