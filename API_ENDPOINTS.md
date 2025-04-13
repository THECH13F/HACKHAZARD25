# RT-CTA API Documentation

This document provides a comprehensive guide for all available API endpoints in the Real-Time Cyber Threat Assistant (RT-CTA) application. These endpoints can be used to integrate with a React frontend application.

## Table of Contents
- [Authentication](#authentication)
- [User Profile](#user-profile)
- [Threat Analysis](#threat-analysis)
  - [Text Analysis](#text-analysis)
  - [Visual Analysis](#visual-analysis)
  - [Audio Analysis](#audio-analysis)
  - [Multimodal Analysis](#multimodal-analysis)
- [Analysis Results](#analysis-results)
- [WebSocket Notifications](#websocket-notifications)

## Base URL

All API endpoints are relative to the base URL of your deployment, e.g., `http://localhost:8000/api/`.

## Authentication

Authentication uses JWT (JSON Web Tokens).

### Login

```
POST /api/auth/login/
```

**Request body:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**React example:**
```javascript
const login = async (username, password) => {
  try {
    const response = await fetch('http://localhost:8000/api/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      // Store tokens in localStorage or state management
      localStorage.setItem('access_token', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      return data;
    } else {
      throw new Error(data.detail || 'Login failed');
    }
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};
```

### Refresh Token

```
POST /api/auth/refresh/
```

**Request body:**
```json
{
  "refresh": "your_refresh_token"
}
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**React example:**
```javascript
const refreshToken = async () => {
  try {
    const refresh = localStorage.getItem('refresh_token');
    
    const response = await fetch('http://localhost:8000/api/auth/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh }),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      localStorage.setItem('access_token', data.access);
      return data;
    } else {
      // Token expired or invalid, redirect to login
      throw new Error('Token refresh failed');
    }
  } catch (error) {
    console.error('Token refresh error:', error);
    throw error;
  }
};
```

## User Profile

### Get User Profile

```
GET /api/auth/user/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "Admin",
  "last_name": "User"
}
```

**React example:**
```javascript
const getUserProfile = async () => {
  try {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch('http://localhost:8000/api/auth/user/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.detail || 'Failed to get user profile');
    }
  } catch (error) {
    console.error('Error fetching user profile:', error);
    throw error;
  }
};
```

## Threat Analysis

### Text Analysis

```
POST /api/analyze/text/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request body:**
```json
{
  "text": "Your text content to analyze for threats",
  "session_id": 123  // Optional
}
```

**Response:**
```json
{
  "message": "Text analysis task submitted successfully",
  "task_id": "some-uuid-task-id",
  "status": "processing"
}
```

**React example:**
```javascript
const analyzeText = async (text, sessionId = null) => {
  try {
    const token = localStorage.getItem('access_token');
    
    const payload = { text };
    if (sessionId) payload.session_id = sessionId;
    
    const response = await fetch('http://localhost:8000/api/analyze/text/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.error || 'Text analysis failed');
    }
  } catch (error) {
    console.error('Error analyzing text:', error);
    throw error;
  }
};
```

### Visual Analysis

```
POST /api/analyze/visual/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request body:**
```json
{
  "image": "base64_encoded_image_data",
  "session_id": 123  // Optional
}
```

**Response:**
```json
{
  "message": "Visual analysis task submitted successfully",
  "task_id": "some-uuid-task-id",
  "status": "processing"
}
```

**React example:**
```javascript
const analyzeImage = async (imageFile, sessionId = null) => {
  try {
    const token = localStorage.getItem('access_token');
    
    // Convert image file to base64
    const reader = new FileReader();
    const base64Promise = new Promise((resolve) => {
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.readAsDataURL(imageFile);
    });
    
    const base64Image = await base64Promise;
    
    const payload = { image: base64Image };
    if (sessionId) payload.session_id = sessionId;
    
    const response = await fetch('http://localhost:8000/api/analyze/visual/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.error || 'Visual analysis failed');
    }
  } catch (error) {
    console.error('Error analyzing image:', error);
    throw error;
  }
};
```

### Audio Analysis

```
POST /api/analyze/audio/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request body:**
```json
{
  "audio": "base64_encoded_audio_data",
  "transcription": "Optional transcription of the audio",
  "session_id": 123  // Optional
}
```

**Response:**
```json
{
  "message": "Audio analysis task submitted successfully",
  "task_id": "some-uuid-task-id",
  "status": "processing"
}
```

**React example:**
```javascript
const analyzeAudio = async (audioFile, transcription = null, sessionId = null) => {
  try {
    const token = localStorage.getItem('access_token');
    
    // Convert audio file to base64
    const reader = new FileReader();
    const base64Promise = new Promise((resolve) => {
      reader.onload = () => resolve(reader.result.split(',')[1]);
      reader.readAsDataURL(audioFile);
    });
    
    const base64Audio = await base64Promise;
    
    const payload = { audio: base64Audio };
    if (transcription) payload.transcription = transcription;
    if (sessionId) payload.session_id = sessionId;
    
    const response = await fetch('http://localhost:8000/api/analyze/audio/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.error || 'Audio analysis failed');
    }
  } catch (error) {
    console.error('Error analyzing audio:', error);
    throw error;
  }
};
```

### Multimodal Analysis

```
POST /api/analyze/multimodal/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Request body:**
```json
{
  "text": "Optional text content to analyze",
  "image": "Optional base64 encoded image data",
  "audio": "Optional base64 encoded audio data",
  "transcription": "Optional transcription of the audio"
}
```

**Response:**
```json
{
  "message": "Multimodal analysis tasks submitted successfully",
  "session_id": 123,
  "tasks": [
    {"type": "text", "task_id": "task-id-1"},
    {"type": "visual", "task_id": "task-id-2"},
    {"type": "audio", "task_id": "task-id-3"}
  ],
  "status": "processing"
}
```

**React example:**
```javascript
const analyzeMultimodal = async (data) => {
  try {
    const token = localStorage.getItem('access_token');
    
    // Prepare payload with available data
    const payload = {};
    
    if (data.text) payload.text = data.text;
    
    if (data.imageFile) {
      // Convert image to base64
      const reader = new FileReader();
      const imagePromise = new Promise((resolve) => {
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(data.imageFile);
      });
      payload.image = await imagePromise;
    }
    
    if (data.audioFile) {
      // Convert audio to base64
      const reader = new FileReader();
      const audioPromise = new Promise((resolve) => {
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.readAsDataURL(data.audioFile);
      });
      payload.audio = await audioPromise;
      
      if (data.transcription) payload.transcription = data.transcription;
    }
    
    const response = await fetch('http://localhost:8000/api/analyze/multimodal/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    
    const responseData = await response.json();
    
    if (response.ok) {
      return responseData;
    } else {
      throw new Error(responseData.error || 'Multimodal analysis failed');
    }
  } catch (error) {
    console.error('Error with multimodal analysis:', error);
    throw error;
  }
};
```

## Analysis Results

### Get Results

```
GET /api/results/
GET /api/results/{session_id}/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "session": {
    "id": 123,
    "session_type": "multimodal",
    "start_time": "2025-04-12T14:30:22Z",
    "end_time": "2025-04-12T14:31:05Z",
    "status": "completed"
  },
  "threats": [
    {
      "id": 456,
      "threat_level": "HIGH",
      "description": "Potential phishing attempt detected",
      "source_type": "text",
      "confidence_score": 0.95,
      "created_at": "2025-04-12T14:30:45Z"
    }
  ]
}
```

**React example:**
```javascript
const getAnalysisResults = async (sessionId = null) => {
  try {
    const token = localStorage.getItem('access_token');
    
    const url = sessionId 
      ? `http://localhost:8000/api/results/${sessionId}/`
      : 'http://localhost:8000/api/results/';
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.error || 'Failed to fetch analysis results');
    }
  } catch (error) {
    console.error('Error fetching analysis results:', error);
    throw error;
  }
};
```

## WebSocket Notifications

The application uses WebSockets to provide real-time threat notifications.

### Connect to WebSocket

```
ws://localhost:8000/ws/notifications/
```

**React example using useEffect hook:**
```javascript
import { useEffect, useState } from 'react';

const ThreatNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [socket, setSocket] = useState(null);
  
  useEffect(() => {
    // Connect to WebSocket
    const userId = 1; // Get this from your authentication state
    const wsUrl = `ws://localhost:8000/ws/notifications/?token=${localStorage.getItem('access_token')}`;
    const newSocket = new WebSocket(wsUrl);
    
    newSocket.onopen = () => {
      console.log('WebSocket connection established');
    };
    
    newSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      if (data.type === 'threat_notification') {
        setNotifications(prev => [...prev, data.data]);
      }
    };
    
    newSocket.onclose = () => {
      console.log('WebSocket connection closed');
    };
    
    setSocket(newSocket);
    
    // Clean up WebSocket connection
    return () => {
      if (newSocket) {
        newSocket.close();
      }
    };
  }, []);
  
  return (
    <div>
      <h2>Threat Notifications</h2>
      <ul>
        {notifications.map((notification, index) => (
          <li key={index}>
            <strong>{notification.level}:</strong> {notification.description}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ThreatNotifications;
```

## Dashboard Data

For the dashboard, you can access threat data:

```
GET /dashboard/data/
```

**Headers:**
```
Authorization: Bearer your_access_token
```

**Response:**
```json
{
  "recent_threats": [
    {
      "id": 123,
      "threat_level": "HIGH",
      "description": "Suspicious network activity detected",
      "source_type": "text",
      "timestamp": "2025-04-12T14:30:45Z"
    }
  ],
  "threat_stats": {
    "total": 10,
    "by_level": {
      "LOW": 2,
      "MEDIUM": 3,
      "HIGH": 4,
      "CRITICAL": 1
    },
    "by_source": {
      "text": 5,
      "visual": 3,
      "audio": 2
    }
  }
}
```

**React example:**
```javascript
const getDashboardData = async () => {
  try {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch('http://localhost:8000/dashboard/data/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });
    
    const data = await response.json();
    
    if (response.ok) {
      return data;
    } else {
      throw new Error(data.error || 'Failed to fetch dashboard data');
    }
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    throw error;
  }
};
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- 200: Success
- 400: Bad Request (invalid parameters)
- 401: Unauthorized (invalid or expired token)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Your React application should handle these status codes appropriately. 