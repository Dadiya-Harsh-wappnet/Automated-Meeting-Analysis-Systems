// src/components/Footer.js
import React from "react";
import { Box, Typography } from "@mui/material";

function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        textAlign: "center",
        p: 2,
        backgroundColor: "#f0f0f0",
        mt: "auto"
      }}
    >
      <Typography variant="body2" color="textSecondary">
        © {new Date().getFullYear()} Meeting Analysis System
      </Typography>
    </Box>
  );
}

export default Footer;
