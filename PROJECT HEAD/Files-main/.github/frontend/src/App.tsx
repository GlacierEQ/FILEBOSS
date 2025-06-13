import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Box from '@mui/material/Box';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Core Components
import Dashboard from './components/Dashboard/Dashboard';
import DocumentWorkspace from './components/DocumentWorkspace/DocumentWorkspace';
import CaseBuilder from './components/CaseBuilder/CaseBuilder';
import AICollaborationPanel from './components/AI/AICollaborationPanel';
import SettingsPanel from './components/Settings/SettingsPanel';
import NavigationBar from './components/Navigation/NavigationBar';
import NotificationCenter from './components/Notifications/NotificationCenter';

// Providers
import { AIProvider } from './contexts/AIContext';
import { DocumentProvider } from './contexts/DocumentContext';
import { CaseProvider } from './contexts/CaseContext';
import { UserProvider } from './contexts/UserContext';
import { WebSocketProvider } from './contexts/WebSocketContext';

// Hooks
import { useLocalStorage } from './hooks/useLocalStorage';
import { useWebSocket } from './hooks/useWebSocket';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';

// Types
import { ThemeMode, UserPreferences } from './types';

const App: React.FC = () => {
  const [themeMode, setThemeMode] = useLocalStorage<ThemeMode>('theme', 'light');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [aiPanelOpen, setAiPanelOpen] = useState(true);
  const [userPreferences, setUserPreferences] = useLocalStorage<UserPreferences>('preferences', {
    theme: 'light',
    layout: 'default',
    notifications: true,
    autoSave: true,
    aiSuggestions: true,
    voiceEnabled: false,
  });

  // Create dynamic theme based on user preference
  const theme = createTheme({
    palette: {
      mode: themeMode,
      primary: {
        main: themeMode === 'light' ? '#1976d2' : '#90caf9',
      },
      secondary: {
        main: themeMode === 'light' ? '#dc004e' : '#f48fb1',
      },
      background: {
        default: themeMode === 'light' ? '#f5f5f5' : '#121212',
        paper: themeMode === 'light' ? '#ffffff' : '#1e1e1e',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 600,
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 500,
      },
      body1: {
        fontSize: '1rem',
        lineHeight: 1.7,
      },
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: 8,
            padding: '8px 16px',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            boxShadow: themeMode === 'light' 
              ? '0 2px 8px rgba(0,0,0,0.1)' 
              : '0 2px 8px rgba(0,0,0,0.3)',
          },
        },
      },
    },
  });

  // Toggle theme
  const toggleTheme = useCallback(() => {
    const newMode = themeMode === 'light' ? 'dark' : 'light';
    setThemeMode(newMode);
    setUserPreferences(prev => ({ ...prev, theme: newMode }));
  }, [themeMode, setThemeMode, setUserPreferences]);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    'ctrl+k': () => document.getElementById('command-palette')?.focus(),
    'ctrl+/': () => setAiPanelOpen(prev => !prev),
    'ctrl+b': () => setSidebarOpen(prev => !prev),
    'ctrl+shift+t': toggleTheme,
  });

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider>
        <UserProvider preferences={userPreferences}>
          <AIProvider>
            <DocumentProvider>
              <CaseProvider>
                <Router>
                  <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
                    {/* Navigation Bar */}
                    <NavigationBar 
                      open={sidebarOpen}
                      onToggle={() => setSidebarOpen(!sidebarOpen)}
                      onThemeToggle={toggleTheme}
                      themeMode={themeMode}
                    />

                    {/* Main Content Area */}
                    <Box
                      component="main"
                      sx={{
                        flexGrow: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        overflow: 'hidden',
                        transition: 'margin-left 0.3s ease',
                        marginLeft: sidebarOpen ? '240px' : '64px',
                      }}
                    >
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/documents/*" element={<DocumentWorkspace />} />
                        <Route path="/cases/*" element={<CaseBuilder />} />
                        <Route path="/settings" element={<SettingsPanel />} />
                      </Routes>
                    </Box>

                    {/* AI Collaboration Panel */}
                    <AICollaborationPanel 
                      open={aiPanelOpen}
                      onToggle={() => setAiPanelOpen(!aiPanelOpen)}
                    />

                    {/* Notification Center */}
                    <NotificationCenter />
                  </Box>
                </Router>
              </CaseProvider>
            </DocumentProvider>
          </AIProvider>
        </UserProvider>
      </WebSocketProvider>
    </ThemeProvider>
  );
};

export default App;