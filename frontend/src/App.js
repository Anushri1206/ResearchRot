import React, { useState } from 'react';
import { Box, Container, Typography, Paper, ThemeProvider, IconButton } from '@mui/material';
import UploadSection from './components/UploadSection';
import GrassEffect from './components/GrassEffect';
import GrassIcon from '@mui/icons-material/Grass';
import FlashcardGenerator from './components/FlashcardGenerator';
import MnemonicGenerator from './components/MnemonicGenerator';
import theme from './theme';
import { CssBaseline } from '@mui/material';

function App() {
  const [showGrass, setShowGrass] = useState(false);
  const [summary, setSummary] = useState(null);

  const handleSummaryGenerated = (newSummary) => {
    setSummary(newSummary);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: 'background.default',
          py: 4,
          position: 'relative',
        }}
      >
        <IconButton
          onClick={() => setShowGrass(true)}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            bgcolor: 'primary.main',
            color: 'white',
            '&:hover': {
              bgcolor: 'primary.dark',
              transform: 'scale(1.1)',
            },
            transition: 'all 0.3s ease',
            boxShadow: 3,
          }}
        >
          <GrassIcon />
        </IconButton>

        <Container maxWidth="md">
          <Box sx={{ my: 4 }}>
            <Typography variant="h3" component="h1" gutterBottom align="center">
              ResearchRot
            </Typography>
            <Typography variant="h5" component="h2" gutterBottom align="center" color="text.secondary">
              Transform Research Papers into Brain Rot
            </Typography>
            
            <Paper elevation={3} sx={{ p: 3, mt: 3 }}>
              <UploadSection onSummaryGenerated={handleSummaryGenerated} />
            </Paper>
            
            {summary && (
              <>
                <FlashcardGenerator summary={summary} />
                <MnemonicGenerator summary={summary} />
              </>
            )}
          </Box>
        </Container>

        {showGrass && (
          <GrassEffect onClose={() => setShowGrass(false)} />
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
