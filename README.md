# DataGround - Local Version

A geospatial analytics platform for urban expansion, sea-level rise risk, and population exposure, featuring an AI assistant and interactive map visualizations.

## Features
- **AI Assistant**: Chat-based interface with Google ADK agents for data queries and project guidance.
- **Analytics Map**: Interactive map with overlays for SLR risk, urban expansion, and population exposure.
- **Time Series Analysis**: Visualize urban growth and risk trends over time.
- **User Authentication**: Secure login and signup.
- **File Upload**: Upload and analyze geospatial datasets.

## Project Structure
```
dataground-250900/
  backend/           # FastAPI backend (APIs, GEE integration, DB)
    app/
      main.py        # FastAPI entrypoint
      adk_chat.py    # Google ADK integration
      analysis.py    # Google Earth Engine logic
      ...
    requirements.txt # Backend dependencies
  frontend/          # React frontend (Vite, MUI, Leaflet)
    src/
      components/    # Main React components
      images/        # Static images (e.g., logo)
    package.json     # Frontend dependencies
```

## Backend Setup
1. **Install dependencies:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. **Run the server:**
   ```bash
   python start_server.py
   ```

## Frontend Setup
1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```
2. **Run the dev server:**
   ```bash
   npm run dev
   ```

## Main Components
- **backend/app/analysis.py**: GEE logic for SLR, urban, and population analytics
- **backend/app/main.py**: FastAPI entrypoint and API routing
- **backend/app/adk_chat.py**: Google ADK agent integration
- **frontend/src/components/ChatPage.jsx**: Main chat interface with AI assistant
- **frontend/src/components/MapDisplay.jsx**: Interactive map with overlays
- **frontend/src/components/UrbanAreaComprehensiveCharts.jsx**: Urban growth and risk charts

## Demo Notes
- Use the provided login/signup to access the platform.
- The AI Assistant provides chat-based help and data queries using Google ADK agents.
- The Analytics tab displays interactive maps and overlays.
- The Time series tab shows urban growth and risk trends.
- For demo purposes, Jakarta is used as the default region.

---

**For questions or issues, contact the project team.**
