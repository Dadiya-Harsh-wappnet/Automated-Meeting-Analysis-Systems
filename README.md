# Automated-Meeting-Analysis-Systems
## AMAS 360

AMAS 360 (Automated Meeting Analysis System 360) is a comprehensive application designed to streamline meeting analysis and HR insights. The system integrates two major components:

- **Chatbot**: An AI-powered conversational interface (using an LLM such as Groq or similar) that helps employees, managers, and HR interactively query meeting transcripts and related data.
- **HR Dashboard**: An interactive dashboard that displays comprehensive meeting analytics, user participation, and transcript performance through graphical visualizations and detailed summaries.

AMAS 360 is built using Flask for the backend, SQLAlchemy for database interactions (with a PostgreSQL database based on the AMAS schema), and Matplotlib for generating visual insights.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Multi-Role Chatbot**:  
  - Three separate chatbot endpoints for Employees, Managers, and HR.
  - Role-specific responses powered by a large language model (LLM) to provide relevant insights.
  - Employee chatbot restricts data access so that users only see their own data.

- **HR Dashboard**:  
  - Displays overall summary metrics: total users, meetings, transcript counts, and average transcript durations.
  - Visualizes meeting participation per user and transcript trends through bar and line charts.
  - Provides user-specific analysis: HR can select an individual to view detailed performance and meeting data.

- **Data Integration**:  
  - Uses a PostgreSQL database with an AMAS schema that includes tables for users, meetings, meeting participants, and meeting transcripts.
  - SQLAlchemy ORM facilitates smooth database interaction.

- **Visualization**:  
  - Generates charts using Matplotlib (with a non-interactive Agg backend) and embeds them in the dashboard.
  - Dynamic plot generation based on live data queries.

## Architecture

AMAS 360 is built on a modular architecture:

- **Backend**:  
  - **Flask**: Serves as the web framework, handling routes for the chatbot and dashboard.
  - **SQLAlchemy**: Manages ORM mapping and database sessions.
  - **LLM Integration**: A module integrates with Groq LLM (or a similar service) to generate chatbot responses.

- **Frontend**:  
  - **Jinja2 Templates**: Render dynamic HTML pages for the HR dashboard and chatbot interfaces.
  - **Static Assets**: Charts are generated and stored in the static folder and then displayed on the dashboard.

- **Data Storage**:  
  - A PostgreSQL database based on the provided AMAS schema.
  - Tables include `users`, `meetings`, `meeting_participants`, and `meeting_transcripts`.

## Project Structure

```
AMAS_dashboard/
├── app.py                # Main Flask application with routes for chatbot and HR dashboard
├── models.py             # SQLAlchemy models matching the AMAS schema
├── analysis.py           # Functions for computing analytics and generating plots
├── requirements.txt      # List of project dependencies
├── README.md             # This documentation file
├── static/
│   └── plots/            # Generated plot images are saved here
└── templates/
    ├── hr_dashboard.html # HR dashboard landing and user-specific analysis pages
    └── user_analysis.html # (Optional) Separate template for detailed user analysis
```

## Installation

### Prerequisites

- Python (>= 3.8)
- PostgreSQL
- Git (optional, for cloning the repository)

### Steps

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/yourusername/AMAS-360.git
   cd AMAS-360
   ```

2. **Create a Virtual Environment (Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up the PostgreSQL Database**
   - Create a database (for example, meeting_analysis):
   ```sql
   CREATE DATABASE meeting_analysis;
   ```
   - Update the db_url in app.py (and optionally in models.py) with your PostgreSQL credentials:
   ```python
   db_url = "postgresql+psycopg2://your_user:your_password@localhost/meeting_analysis"
   ```

## Configuration

- **Database URL**:
  Edit the `db_url` variable in `app.py` to match your PostgreSQL settings.

- **Matplotlib Backend**:
  Ensure that `analysis.py` uses the Agg backend to prevent GUI errors:
  ```python
  import matplotlib
  matplotlib.use("Agg")
  ```

- **LLM Integration (Chatbot)**:
  If you plan to use an LLM (such as Groq), configure the API key and endpoints in your chatbot module accordingly.

## Usage

### Running the Application

1. **Start the Flask Server**
   ```bash
   python app.py
   ```
   You should see output similar to:
   ```
   * Running on http://127.0.0.1:5000
   ```

2. **Access the HR Dashboard**
   Open your browser and go to:
   ```
   http://127.0.0.1:5000/hr/dashboard
   ```
   The dashboard will display overall summary metrics and visualizations.

3. **User-Specific Analysis**
   From the dashboard, select a user from the dropdown list to view user-specific charts and details.

4. **Chatbot Interaction**
   Access chatbot endpoints for different roles to query meeting data:
   - Employee: `/chatbot/employee`
   - Manager: `/chatbot/manager`
   - HR: `/chatbot/hr`

## Troubleshooting

- **Template Not Found Error**:
  Ensure that the `templates/` directory exists at the same level as `app.py` and that all template file names match exactly (case-sensitive).

- **Matplotlib GUI Warning**:
  If you see warnings about starting a Matplotlib GUI outside of the main thread, confirm that the Agg backend is set at the top of `analysis.py`:
  ```python
  import matplotlib
  matplotlib.use("Agg")
  ```

- **Database Connection Issues**:
  Verify your `db_url` settings and ensure your PostgreSQL server is running.

- **404 on Favicon**:
  You may ignore the favicon 404 error or add a favicon file in the static folder.

## Future Enhancements

- **Advanced Chatbot NLP**:
  Integrate a state-of-the-art LLM (e.g., Groq, GPT) for dynamic, context-aware responses.

- **Interactive Visualizations**:
  Use libraries like Plotly or Chart.js for interactive dashboards.

- **User Authentication & Authorization**:
  Implement secure login and restrict data access based on user roles.

- **Real-Time Data Processing**:
  Add live updates and real-time analytics as new meeting data is ingested.

- **Enhanced Analytics**:
  Expand performance metrics, add sentiment analysis, topic modeling, and deeper statistical insights.

## Contributing

Contributions are welcome! Please fork this repository and create a pull request with your changes. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the LICENSE file for details.