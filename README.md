# CodeMentorAI – Backend Microservices

A production-grade microservices backend system powering an AI-powered coding mentor platform. Built with Django, FastAPI, and Docker following real-world backend engineering and security practices.

## 🏗️ Architecture Overview

CodeMentorAI follows a microservices architecture where each service is independent and responsible for a specific domain:

```
CodeMentorAI-Services/
├── auth-service/               # Authentication & Authorization
├── profile-service/            # User profiles & data
├── problem-service/            # Coding problems & AI review
├── execution-service/          # Code execution engine
├── ai-mentor-service/          # AI mentor logic & feedback
├── pair-programming-service/   # Real-time pair programming
├── resume-ai-service/          # AI-based resume analysis
├── docker-compose.yml
├── .gitignore
└── README.md
```

## 🛠️ Tech Stack

**Backend Framework:**
- Python Django and Django REST Framework
- FastAPI for high-performance services

**Infrastructure:**
- Docker and Docker Compose
- REST APIs with Microservices architecture
- Celery for background task processing
- WebSockets for real-time features

**AI Integration:**
- LLM-based feedback and analysis
- AI-powered problem review
- Resume parsing and enhancement

## 📦 Services Description

### Auth Service (Django)
- User authentication and authorization
- OAuth-based login
- JWT token handling
- Event publishing for other services

### Profile Service (Django)
- User profile management
- Synchronization with authentication events
- Storage of user-related metadata

### Problem Service (Django)
- Coding problem management
- Submission and attempt handling
- AI-based code review and scoring
- Background processing using Celery

### Execution Service (FastAPI)
- Secure code execution
- Language-agnostic execution workflow
- Communication with external judge API

### AI Mentor Service (Django)
- AI-driven mentoring and feedback
- Code evaluation and improvement suggestions
- Task-based background processing

### Pair Programming Service (Django + Channels)
- Real-time collaboration
- WebSocket-based communication
- Shared coding sessions

### Resume AI Service (Django)
- Resume upload and parsing (PDF and DOCX)
- AI-powered resume feedback
- Skill and content analysis

## ⚙️ Environment Variables

Each service uses its own `.env` file, which is not committed to the repository.

Example:
```
auth-service/.env
problem-service/.env
execution-service/.env
ai-mentor-service/.env
pair-programming-service/.env
resume-ai-service/.env
```

Refer to the `.env.example` files inside each service directory to configure environment variables.

## 🚀 Getting Started

### Prerequisites
- Docker
- Docker Compose

### Running the Project

Start all services:

```bash
docker-compose up --build
```

Each service runs independently and communicates with other services through APIs.

## 📌 Why This Project Matters

This project demonstrates:
- Real-world backend engineering practices
- Clean microservices design
- Secure configuration management
- AI integration in backend systems
- Docker-based development workflow

## 📄 License

This project is intended for learning, demonstration, and portfolio purposes.
