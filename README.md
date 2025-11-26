# Telegram University Matcher Bot

Intelligent university matching system with semantic search and Telegram integration

## 🌟 Overview

University Matcher Bot is a sophisticated matching system that connects university students based on shared interests and academic profiles using semantic search. Built with modern Python stack and deployed as a Telegram bot, this project demonstrates full-cycle development from database design to machine learning integration.

## 🚀 Features

### Core Functionality

- Smart Matching: Semantic search using FAISS index and Sentence Transformers
- Telegram Integration: Intuitive bot interface for user registration and matching
- Dynamic Profiling: Interest-based user profiles with adaptive recommendations
- Admin Dashboard: Web interface for system monitoring and user management

### Technical Highlights

- Real-time Indexing: Background tasks for continuous FAISS index updates
- Async Architecture: Full asynchronous stack with FastAPI and async database operations
- Robust Error Handling: Comprehensive error monitoring
- Secure Architecture: Environment-based configuration with sensitive data protection

## 🛠 Technology Stack

### Backend & API

FastAPI (v0.100+) - High-performance async web framework
SQLAlchemy (v2.0+) with AsyncPG - Modern ORM with async support
Alembic (v1.17+) - Database migrations

### Machine Learning

Sentence-Transformers (v5.1+) - Semantic text embeddings
FAISS-CPU - Efficient similarity search
Transformers (v4.57+) - Hugging Face integration
Numpy - Data processing

### Infrastructure

SQLite - Primary database
Docker - Containerization

## ⚡ Getting Started

### Prerequisites

- Python 3.11+
- SQLite
- Telegram Bot token (from @BotFather)

```bash
# Clone the repository
git clone https://github.com/yourusername/university-matcher-bot.git
cd university-matcher-bot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/MacOS
# .\.venv\Scripts\activate  # Windows

# Install dependencies
pip install uv
uv pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Seed initial data (optional)
python seed.py

# Start the application
python main.py
```

### Running with Docker

```bash
# Build and start services
docker-compose up --build

# Run migrations
docker-compose run app alembic upgrade head

# Seed initial data
docker-compose run app python seed.py
```

## Project Structure

```plain text
university-matcher-bot/
├── src/
│   ├── bot/                   # Telegram bot implementation
│   │   ├── dialogs/           # Dialog flows and handlers
│   │   ├── middleware/        # Bot middleware
│   │   └── setup.py           # Bot initialization
│   │
│   ├── services/
│   │   ├── matcher.py         # RAG system core logic
│   │   ├── database.py        # Database operations
│   │   └── cache.py           # Caching layer
│   │
│   ├── models/                # Database models
│   │   ├── user.py            # User model
│   │   ├── interest.py        # Interest model
│   │   └── match.py           # Match history model
│   │
│   ├── web/                   # FastAPI application
│   │   ├── app.py             # Main application entrypoint
│   │   ├── routes/            # API routes
│   │   └── admin.py           # Admin dashboard
│   │
│   └── utils/                 # Utility functions
│       ├── logger.py          # Logging configuration
│       └── config.py          # Configuration management
│
├── alembic/                   # Database migrations
├── tests/                     # Test suite
├── data/                      # ML models and datasets
├── docker/                    # Docker configurations
├── seed.py                    # Database seed script
├── main.py                    # Application entrypoint
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project configuration
├── Dockerfile                 # Docker build instructions
├── docker-compose.yml         # Docker Compose configuration
└── .env.example               # Environment template
```

## 🔗 Links & Resources

- Telegram Bot API Documentation
- FastAPI Documentation
- Sentence-Transformers Documentation
- FAISS GitHub Repository
- SQLAlchemy 2.0 Documentation
