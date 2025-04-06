import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  CircularProgress,
  TextField,
} from '@mui/material';

const BrainRotSection = () => {
  const [pdfUrl, setPdfUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [resultVideo, setResultVideo] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!pdfUrl) {
      setError('Please provide a PDF URL');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    
    // Create request data with fixed values
    const requestData = {
      pdf_url: pdfUrl,
      text_color: 'white',
      font_size: 225,
      duration_per_phrase: 3.0,
      position: 'center'
    };
    
    // Log the request data
    console.log('Request data:', requestData);
    
    // Append request data
    formData.append('request', JSON.stringify(requestData));

    try {
      console.log('Sending request...');
      const response = await fetch('http://localhost:8000/generate_brainrot', {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        throw new Error(errorData.error || 'Failed to process video');
      }

      const data = await response.json();
      console.log('Success response:', data);

      if (data.status === 'success') {
        setResultVideo(`data:video/mp4;base64,${data.video_file}`);
      } else {
        setError(data.error || 'Something went wrong');
      }
    } catch (err) {
      console.error('Error details:', err);
      setError(err.message || 'Failed to process video');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          Brain Rot Video Generator
        </Typography>

        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="PDF URL"
            value={pdfUrl}
            onChange={(e) => setPdfUrl(e.target.value)}
            placeholder="Enter PDF URL"
            sx={{ mb: 2 }}
          />
        </Box>

        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={loading || !pdfUrl}
          sx={{ mt: 3, width: '100%' }}
        >
          {loading ? <CircularProgress size={24} /> : 'Generate Video'}
        </Button>

        {error && (
          <Typography color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}

        {resultVideo && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Result
            </Typography>
            <video
              controls
              style={{ width: '100%', maxHeight: '400px' }}
            >
              <source src={resultVideo} type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default BrainRotSection; 