import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  IconButton,
  InputAdornment,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import LinkIcon from '@mui/icons-material/Link';
import CloseIcon from '@mui/icons-material/Close';

const UploadSection = () => {
  const [url, setUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUrlSubmit = (event) => {
    event.preventDefault();
    if (url) {
      // Handle URL submission
      console.log('URL submitted:', url);
      setUrl('');
    }
  };

  const handleFileUpload = () => {
    if (selectedFile) {
      // Handle file upload
      console.log('File to upload:', selectedFile);
      setSelectedFile(null);
    }
  };

  return (
    <Box sx={{ mt: 4 }}>
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
            disabled={!url}
          >
            Add URL
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
            >
              Upload File
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default UploadSection; 