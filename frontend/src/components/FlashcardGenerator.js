import React, { useState } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Slider,
  IconButton,
  Card,
  CardContent,
  CardActions,
  Grid,
  Divider,
} from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import RefreshIcon from '@mui/icons-material/Refresh';
import FlipIcon from '@mui/icons-material/Flip';

const FlashcardGenerator = ({ summary }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [flashcards, setFlashcards] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [count, setCount] = useState(10);

  const handleGenerateFlashcards = async () => {
    if (!summary) {
      setError('No summary available to generate flashcards from');
      return;
    }

    setLoading(true);
    setError(null);
    setFlashcards([]);
    setCurrentIndex(0);
    setIsFlipped(false);

    try {
      // Generate flashcards from the summary
      const response = await fetch('http://localhost:8000/generate-flashcards', {
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
        throw new Error('Failed to generate flashcards');
      }

      const data = await response.json();
      setFlashcards(data.flashcards);
    } catch (err) {
      console.error('Error generating flashcards:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = () => {
    if (currentIndex < flashcards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setIsFlipped(false);
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
      setIsFlipped(false);
    }
  };

  const handleFlip = () => {
    setIsFlipped(!isFlipped);
  };

  const handleCountChange = (event, newValue) => {
    setCount(newValue);
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
      <Typography variant="h5" gutterBottom>
        Generate Flashcards
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Box sx={{ mb: 3 }}>
        <Typography gutterBottom>
          Number of flashcards: {count}
        </Typography>
        <Slider
          value={count}
          onChange={handleCountChange}
          min={5}
          max={20}
          step={1}
          marks
          valueLabelDisplay="auto"
          sx={{ mb: 2 }}
        />
        
        <Button
          variant="contained"
          color="primary"
          onClick={handleGenerateFlashcards}
          disabled={loading || !summary}
          fullWidth
        >
          {loading ? <CircularProgress size={24} /> : 'Generate Flashcards'}
        </Button>
      </Box>
      
      {flashcards.length > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="body2" color="text.secondary">
              Card {currentIndex + 1} of {flashcards.length}
            </Typography>
            <Button
              startIcon={<RefreshIcon />}
              onClick={handleGenerateFlashcards}
              disabled={loading}
            >
              Regenerate
            </Button>
          </Box>
          
          <Box sx={{ perspective: '1000px', height: '300px', position: 'relative' }}>
            <Card
              sx={{
                minHeight: 200,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                p: 2,
                mb: 2,
                position: 'absolute',
                width: '100%',
                height: '100%',
                backfaceVisibility: 'hidden',
                transformStyle: 'preserve-3d',
                transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0)',
                transition: 'transform 0.6s',
              }}
              onClick={handleFlip}
            >
              <CardContent sx={{ textAlign: 'center', width: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Question
                </Typography>
                <Typography variant="body1">
                  {flashcards[currentIndex].question}
                </Typography>
              </CardContent>
              <CardActions>
                <IconButton onClick={handleFlip}>
                  <FlipIcon />
                </IconButton>
              </CardActions>
            </Card>
            
            <Card
              sx={{
                minHeight: 200,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                p: 2,
                mb: 2,
                position: 'absolute',
                width: '100%',
                height: '100%',
                backfaceVisibility: 'hidden',
                transformStyle: 'preserve-3d',
                transform: isFlipped ? 'rotateY(0)' : 'rotateY(-180deg)',
                transition: 'transform 0.6s',
                backgroundColor: '#f5f5f5',
              }}
              onClick={handleFlip}
            >
              <CardContent sx={{ textAlign: 'center', width: '100%' }}>
                <Typography variant="h6" gutterBottom>
                  Answer
                </Typography>
                <Typography variant="body1">
                  {flashcards[currentIndex].answer}
                </Typography>
              </CardContent>
              <CardActions>
                <IconButton onClick={handleFlip}>
                  <FlipIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Box>
          
          <Grid container spacing={2} justifyContent="center">
            <Grid item>
              <Button
                variant="outlined"
                startIcon={<NavigateBeforeIcon />}
                onClick={handlePrevious}
                disabled={currentIndex === 0}
              >
                Previous
              </Button>
            </Grid>
            <Grid item>
              <Button
                variant="outlined"
                endIcon={<NavigateNextIcon />}
                onClick={handleNext}
                disabled={currentIndex === flashcards.length - 1}
              >
                Next
              </Button>
            </Grid>
          </Grid>
        </>
      )}
    </Paper>
  );
};

export default FlashcardGenerator; 