import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Slider,
  Card,
  CardContent,
  Divider,
  Grid,
  IconButton,
} from '@mui/material';
import EmojiObjectsIcon from '@mui/icons-material/EmojiObjects';
import RefreshIcon from '@mui/icons-material/Refresh';

const MnemonicGenerator = ({ summary }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [mnemonics, setMnemonics] = useState([]);
  const [count, setCount] = useState(5);

  const handleGenerateMnemonics = async () => {
    if (!summary) {
      setError('No summary available to generate mnemonics from');
      return;
    }

    setLoading(true);
    setError(null);
    setMnemonics([]);

    try {
      const response = await fetch('http://localhost:8000/generate-mnemonics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          summary,
          count,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate mnemonics');
      }

      const data = await response.json();
      console.log('Received mnemonics data:', data);
      
      if (!data.mnemonics || data.mnemonics.length === 0) {
        throw new Error('No mnemonics were generated');
      }

      setMnemonics(data.mnemonics);
    } catch (err) {
      console.error('Error generating mnemonics:', err);
      setError(err.message || 'Failed to generate mnemonics');
    } finally {
      setLoading(false);
    }
  };

  const handleCountChange = (event, newValue) => {
    setCount(newValue);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <EmojiObjectsIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h5" gutterBottom>
          Brain Rotted Mnemonics
        </Typography>
      </Box>
      
      <Typography variant="body1" sx={{ mb: 3 }}>
        Generate fun mnemonics to help you remember key concepts from the research paper because in this day and age we probably all have the attention span of a goldfish. 
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ mb: 3 }}>
        <Typography gutterBottom>
          Number of mnemonics: {count}
        </Typography>
        <Slider
          value={count}
          onChange={handleCountChange}
          aria-labelledby="mnemonic-count-slider"
          valueLabelDisplay="auto"
          step={1}
          marks
          min={3}
          max={10}
          sx={{ mb: 2 }}
        />
        
        <Button
          variant="contained"
          color="primary"
          onClick={handleGenerateMnemonics}
          disabled={loading || !summary}
          fullWidth
        >
          {loading ? <CircularProgress size={24} /> : 'Generate Mnemonics'}
        </Button>
      </Box>
      
      {mnemonics.length > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          
          <Typography variant="h6" gutterBottom>
            Your Mnemonics
          </Typography>
          
          <Grid container spacing={2}>
            {mnemonics.map((mnemonic, index) => (
              <Grid item xs={12} key={index}>
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="subtitle1" color="primary" gutterBottom>
                      Concept: {mnemonic.concept}
                    </Typography>
                    <Typography variant="body1">
                      {mnemonic.mnemonic}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
          
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Button
              startIcon={<RefreshIcon />}
              onClick={handleGenerateMnemonics}
              disabled={loading}
            >
              Regenerate Mnemonics
            </Button>
          </Box>
        </>
      )}
    </Paper>
  );
};

export default MnemonicGenerator; 