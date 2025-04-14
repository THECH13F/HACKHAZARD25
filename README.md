# Real-Time Cyber Threat Assistant (RT-CTA)

A multimodal, AI-powered application that monitors and detects cybersecurity threats in real time by analyzing multiple data inputs using Groq's ultra-fast inference capabilities.

## Features

- **Multimodal Input Analysis**
  - Visual Module: Captures and analyzes images/screen recordings
  - Audio Module: Processes audio for threat detection
  - Text Module: Analyzes logs and chat inputs
  
- **Real-Time Inference with Groq**
  - Low-latency performance
  - Optimized machine learning models
  
- **Interactive Dashboard**
  - Real-time threat monitoring
  - Alert system
  - AI Copilot features

## Prerequisites

- Python 3.8+
- PostgreSQL
- Redis
- Groq API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/THECH13F/HACKHAZARD25.git
cd rt-cta
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Update the variables with your configuration

5. Initialize the database:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Start the development server:
```bash
python manage.py runserver
```

## Project Structure

- `core/`: Core functionality and shared components
- `visual/`: Visual analysis module
- `audio/`: Audio analysis module
- `text_analysis/`: Text analysis module
- `api/`: REST API endpoints

## API Documentation

- Swagger UI: `/docs/`
- ReDoc: `/redoc/`

## Development

1. Make sure all tests pass:
```bash
python manage.py test
```

2. Start Celery worker:
```bash
celery -A rt_cta worker -l info
```

3. Start Redis:
```bash
wsl -d Ubuntu -e sudo service redis-server start
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
