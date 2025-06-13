import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  Button,
  LinearProgress,
  Chip,
  Avatar,
  AvatarGroup,
  Tooltip,
  Paper,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  AccessTime,
  Folder,
  Assignment,
  Warning,
  CheckCircle,
  Schedule,
  Analytics,
  AutoAwesome,
  Refresh,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

// Custom Components
import StatCard from './StatCard';
import ActivityTimeline from './ActivityTimeline';
import CaseOverview from './CaseOverview';
import AIInsightsPanel from './AIInsightsPanel';
import QuickActions from './QuickActions';
import DocumentHeatmap from './DocumentHeatmap';
import DeadlineCalendar from './DeadlineCalendar';

// Hooks
import { useAI } from '../../contexts/AIContext';
import { useDocuments } from '../../contexts/DocumentContext';
import { useCases } from '../../contexts/CaseContext';
import { useWebSocket } from '../../hooks/useWebSocket';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { getInsights, getRecommendations } = useAI();
  const { documents, getRecentDocuments } = useDocuments();
  const { cases, getActiveCases, getUpcomingDeadlines } = useCases();
  const { subscribe } = useWebSocket();

  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalDocuments: 0,
    activeCases: 0,
    upcomingDeadlines: 0,
    processingQueue: 0,
  });
  const [aiInsights, setAiInsights] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    loadDashboardData();
    
    // Subscribe to real-time updates
    const unsubscribe = subscribe('dashboard-update', (data) => {
      updateDashboardData(data);
    });

    return () => unsubscribe();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all dashboard data in parallel
      const [
        documentsData,
        casesData,
        deadlinesData,
        insights,
        recommendations,
        activity
      ] = await Promise.all([
        getRecentDocuments(10),
        getActiveCases(),
        getUpcomingDeadlines(7),
        getInsights(),
        getRecommendations(),
        fetchRecentActivity(),
      ]);

      setStats({
        totalDocuments: documentsData.total,
        activeCases: casesData.length,
        upcomingDeadlines: deadlinesData.length,
        processingQueue: documentsData.processing,
      });

      setAiInsights([...insights, ...recommendations]);
      setRecentActivity(activity);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecentActivity = async () => {
    // Fetch recent activity from API
    return [];
  };

  const updateDashboardData = (data: any) => {
    // Update dashboard with real-time data
    if (data.type === 'document_processed') {
      setStats(prev => ({
        ...prev,
        totalDocuments: prev.totalDocuments + 1,
        processingQueue: Math.max(0, prev.processingQueue - 1),
      }));
    }
  };

  return (
    <Box sx={{ p: 3, height: '100%', overflow: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          Legal Intelligence Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Welcome back! Here's your case management overview.
        </Typography>
      </Box>

      {/* Quick Actions */}
      <QuickActions sx={{ mb: 3 }} />

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Documents"
            value={stats.totalDocuments}
            icon={<Folder />}
            trend="+12%"
            color="primary"
            onClick={() => navigate('/documents')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Cases"
            value={stats.activeCases}
            icon={<Assignment />}
            trend="+3"
            color="success"
            onClick={() => navigate('/cases')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Upcoming Deadlines"
            value={stats.upcomingDeadlines}
            icon={<Schedule />}
            trend="This week"
            color="warning"
            onClick={() => navigate('/cases/deadlines')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Processing Queue"
            value={stats.processingQueue}
            icon={<AccessTime />}
            trend="-5"
            color="info"
            loading={stats.processingQueue > 0}
          />
        </Grid>
      </Grid>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Left Column */}
        <Grid item xs={12} lg={8}>
          {/* AI Insights Panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <AIInsightsPanel 
              insights={aiInsights}
              onRefresh={loadDashboardData}
              sx={{ mb: 3 }}
            />
          </motion.div>

          {/* Case Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <CaseOverview 
              cases={cases}
              sx={{ mb: 3 }}
            />
          </motion.div>

          {/* Document Heatmap */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <DocumentHeatmap 
              documents={documents}
              sx={{ mb: 3 }}
            />
          </motion.div>
        </Grid>

        {/* Right Column */}
        <Grid item xs={12} lg={4}>
          {/* Deadline Calendar */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5 }}
          >
            <DeadlineCalendar 
              deadlines={getUpcomingDeadlines(30)}
              sx={{ mb: 3 }}
            />
          </motion.div>

          {/* Activity Timeline */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <ActivityTimeline 
              activities={recentActivity}
              sx={{ mb: 3 }}
            />
          </motion.div>

          {/* Team Activity */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Team Activity
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <AvatarGroup max={4}>
                    <Avatar alt="User 1" src="/avatars/1.jpg" />
                    <Avatar alt="User 2" src="/avatars/2.jpg" />
                    <Avatar alt="User 3" src="/avatars/3.jpg" />
                    <Avatar alt="User 4" src="/avatars/4.jpg" />
                  </AvatarGroup>
                  <Typography variant="body2" color="text.secondary">
                    4 team members online
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {/* Loading Overlay */}
      {loading && (
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
          }}
        >
          <LinearProgress />
        </Box>
      )}
    </Box>
  );
};

export default Dashboard;