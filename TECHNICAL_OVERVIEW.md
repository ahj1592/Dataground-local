# DataGround Technical Overview

## Project Summary
DataGround is a comprehensive geospatial analytics platform that combines AI-powered conversational agents with interactive data visualization. The system uses Google ADK (Agent Development Kit) for natural language processing and Google Earth Engine for geospatial analysis.

## Core Architecture

### Frontend (React + Vite)
- **Framework**: React 18 with Vite build system
- **UI Library**: Material-UI (MUI) for consistent design
- **Maps**: Leaflet with React-Leaflet for interactive mapping
- **Charts**: Recharts for data visualization
- **Routing**: React Router for client-side navigation
- **State Management**: React hooks and context

### Backend (FastAPI)
- **Framework**: FastAPI for high-performance API development
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT tokens with bcrypt password hashing
- **Validation**: Pydantic for data validation and serialization
- **CORS**: Configured for cross-origin requests

### AI Agent System (Google ADK)
- **Main Agent**: Coordinates conversation and parameter collection
- **Specialized Agents**: Handle specific analysis types
- **Natural Language Processing**: Converts user requests to structured parameters
- **Session Management**: Maintains conversation context

## Key Features

### 1. Conversational AI Interface
```
User Input → ADK Agent → Parameter Collection → Analysis Execution → Visualization
```

**Flow:**
1. User types natural language request
2. Main agent detects analysis intent
3. Specialized agent collects required parameters
4. System executes analysis with collected parameters
5. Results displayed in interactive visualizations

### 2. Geospatial Analysis
- **Sea Level Rise Risk**: Coastal flooding analysis using elevation data
- **Urban Area Analysis**: Urban expansion tracking over time periods
- **Infrastructure Exposure**: Vulnerability assessment of infrastructure
- **Interactive Maps**: Real-time visualization with custom overlays

### 3. Topic Modeling
- **LDA (Latent Dirichlet Allocation)**: Traditional topic modeling
- **BERTopic**: Advanced topic modeling with automatic topic detection
- **File Support**: PDF, DOCX, TXT document processing
- **Visualization**: Word clouds and topic distribution charts

### 4. Data Management
- **User Authentication**: Secure login/signup system
- **Chat History**: Persistent conversation storage
- **File Upload**: Multi-format document support
- **Location Database**: Comprehensive world cities database

## Technology Stack Details

### Frontend Dependencies
```json
{
  "react": "^18.2.0",
  "vite": "^6.3.5",
  "@mui/material": "^5.14.0",
  "leaflet": "^1.9.4",
  "react-leaflet": "^4.2.1",
  "recharts": "^3.0.0",
  "react-router-dom": "^6.22.3",
  "axios": "^1.6.8"
}
```

### Backend Dependencies
```txt
fastapi
uvicorn
sqlalchemy
pydantic
python-jose[cryptography]
passlib[bcrypt]
google-adk
litellm
scikit-learn
bertopic
numpy
matplotlib
wordcloud
```

## Database Schema

### User Management
```sql
users:
  - id (Primary Key)
  - user_name
  - email (Unique)
  - hashed_password

chats:
  - id (Primary Key)
  - user_id (Foreign Key)
  - title
  - created_at

messages:
  - id (Primary Key)
  - chat_id (Foreign Key)
  - sender ('user' or 'ai')
  - content
  - created_at
```

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/signup` - User registration

### Chat Management
- `GET /chat/chats` - Get user's chats
- `POST /chat/chats` - Create new chat
- `GET /chat/chats/{id}/messages` - Get chat messages
- `POST /chat/chats/{id}/messages` - Send message

### Analysis
- `POST /analysis/sea-level-rise` - Sea level rise analysis
- `POST /analysis/urban-area-comprehensive` - Urban area analysis
- `POST /analysis/infrastructure-exposure` - Infrastructure analysis
- `POST /analysis/topic-modeling` - Topic modeling analysis

### File Management
- `POST /files/upload` - Upload files
- `GET /files/{filename}` - Download files

### Location Services
- `GET /location/countries` - Get country list
- `GET /location/cities` - Get city list
- `POST /location/geocode` - Geocode location

## ADK Agent Architecture

### Agent Hierarchy
```
Main Agent (Coordinator)
├── Sea Level Agent
├── Urban Agent
├── Infrastructure Agent
└── Topic Modeling Agent
```

### Shared Components
- **Parameter Collector**: Extracts parameters from natural language
- **Location Matcher**: Matches city/country names to database
- **Bbox Utils**: Calculates bounding boxes for analysis
- **Geospatial Tools**: Common geospatial operations

## Analysis Workflows

### 1. Sea Level Rise Analysis
```
Input: Country, City, Year, Threshold
Process: Google Earth Engine elevation analysis
Output: Risk map with affected areas
```

### 2. Urban Area Analysis
```
Input: Country, City, Start Year, End Year, Threshold
Process: Time-series urban expansion analysis
Output: Growth charts and expansion maps
```

### 3. Infrastructure Exposure
```
Input: Country, City, Year, Threshold
Process: Infrastructure vulnerability assessment
Output: Exposure maps and risk metrics
```

### 4. Topic Modeling
```
Input: Documents (text/files), Method (LDA/BERTopic), Parameters
Process: Topic extraction and analysis
Output: Topics, word clouds, document assignments
```

## Security Features

### Authentication
- JWT token-based authentication
- Password hashing with bcrypt
- Token validation on each request
- Automatic token refresh

### Data Protection
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- CORS configuration for cross-origin requests
- Error handling without sensitive data exposure

### File Security
- File type validation
- Size limits for uploads
- Secure file storage
- Access control for uploaded files

## Performance Optimizations

### Frontend
- React component memoization
- Lazy loading for large components
- Efficient state management
- Optimized re-rendering

### Backend
- FastAPI async/await for concurrent requests
- Database connection pooling
- Efficient query optimization
- Caching for frequently accessed data

### Analysis
- Parallel processing for large datasets
- Incremental analysis for time-series data
- Optimized geospatial operations
- Memory-efficient data structures

## Deployment Considerations

### Development
- Hot reloading with Vite
- FastAPI auto-reload
- SQLite for development database
- Local file storage

### Production
- Docker containerization
- PostgreSQL for production database
- Cloud storage for files
- Load balancing for high availability
- Monitoring and logging

## Future Enhancements

### Planned Features
- Real-time collaboration
- Advanced visualization options
- Machine learning model integration
- Mobile application
- API rate limiting
- Advanced caching strategies

### Scalability
- Microservices architecture
- Message queue integration
- Distributed computing
- Cloud-native deployment
- Auto-scaling capabilities
