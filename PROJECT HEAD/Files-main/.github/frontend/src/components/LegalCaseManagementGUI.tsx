  import React, { useState, useEffect, useCallback, useRef } from 'react';
  import {
    Box,
    Grid,
    Paper,
    AppBar,
    Toolbar,
    Typography,
    IconButton,
    Drawer,
    List,
    ListItem,
    ListItemIcon,
    ListItemText,
    Chip,
    Avatar,
    Badge,
    Tooltip,
    Fab,
    Dialog,
    DialogTitle,
    DialogContent,
    TextField,
    Button,
    Card,
    CardContent,
    CardActions,
    LinearProgress,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Tabs,
    Tab,
    Menu,
    MenuItem,
    Switch,
    FormControlLabel,
    Slider,
    useTheme,
    ThemeProvider,
    createTheme,
    CssBaseline,
    alpha
  } from '@mui/material';
  import {
    Dashboard,
    Description,
    Timeline,
    AccountTree,
    Gavel,
    Psychology,
    Brightness4,
    Brightness7,
    Mic,
    MicOff,
    Search,
    FilterList,
    ViewModule,
    ViewList,
    Share,
    Security,
    Settings,
    Help,
    Notifications,
    ExpandMore,
    Add,
    Edit,
    Delete,
    Visibility,
    VisibilityOff,
    CloudUpload,
    GetApp,
    Print,
    Comment,
    Highlight,
    Link,
    Group,
    Schedule,
    Assignment,
    TrendingUp,
    Warning,
    CheckCircle,
    Error,
    Info,
    Close,
    Fullscreen,
    FullscreenExit,
    ZoomIn,
    ZoomOut,
    Undo,
    Redo,
    Save,
    PlayArrow,
    Pause,
    Stop
  } from '@mui/icons-material';
  import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
  import { motion, AnimatePresence } from 'framer-motion';
  import { Line, Bar, Pie, Scatter } from 'react-chartjs-2';
  import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip as ChartTooltip,
    Legend,
  } from 'chart.js';

  // Register Chart.js components
  ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    ChartTooltip,
    Legend
  );

  // Enhanced theme for legal professionals
  const createLegalTheme = (darkMode: boolean) => createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: darkMode ? '#1976d2' : '#1565c0',
        light: darkMode ? '#42a5f5' : '#1976d2',
        dark: darkMode ? '#0d47a1' : '#0d47a1',
      },
      secondary: {
        main: darkMode ? '#f57c00' : '#ff9800',
      },
      success: {
        main: '#4caf50',
      },
      warning: {
        main: '#ff9800',
      },
      error: {
        main: '#f44336',
      },
      background: {
        default: darkMode ? '#0a0a0a' : '#f8f9fa',
        paper: darkMode ? '#1a1a1a' : '#ffffff',
      },
      text: {
        primary: darkMode ? '#ffffff' : '#212121',
        secondary: darkMode ? '#b0b0b0' : '#757575',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: { fontWeight: 600 },
      h6: { fontWeight: 500 },
      body1: { lineHeight: 1.6 },
      body2: { lineHeight: 1.5 },
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            backdropFilter: 'blur(10px)',
            border: darkMode ? '1px solid rgba(255,255,255,0.1)' : '1px solid rgba(0,0,0,0.05)',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: 'none',
            fontWeight: 500,
          },
        },
      },
    },
  });

  // Type definitions
  interface Document {
    id: string;
    name: string;
    type: 'pleading' | 'evidence' | 'correspondence' | 'contract' | 'motion' | 'deposition' | 'exhibit';
    status: 'processing' | 'ready' | 'reviewed' | 'flagged' | 'archived';
    confidence: number;
    lastModified: Date;
    size: string;
    tags: string[];
    relationships: string[];
    priority: 'low' | 'medium' | 'high' | 'urgent';
    assignee?: string;
    annotations: Annotation[];
    securityLevel: 'public' | 'confidential' | 'privileged' | 'work-product';
  }

  interface Annotation {
    id: string;
    type: 'highlight' | 'comment' | 'audio' | 'video';
    content: string;
    position: { start: number; end: number };
    author: string;
    timestamp: Date;
    color?: string;
  }

  interface AIInsight {
    id: string;
    type: 'suggestion' | 'warning' | 'opportunity' | 'contradiction' | 'pattern';
    title: string;
    description: string;
    confidence: number;
    relatedDocuments: string[];
    timestamp: Date;
    reasoning: string[];
    actionable: boolean;
    priority: 'low' | 'medium' | 'high';
  }

  interface Case {
    id: string;
    name: string;
    client: string;
    status: 'active' | 'pending' | 'closed' | 'archived';
    priority: 'low' | 'medium' | 'high' | 'urgent';
    assignedTeam: string[];
    documents: Document[];
    timeline: TimelineEvent[];
    deadlines: Deadline[];
    budget: number;
    billedHours: number;
  }

  interface TimelineEvent {
    id: string;
    title: string;
    description: string;
    date: Date;
    type: 'filing' | 'hearing' | 'meeting' | 'deadline' | 'discovery';
    documents: string[];
    participants: string[];
  }

  interface Deadline {
    id: string;
    title: string;
    date: Date;
    type: 'court' | 'internal' | 'client' | 'discovery';
    status: 'pending' | 'completed' | 'overdue';
    assignee: string;
  }

  const LegalCaseManagementGUI: React.FC = () => {
    // State management
    const [darkMode, setDarkMode] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [aiPanelOpen, setAiPanelOpen] = useState(true);
    const [currentView, setCurrentView] = useState('dashboard');
    const [documents, setDocuments] = useState<Document[]>([]);
    const [aiInsights, setAiInsights] = useState<AIInsight[]>([]);
    const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
    const [voiceMode, setVoiceMode] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [cases, setCases] = useState<Case[]>([]);
    const [selectedCase, setSelectedCase] = useState<string | null>(null);
    const [aiProcessing, setAiProcessing] = useState(false);
    const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
    const [fullscreenMode, setFullscreenMode] = useState(false);
    const [annotationMode, setAnnotationMode] = useState<'highlight' | 'comment' | null>(null);
    const [confidenceThreshold, setConfidenceThreshold] = useState(75);

    const theme = createLegalTheme(darkMode);
    const aiChatRef = useRef<HTMLDivElement>(null);

    // Enhanced AI Collaboration Panel
    const AICollaborationPanel = () => {
      const [chatMessages, setChatMessages] = useState<Array<{
        id: string;
        type: 'user' | 'ai';
        content: string;
        timestamp: Date;
        confidence?: number;
        suggestions?: string[];
      }>>([]);
      const [currentMessage, setCurrentMessage] = useState('');

      const handleSendMessage = async () => {
        if (!currentMessage.trim()) return;

        const userMessage = {
          id: Date.now().toString(),
          type: 'user' as const,
          content: currentMessage,
          timestamp: new Date()
        };

        setChatMessages(prev => [...prev, userMessage]);
        setCurrentMessage('');
        setAiProcessing(true);

        // Simulate AI response
        setTimeout(() => {
          const aiResponse = {
            id: (Date.now() + 1).toString(),
            type: 'ai' as const,
            content: `Based on your query about "${currentMessage}", I found 3 relevant documents and identified a potential contradiction in the timeline. Would you like me to highlight these for review?`,
            timestamp: new Date(),
            confidence: 87,
            suggestions: ['Review timeline', 'Check contradictions', 'Generate summary']
          };
          setChatMessages(prev => [...prev, aiResponse]);
          setAiProcessing(false);
        }, 2000);
      };

      return (
        <Paper
          elevation={3}
          sx={{
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            borderLeft: `1px solid ${theme.palette.divider}`,
            minWidth: aiPanelOpen ? 350 : 60,
            maxWidth: aiPanelOpen ? 500 : 60,
            transition: 'all 0.3s ease'
          }}
        >
          {/* AI Panel Header */}
          <Box sx={{
            p: 2,
            borderBottom: `1px solid ${theme.palette.divider}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            {aiPanelOpen && (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Psychology color="primary" />
                  <Typography variant="h6">AI Assistant</Typography>
                  <Chip
                    label="Online"
                    color="success"
                    size="small"
                    sx={{ animation: 'pulse 2s infinite' }}
                  />
                </Box>
                <IconButton
                  size="small"
                  onClick={() => setAiPanelOpen(false)}
                >
                  <Close />
                </IconButton>
              </>
            )}
            {!aiPanelOpen && (
              <IconButton
                onClick={() => setAiPanelOpen(true)}
                sx={{ mx: 'auto' }}
              >
                <Psychology />
              </IconButton>
            )}
          </Box>

          {aiPanelOpen && (
            <>
              {/* AI Insights Section */}
              <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                  Active Insights ({aiInsights.length})
                </Typography>

                <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                  <AnimatePresence>
                    {aiInsights.slice(0, 3).map((insight, index) => (
                      <motion.div
                        key={insight.id}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <Card
                          elevation={1}
                          sx={{
                            mb: 1,
                            cursor: 'pointer',
                            '&:hover': {
                              elevation: 3,
                              transform: 'translateY(-2px)',
                              transition: 'all 0.2s ease'
                            }
                          }}
                        >
                          <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              <Chip
                                label={insight.type}
                                size="small"
                                color={
                                  insight.type === 'warning' ? 'warning' :
                                  insight.type === 'opportunity' ? 'success' :
                                  insight.type === 'contradiction' ? 'error' : 'info'
                                }
                                icon={
                                  insight.type === 'warning' ? <Warning /> :
                                  insight.type === 'opportunity' ? <TrendingUp /> :
                                  insight.type === 'contradiction' ? <Error /> : <Info />
                                }
                              />
                              <Typography variant="caption" sx={{ ml: 'auto' }}>
                                {insight.confidence}%
                              </Typography>
                            </Box>
                            <Typography variant="body2" fontWeight="medium" gutterBottom>
                              {insight.title}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              {insight.description}
                            </Typography>

                            {insight.actionable && (
                              <Box sx={{ mt: 1 }}>
                                <Button size="small" variant="outlined">
                                  Take Action
                                </Button>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </Box>
              </Box>

              {/* AI Chat Interface */}
              <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                <Box sx={{ flex: 1, overflow: 'auto', p: 2 }} ref={aiChatRef}>
                  {chatMessages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start',
                        mb: 2
                      }}
                    >
                      <Paper
                        elevation={1}
                        sx={{
                          p: 2,
                          maxWidth: '80%',
