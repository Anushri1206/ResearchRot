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
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import LinkIcon from '@mui/icons-material/Link';
import CloseIcon from '@mui/icons-material/Close';

const UploadSection = () => {
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
      setResponse(null);
    }
  };

  const handleUrlSubmit = async (event) => {
    event.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: url,
          context: null,
          file_content: null,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process URL');
      }

      const data = await response.json();
      setResponse(data.answer);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const fileContent = await selectedFile.text();
      
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: 'Process this file content',
          context: null,
          file_content: fileContent,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to process file');
      }

      const data = await response.json();
      setResponse(data.answer);
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
          <Typography variant="body1">{response}</Typography>
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
        <form onSubmit={handleUrlSubmit}>
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
          <Button
            type="submit"
            variant="contained"
            color="primary"
            sx={{ mt: 2 }}
            disabled={!url || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Process URL'}
          </Button>
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
          accept="*/*"
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
            Choose File
          </Button>
        </label>
        {selectedFile && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Selected: {selectedFile.name}
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={handleFileUpload}
              sx={{ mt: 2 }}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Process File'}
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default UploadSection; 