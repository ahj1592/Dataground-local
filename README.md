# DataGround

A geospatial analytics platform for urban expansion, sea-level rise risk, and population exposure, featuring an AI assistant and interactive map visualizations.

## Features
- **AI Assistant**: Chat-based interface for data queries and project guidance.
- **Analytics Map**: Interactive map with overlays for SLR risk, urban expansion, and population exposure.
- **Time Series Analysis**: Visualize urban growth and risk trends over time.
- **User Authentication**: Secure login and signup.
- **File Upload**: Upload and analyze geospatial datasets.

## Project Structure
```
data-ground-progress/
  backend/           # FastAPI backend (APIs, GEE integration, DB)
    app/
      main.py        # FastAPI entrypoint
      gee.py         # Google Earth Engine logic
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
   uvicorn app.main:app --reload
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
- **backend/app/gee.py**: GEE logic for SLR, urban, and population analytics
- **backend/app/main.py**: FastAPI entrypoint and API routing
- **frontend/src/components/MainTabs.jsx**: Main tab navigation (AI Assistant, Analytics, Time series)
- **frontend/src/components/LoginPage.jsx**: Login page with DataGround logo
- **frontend/src/components/MapDisplay.jsx**: Interactive map with overlays
- **frontend/src/components/UrbanExpansionCharts.jsx**: Urban growth and risk charts

## Demo Notes
- Use the provided login/signup to access the platform.
- The AI Assistant tab provides chat-based help and data queries.
- The Analytics tab displays interactive maps and overlays.
- The Time series tab shows urban growth and risk trends.
- For demo purposes, Jakarta is used as the default region.

---

**For questions or issues, contact the project team.** 