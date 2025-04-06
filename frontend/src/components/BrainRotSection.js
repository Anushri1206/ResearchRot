import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import AddIcon from '@mui/icons-material/Add';

const BrainRotSection = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [phrases, setPhrases] = useState(['']);
  const [loading, setLoading] = useState(false);
  const [resultVideo, setResultVideo] = useState(null);
  const [error, setError] = useState(null);

  const handleVideoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Check if the file is a video
      if (!file.type.startsWith('video/')) {
        setError('Please upload a valid video file');
        setVideoFile(null);
        return;
      }
      
      // Check file size (max 100MB)
      if (file.size > 100 * 1024 * 1024) {
        setError('Video file size should be less than 100MB');
        setVideoFile(null);
        return;
      }
      
      setVideoFile(file);
      setError(null);
    }
  };

  const handlePhraseChange = (index, value) => {
    const newPhrases = [...phrases];
    newPhrases[index] = value;
    setPhrases(newPhrases);
  };

  const addPhrase = () => {
    setPhrases([...phrases, '']);
  };

  const removePhrase = (index) => {
    const newPhrases = phrases.filter((_, i) => i !== index);
    setPhrases(newPhrases);
  };

  const handleSubmit = async () => {
    if (!videoFile || phrases.length === 0) {
      setError('Please upload a video and add at least one phrase');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('video', videoFile);
    
    // Create request data
    const requestData = {
      phrases: phrases.filter(phrase => phrase.trim() !== ''),
      text_color: 'white',
      font_size: 50,
      duration_per_phrase: 2.0,
      position: 'center'
    };
    
    // Log the request data
    console.log('Request data:', requestData);
    console.log('Video file:', videoFile);
    
    // Append request data as a separate field
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
          <Button
            variant="contained"
            component="label"
            sx={{ mb: 2 }}
          >
            Upload Background Video
            <input
              type="file"
              hidden
              accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
              onChange={handleVideoUpload}
            />
          </Button>
          {videoFile && (
            <Box sx={{ ml: 2 }}>
              <Typography variant="body2">
                Selected: {videoFile.name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Supported formats: MP4, MOV, AVI, MKV
              </Typography>
            </Box>
          )}
        </Box>

        <Typography variant="h6" gutterBottom>
          Phrases
        </Typography>
        <List>
          {phrases.map((phrase, index) => (
            <ListItem key={index}>
              <TextField
                fullWidth
                value={phrase}
                onChange={(e) => handlePhraseChange(index, e.target.value)}
                placeholder="Enter phrase"
                variant="outlined"
                size="small"
              />
              <ListItemSecondaryAction>
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => removePhrase(index)}
                >
                  <DeleteIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>

        <Button
          startIcon={<AddIcon />}
          onClick={addPhrase}
          sx={{ mt: 1 }}
        >
          Add Phrase
        </Button>

        <Button
          variant="contained"
          color="primary"
          onClick={handleSubmit}
          disabled={loading}
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