# DataGround Component Relationship Diagram

## System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        User[User Interface]
    end

    subgraph "Frontend Layer (React)"
        subgraph "Authentication"
            Login[LoginPage]
            Signup[SignupPage]
        end
        
        subgraph "Main Application"
            App[App.jsx]
            ChatPage[ChatPage.jsx]
        end
        
        subgraph "Chat Components"
            ChatSidebar[ChatSidebar.jsx]
            ChatWindow[ChatWindow.jsx]
        end
        
        subgraph "Analysis Components"
            MapSidebar[MapSidebar.jsx]
            MapDisplay[MapDisplay.jsx]
            TopicModeling[TopicModeling.jsx]
            UrbanCharts[UrbanAreaCharts.jsx]
            Infrastructure[InfrastructureExposure.jsx]
        end
        
        subgraph "Utility Components"
            FileUpload[FileUpload.jsx]
            ErrorBoundary[ErrorBoundary.jsx]
        end
    end

    subgraph "Backend Layer (FastAPI)"
        subgraph "API Endpoints"
            AuthAPI[auth.py]
            ChatAPI[chat.py]
            AnalysisAPI[analysis.py]
            FileAPI[file_upload.py]
            LocationAPI[location.py]
        end
        
        subgraph "Core Services"
            ADKChat[adk_chat.py]
            TopicModels[topic_models.py]
            Database[database.py]
        end
        
        subgraph "ADK Agent System"
            MainAgent[main_agent/]
            SeaLevelAgent[sea_level_agent/]
            UrbanAgent[urban_agent/]
            InfrastructureAgent[infrastructure_agent/]
            TopicAgent[topic_modeling_agent/]
            SharedUtils[shared/utils/]
        end
    end

    subgraph "Data Layer"
        SQLite[(SQLite Database)]
        Files[(File Storage)]
        WorldCities[(World Cities DB)]
    end

    subgraph "External Services"
        GEE[Google Earth Engine]
        ADK[Google ADK]
    end

    %% User interactions
    User --> Browser
    Browser --> Login
    Browser --> Signup
    Browser --> ChatPage

    %% Frontend component relationships
    App --> Login
    App --> Signup
    App --> ChatPage
    ChatPage --> ChatSidebar
    ChatPage --> ChatWindow
    ChatPage --> MapSidebar
    ChatPage --> MapDisplay
    ChatPage --> TopicModeling
    ChatPage --> UrbanCharts
    ChatPage --> Infrastructure
    ChatPage --> FileUpload
    App --> ErrorBoundary

    %% Frontend to Backend API calls
    Login -.->|"POST /auth/login"| AuthAPI
    Signup -.->|"POST /auth/signup"| AuthAPI
    ChatSidebar -.->|"GET /chat/chats"| ChatAPI
    ChatWindow -.->|"POST /chat/chats/messages"| ChatAPI
    MapSidebar -.->|"POST /analysis"| AnalysisAPI
    FileUpload -.->|"POST /files/upload"| FileAPI
    MapDisplay -.->|"GET /location"| LocationAPI

    %% Backend internal relationships
    ChatAPI --> ADKChat
    AnalysisAPI --> TopicModels
    ADKChat --> MainAgent
    MainAgent --> SeaLevelAgent
    MainAgent --> UrbanAgent
    MainAgent --> InfrastructureAgent
    MainAgent --> TopicAgent
    MainAgent --> SharedUtils
    SeaLevelAgent --> SharedUtils
    UrbanAgent --> SharedUtils
    InfrastructureAgent --> SharedUtils
    TopicAgent --> SharedUtils

    %% Database connections
    AuthAPI --> SQLite
    ChatAPI --> SQLite
    FileAPI --> Files
    LocationAPI --> WorldCities

    %% External service connections
    AnalysisAPI --> GEE
    ADKChat --> ADK
    MainAgent --> ADK
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant C as ChatPage
    participant CW as ChatWindow
    participant API as ChatAPI
    participant ADK as ADKChat
    participant MA as MainAgent
    participant SA as SpecializedAgent
    participant A as AnalysisAPI
    participant GEE as Google Earth Engine
    participant M as MapDisplay

    U->>CW: Types message
    CW->>API: POST chat messages
    API->>ADK: Process with ADK
    ADK->>MA: Call main agent
    MA->>SA: Delegate to specialized agent
    
    alt Parameter Collection Needed
        SA->>MA: Request more parameters
        MA->>ADK: Generate question
        ADK->>API: Return question
        API->>CW: Display question
        CW->>U: Show question
        U->>CW: Provide answer
        Note over CW,SA: Repeat until all parameters collected
    end
    
    SA->>MA: All parameters ready
    MA->>ADK: Execute analysis
    ADK->>A: Call analysis API
    A->>GEE: Process geospatial data
    GEE->>A: Return results
    A->>ADK: Analysis complete
    ADK->>API: Return results
    API->>CW: Display results
    CW->>M: Update map visualization
    M->>U: Show interactive map
```

## Component Dependencies

### Frontend Dependencies
```mermaid
graph TD
    App --> ChatPage
    App --> LoginPage
    App --> SignupPage
    App --> ErrorBoundary
    
    ChatPage --> ChatSidebar
    ChatPage --> ChatWindow
    ChatPage --> MapSidebar
    ChatPage --> MapDisplay
    ChatPage --> TopicModeling
    ChatPage --> UrbanAreaCharts
    ChatPage --> InfrastructureExposure
    ChatPage --> FileUpload
    
    ChatSidebar --> api.js
    ChatWindow --> api.js
    MapSidebar --> api.js
    MapDisplay --> api.js
    TopicModeling --> api.js
    UrbanAreaCharts --> api.js
    InfrastructureExposure --> api.js
    FileUpload --> api.js
```

### Backend Dependencies
```mermaid
graph TD
    main.py --> auth.py
    main.py --> chat.py
    main.py --> analysis.py
    main.py --> file_upload.py
    main.py --> location.py
    
    chat.py --> adk_chat.py
    chat.py --> database.py
    chat.py --> models.py
    
    adk_chat.py --> main_agent
    adk_chat.py --> shared/utils
    
    main_agent --> sea_level_agent
    main_agent --> urban_agent
    main_agent --> infrastructure_agent
    main_agent --> topic_modeling_agent
    
    analysis.py --> topic_models.py
    analysis.py --> utils.py
    
    auth.py --> database.py
    auth.py --> models.py
    auth.py --> schemas.py
```

## Key Integration Points

### 1. ADK Agent Integration
- **Entry Point**: `adk_chat.py` receives user messages
- **Coordination**: `main_agent` coordinates conversation flow
- **Specialization**: Domain-specific agents handle analysis types
- **Parameter Collection**: Interactive parameter gathering through conversation

### 2. Analysis Pipeline
- **Input**: User parameters from ADK agents
- **Processing**: Google Earth Engine for geospatial analysis
- **Topic Modeling**: LDA/BERTopic for document analysis
- **Output**: Interactive visualizations and charts

### 3. Data Persistence
- **User Management**: Authentication and user profiles
- **Chat History**: Persistent conversation storage
- **File Storage**: Uploaded documents and datasets
- **Location Data**: World cities database for geocoding

### 4. Real-time Communication
- **WebSocket**: Real-time chat updates (if implemented)
- **API Polling**: Regular updates for analysis progress
- **State Management**: React state for UI updates
- **Error Handling**: Comprehensive error boundaries and logging
