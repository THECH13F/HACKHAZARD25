# RT-CTA API Developer Guide

This document provides an in-depth explanation of all API endpoints in the Real-Time Cyber Threat Assistant (RT-CTA) application, including implementation details, technical background, and integration guidance for React frontend developers.

## System Architecture Overview

The RT-CTA system uses a Django-based backend with the following components:
- **Django REST Framework**: Provides the RESTful API endpoints
- **Channels**: Handles WebSocket connections for real-time notifications
- **Celery**: Manages asynchronous task processing for threat analysis
- **Groq API**: Powers the AI inference for threat detection
- **JWT Authentication**: Secures API endpoints

## API Authentication

### JWT Authentication Flow

The system uses JSON Web Tokens (JWT) for authentication, with a token-based approach that includes:
- Access tokens (short-lived, 5 minutes by default)
- Refresh tokens (longer-lived, 24 hours by default)

#### Login Endpoint

```
POST /api/auth/login/
```

**Implementation Details:**
- Uses `TokenObtainPairView` from `rest_framework_simplejwt`
- Authenticates against Django's user model
- Returns both access and refresh tokens on successful authentication
- Frontend should store these tokens securely (localStorage, secure cookie, or state management)

**Request Processing:**
1. Validates username and password
2. Queries the database for the user
3. Verifies password using Django's password hashing
4. Generates JWT tokens with user claims

**Usage Notes:**
- Do not expose tokens in URLs or log them
- Store refresh tokens securely
- Implement proper token refresh mechanics in your frontend

#### Token Refresh Endpoint

```
POST /api/auth/refresh/
```

**Implementation Details:**
- Uses `TokenRefreshView` from `rest_framework_simplejwt`
- Takes a valid refresh token and returns a new access token
- Should be called when access token expires (typically before making API calls)

**Request Processing:**
1. Validates the refresh token signature and expiry
2. If valid, generates a new access token
3. Returns the new access token in the response

**Integration Tips:**
- Implement an interceptor in your frontend to automatically refresh tokens
- For example, with axios:

```javascript
// Axios interceptor for automatic token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried refreshing yet
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post('/api/auth/refresh/', {
          refresh: refreshToken
        });
        
        // Store the new access token
        localStorage.setItem('access_token', response.data.access);
        
        // Update the authorization header
        originalRequest.headers['Authorization'] = 
          `Bearer ${response.data.access}`;
          
        // Retry the original request
        return axios(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);
```

## User Management

### User Profile Endpoint

```
GET /api/auth/user/
```

**Implementation Details:**
- Uses a custom `UserProfileView` that extends `APIView`
- Protected by `IsAuthenticated` permission class
- Returns serialized details of the authenticated user

**Request Processing:**
1. Extracts user ID from JWT token
2. Retrieves user object from database
3. Serializes user data using `UserSerializer`

**Response Fields:**
- `id`: User's unique identifier
- `username`: User's login name
- `email`: User's email address
- `first_name`: User's first name
- `last_name`: User's last name

**Data Security Considerations:**
- Only returns non-sensitive user data
- Password and security data are never exposed
- User ID mapping is handled server-side

## Threat Analysis APIs

The threat analysis endpoints are the core of the RT-CTA system, allowing different types of data to be submitted for threat detection. All analysis endpoints:

1. Accept multimodal inputs (text, visual, audio)
2. Process inputs asynchronously using Celery tasks
3. Return task IDs for tracking analysis progress
4. Store analysis results in the database
5. Send real-time notifications via WebSockets when threats are detected

### Common Implementation Pattern

All analysis endpoints follow a similar pattern:
1. Validate incoming request data with a serializer
2. Create an analysis session if needed or use an existing one
3. Submit analysis task to Celery queue
4. Return task ID and status information

### Text Analysis

```
POST /api/analyze/text/
```

**Implementation Details:**
- Extends `BaseAnalysisView` which handles common logic
- Uses `TextAnalysisRequestSerializer` for input validation
- Processes text through the Groq API using the `process_text_analysis` Celery task

**Request Processing:**
1. Validates text input and optional session ID
2. Either creates new session or uses existing session
3. Submits text to Celery task for processing
4. Task calls Groq API with text input
5. Analyzes the API response for threats
6. If threats detected, creates `TextThreatDetection` record
7. Sends WebSocket notification to the user's notification channel

**Groq API Integration:**
The text is analyzed using:
- Groq's `llama3-70b-8192` model by default
- Prompt template designed for security threat detection
- Response parsing to extract threat level, confidence, etc.

**Performance Considerations:**
- Text processing is typically very fast (100-300ms)
- Groq API calls are made with a timeout of 10 seconds
- Rate limiting may apply based on your Groq API plan

### Visual Analysis

```
POST /api/analyze/visual/
```

**Implementation Details:**
- Similar to text analysis, but handles image data
- Uses `VisualAnalysisRequestSerializer` for input validation
- Processes images through the `process_visual_analysis` Celery task

**Request Processing:**
1. Accepts base64-encoded image data
2. Decodes and validates the image
3. Stores image temporarily for analysis
4. Performs threat detection using visual analysis algorithms
5. Creates `VisualThreatDetection` records if threats are found
6. Can include bounding boxes for detected threats

**Integration Notes:**
- Images should be reasonably sized (max 5MB recommended)
- Base64 encoding increases size by ~33%
- Consider resizing large images before sending

### Audio Analysis

```
POST /api/analyze/audio/
```

**Implementation Details:**
- Handles audio data and optional transcription
- Uses `AudioAnalysisRequestSerializer` for input validation
- Processes audio through the `process_audio_analysis` Celery task

**Request Processing:**
1. Accepts base64-encoded audio data
2. If transcription is provided, uses it directly
3. Otherwise, may perform speech-to-text conversion
4. Analyzes both audio patterns and transcribed content
5. Creates `AudioThreatDetection` records if threats are detected

**Audio Processing Notes:**
- Supports common audio formats (MP3, WAV, etc.)
- Recommended maximum duration: 60 seconds
- Audio analysis may consider tone, patterns, and content

### Multimodal Analysis

```
POST /api/analyze/multimodal/
```

**Implementation Details:**
- Allows submission of multiple input types in a single request
- Uses `MultimodalAnalysisRequestSerializer` for input validation
- Processes each input type through the respective Celery tasks

**Request Processing:**
1. Creates a single multimodal analysis session
2. Accepts any combination of text, image, and audio inputs
3. Processes each input type through its specialized pipeline
4. Returns a single session ID and multiple task IDs
5. Results are correlated through the session ID

**Multimodal Advantages:**
- Allows correlation of threats across input types
- May detect sophisticated threats that span multiple modalities
- More comprehensive security analysis

**Integration Example:**
```javascript
// React component for multimodal analysis form
const MultimodalAnalysisForm = () => {
  const [text, setText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Collect all available inputs
      const data = {};
      if (text) data.text = text;
      if (imageFile) data.imageFile = imageFile;
      if (audioFile) data.audioFile = audioFile;
      
      // Submit for analysis
      const response = await analyzeMultimodal(data);
      setResult(response);
      
      // You can now poll for results using the session ID
      // or wait for WebSocket notifications
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label>Text to analyze:</label>
        <textarea 
          value={text} 
          onChange={(e) => setText(e.target.value)}
          className="form-control"
        />
      </div>
      
      <div className="form-group">
        <label>Image file:</label>
        <input 
          type="file" 
          accept="image/*"
          onChange={(e) => setImageFile(e.target.files[0])}
          className="form-control"
        />
      </div>
      
      <div className="form-group">
        <label>Audio file:</label>
        <input 
          type="file" 
          accept="audio/*"
          onChange={(e) => setAudioFile(e.target.files[0])}
          className="form-control"
        />
      </div>
      
      <button 
        type="submit" 
        disabled={loading || (!text && !imageFile && !audioFile)}
        className="btn btn-primary"
      >
        {loading ? 'Analyzing...' : 'Analyze'}
      </button>
      
      {result && (
        <div className="mt-4">
          <h4>Analysis submitted:</h4>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </form>
  );
};
```

## Results & Analysis Data

### Analysis Results Endpoint

```
GET /api/results/
GET /api/results/{session_id}/
```

**Implementation Details:**
- Uses `AnalysisResultView` that extends `APIView`
- Protected by `IsAuthenticated` permission class
- Returns threat detections and session details

**Request Processing:**
1. If session ID is provided, fetches that specific session
2. Otherwise, retrieves the user's latest session
3. Verifies the session belongs to the authenticated user
4. Retrieves all threat detections for the session
5. Serializes session and threats data

**Response Structure:**
- Session details (ID, type, start/end times, status)
- List of detected threats with detailed information
- Each threat includes level, description, confidence, etc.

**Polling Strategy:**
For long-running analyses, the frontend can poll this endpoint:
```javascript
const pollResults = async (sessionId, interval = 2000, maxAttempts = 30) => {
  let attempts = 0;
  
  const checkResults = async () => {
    attempts++;
    
    try {
      const results = await getAnalysisResults(sessionId);
      
      // Check if analysis is complete
      if (results.session.status === 'completed' || 
          results.session.status === 'failed' ||
          attempts >= maxAttempts) {
        return results;
      }
      
      // Continue polling
      return new Promise(resolve => {
        setTimeout(async () => {
          resolve(await checkResults());
        }, interval);
      });
    } catch (error) {
      console.error('Error polling results:', error);
      throw error;
    }
  };
  
  return checkResults();
};
```

## Real-Time Notifications

### WebSocket Connection

The RT-CTA system uses Django Channels to provide real-time WebSocket notifications for threat detections.

**Implementation Details:**
- WebSocket endpoint: `ws://localhost:8000/ws/notifications/`
- Requires authentication token in the connection URL
- Creates user-specific notification groups

**Connection Process:**
1. Frontend connects to WebSocket with token
2. Backend authenticates the connection
3. User is subscribed to their notification group
4. Analysis processes send real-time updates to this group
5. Frontend receives and displays notifications

**WebSocket Message Types:**
- `threat_notification`: New threat detected
- `session_update`: Analysis session status changed
- `system_alert`: System-level notifications

**React Implementation Example:**
```javascript
// React hook for WebSocket threat notifications
const useThreatNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef(null);
  
  useEffect(() => {
    // Get the user's token
    const token = localStorage.getItem('access_token');
    if (!token) return;
    
    // Connect to the WebSocket
    const socket = new WebSocket(
      `ws://localhost:8000/ws/notifications/?token=${token}`
    );
    
    socket.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };
    
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'threat_notification') {
        // Add new notification to state
        setNotifications(prev => [data.data, ...prev]);
        
        // Optionally trigger browser notification
        if (Notification.permission === 'granted') {
          new Notification('Security Threat Detected', {
            body: `${data.data.level} threat: ${data.data.description}`,
            icon: '/path/to/notification-icon.png'
          });
        }
      }
    };
    
    socket.onclose = () => {
      console.log('WebSocket disconnected');
      setConnected(false);
    };
    
    socketRef.current = socket;
    
    // Clean up on unmount
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, []);
  
  return { notifications, connected };
};
```

## Dashboard Data API

The dashboard data API provides aggregated threat statistics and recent threats for display in the UI.

```
GET /dashboard/data/
```

**Implementation Details:**
- Implemented in `core_views.threat_data` view
- Aggregates threat data for the authenticated user
- Returns counts, distributions, and recent threats

**Request Processing:**
1. Authenticates the user
2. Queries threat detections for the user
3. Aggregates counts by threat level and source type
4. Retrieves most recent threat detections
5. Formats data for dashboard display

**Response Structure:**
- Recent threats list with core details
- Total threat count
- Distribution by threat level (LOW, MEDIUM, HIGH, CRITICAL)
- Distribution by source type (text, visual, audio)

**Integration with Charts:**
The data is structured to be easily integrated with chart libraries:

```javascript
// Example with Chart.js
const DashboardCharts = ({ dashboardData }) => {
  useEffect(() => {
    if (!dashboardData) return;
    
    // Threat level distribution chart
    const levelCtx = document.getElementById('levelChart').getContext('2d');
    new Chart(levelCtx, {
      type: 'pie',
      data: {
        labels: Object.keys(dashboardData.threat_stats.by_level),
        datasets: [{
          data: Object.values(dashboardData.threat_stats.by_level),
          backgroundColor: [
            '#28a745', // LOW - Green
            '#ffc107', // MEDIUM - Yellow
            '#fd7e14', // HIGH - Orange
            '#dc3545'  // CRITICAL - Red
          ]
        }]
      }
    });
    
    // Source type distribution chart
    const sourceCtx = document.getElementById('sourceChart').getContext('2d');
    new Chart(sourceCtx, {
      type: 'bar',
      data: {
        labels: Object.keys(dashboardData.threat_stats.by_source),
        datasets: [{
          label: 'Threats by Source',
          data: Object.values(dashboardData.threat_stats.by_source),
          backgroundColor: [
            '#007bff', // text - Blue
            '#6f42c1', // visual - Purple
            '#20c997'  // audio - Teal
          ]
        }]
      }
    });
  }, [dashboardData]);
  
  if (!dashboardData) return <div>Loading...</div>;
  
  return (
    <div className="dashboard-charts">
      <div className="chart-container">
        <h3>Threats by Severity</h3>
        <canvas id="levelChart" width="300" height="300"></canvas>
      </div>
      
      <div className="chart-container">
        <h3>Threats by Source</h3>
        <canvas id="sourceChart" width="400" height="200"></canvas>
      </div>
    </div>
  );
};
```

## Administration APIs

In addition to the standard API endpoints, the system includes Django Admin functionality at `/admin/` that provides:
- User management
- Session and threat monitoring
- System configuration

These admin functionalities are not directly exposed as API endpoints but are available to superusers through the Django Admin interface.

## Error Handling

All API endpoints implement comprehensive error handling with appropriate HTTP status codes:

- **400 Bad Request**: Invalid input data
- **401 Unauthorized**: Missing or invalid authentication
- **403 Forbidden**: Authentication valid but insufficient permissions
- **404 Not Found**: Resource doesn't exist
- **500 Internal Server Error**: Server-side error

**Frontend Error Handling Example:**
```javascript
// React error handling hook
const useApiRequest = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const apiRequest = async (requestFn, ...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await requestFn(...args);
      setLoading(false);
      return result;
    } catch (err) {
      setLoading(false);
      
      // Handle different error types
      if (err.response) {
        // Server responded with error status
        switch (err.response.status) {
          case 401:
            setError('Authentication required. Please log in.');
            // Redirect to login page
            break;
          case 403:
            setError('You do not have permission to perform this action.');
            break;
          case 404:
            setError('The requested resource was not found.');
            break;
          case 400:
            setError(`Invalid request: ${err.response.data.detail || JSON.stringify(err.response.data)}`);
            break;
          case 500:
            setError('Server error. Please try again later.');
            break;
          default:
            setError(`Error: ${err.response.status}`);
        }
      } else if (err.request) {
        // Request made but no response received
        setError('No response from server. Please check your connection.');
      } else {
        // Error setting up the request
        setError(`Request error: ${err.message}`);
      }
      
      throw err;
    }
  };
  
  return { apiRequest, loading, error };
};
```

## Technical Performance Considerations

When integrating with the RT-CTA API, consider the following performance aspects:

1. **Token Management**: Implement proper token refresh mechanics
2. **File Sizes**: 
   - Image uploads: Keep under 5MB
   - Audio uploads: Keep under 10MB or 60 seconds
   - Text: No practical limits, but very large texts may be slow to process
3. **Processing Times**:
   - Text analysis: ~100-300ms
   - Image analysis: ~500ms-2s
   - Audio analysis: ~1-5s depending on length
   - Multimodal: Sum of individual processing times
4. **Polling vs. WebSockets**:
   - Use WebSockets for real-time updates
   - Use polling as a fallback when WebSockets aren't available
   - Recommended polling interval: 2-5 seconds
5. **Backend Resource Usage**:
   - Groq API calls consume tokens based on your plan
   - Celery tasks consume server CPU and memory
   - File uploads consume temporary storage

## Security Best Practices

When implementing a frontend for the RT-CTA API:

1. **Token Storage**:
   - Store tokens in memory for SPAs when possible
   - If using localStorage, implement additional safeguards
   - Consider HttpOnly cookies for refresh tokens
2. **Content Security Policy**:
   - Implement CSP headers to prevent XSS attacks
   - Restrict WebSocket connections to trusted origins
3. **Sensitive Data**:
   - Don't log or store analysis results client-side unnecessarily
   - Clear sensitive data when no longer needed
4. **Input Validation**:
   - Validate inputs before sending to the API
   - Limit file sizes and types client-side
5. **Error Handling**:
   - Don't expose detailed error messages to end users
   - Log errors for debugging but sanitize sensitive information

## Implementation Roadmap for Frontend Developers

When integrating the RT-CTA API into your React application, follow this recommended approach:

1. **Authentication Implementation**:
   - Set up login and token storage
   - Implement token refresh
   - Create protected routes
2. **Core API Services**:
   - Create service modules for each API category
   - Implement error handling
   - Set up WebSocket connection
3. **UI Components**:
   - Build input forms for each analysis type
   - Create threat notification display
   - Design dashboard with statistics
4. **Testing**:
   - Test with sample data
   - Verify WebSocket notifications
   - Test token refresh
5. **Production Readiness**:
   - Optimize bundle size
   - Implement lazy loading
   - Add error boundaries
   - Set up monitoring

By following this implementation guide, you'll create a robust frontend application that effectively utilizes all the capabilities of the RT-CTA API. 