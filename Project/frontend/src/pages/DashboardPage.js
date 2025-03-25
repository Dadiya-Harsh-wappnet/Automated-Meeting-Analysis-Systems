// src/pages/DashboardPage.js
import React, { useState, useEffect } from "react";
import { Container, Typography, Grid, Card, CardContent, Box } from "@mui/material";
import PerformanceChart from "../charts/PerformanceChart";
import axios from "axios";

function DashboardPage() {
  const [metrics, setMetrics] = useState([]);

  useEffect(() => {
    // Replace with your backend endpoint for performance metrics
    axios.get("http://localhost:5000/api/meetings/performance") // Stub endpoint – adjust as needed
      .then(res => setMetrics(res.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>Dashboard</Typography>
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ boxShadow: 2 }}>
            <CardContent>
              <Typography variant="h6">Meetings Today</Typography>
              <Typography variant="h4">5</Typography>
              <Typography variant="body2" color="text.secondary">
                You have 5 upcoming meetings today
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ boxShadow: 2 }}>
            <CardContent>
              <Typography variant="h6">Team Sentiment</Typography>
              <Typography variant="h4">+0.75</Typography>
              <Typography variant="body2" color="text.secondary">
                Average sentiment this week
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Box sx={{ p: 2, boxShadow: 2, backgroundColor: "#fff" }}>
            <PerformanceChart data={metrics} chartTitle="Speaking Time" metricType="speaking_time" />
          </Box>
        </Grid>
        <Grid item xs={12} md={6}>
          <Box sx={{ p: 2, boxShadow: 2, backgroundColor: "#fff" }}>
            <PerformanceChart data={metrics} chartTitle="Sentiment Over Time" metricType="sentiment_average" />
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
}

export default DashboardPage;
