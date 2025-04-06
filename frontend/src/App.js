import React, { useState } from 'react';
import { Box, Container, Typography, Paper, ThemeProvider, createTheme, IconButton, Tabs, Tab } from '@mui/material';
import UploadSection from './components/UploadSection';
import BrainRotSection from './components/BrainRotSection';
import GrassEffect from './components/GrassEffect';
import GrassIcon from '@mui/icons-material/Grass';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const [showGrass, setShowGrass] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
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
          <Paper
            elevation={3}
            sx={{
              p: 4,
              borderRadius: 2,
              textAlign: 'center',
            }}
          >
            <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 'bold', mb: 4 }}>
              ResearchRot
            </Typography>
            
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
              <Tabs value={currentTab} onChange={handleTabChange} centered>
                <Tab label="Research" />
                <Tab label="Brain Rot" />
              </Tabs>
            </Box>

            {currentTab === 0 ? (
              <>
                <Typography variant="h6" color="text.secondary" paragraph>
                  Upload your files or add URLs to get started
                </Typography>
                <UploadSection />
              </>
            ) : (
              <BrainRotSection />
            )}
          </Paper>
        </Container>

        {showGrass && (
          <GrassEffect onClose={() => setShowGrass(false)} />
        )}
      </Box>
    </ThemeProvider>
  );
}

export default App;
