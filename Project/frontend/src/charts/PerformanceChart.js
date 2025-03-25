// src/charts/PerformanceChart.js
import React from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

function PerformanceChart({ data, chartTitle, metricType }) {
  // Filter data for the specific metric type; adjust mapping as needed.
  const chartData = data
    .filter(item => item.metric_type === metricType)
    .map(item => ({
      name: `User ${item.user_id}`,
      value: Number(item.metric_value)
    }));

  return (
    <div style={{ width: "100%", height: 300 }}>
      <h4>{chartTitle}</h4>
      <ResponsiveContainer>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#82ca9d" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default PerformanceChart;
