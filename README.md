# Book Management Agent

Intelligent book management system with RAG (Retrieval-Augmented Generation) capabilities, user management, and document handling.

## Features

### 📚 Book Management
- **CRUD Operations**: Create, read, update, delete books
- **Book Reviews**: Add and view book reviews with ratings
- **AI Summaries**: Generate book summaries using LLaMA 3
- **Recommendations**: Get book recommendations by genre

### 🔍 RAG Pipeline
- **Semantic Search**: Search books using natural language queries
- **Vector Embeddings**: Uses sentence-transformers for book content indexing
- **Automatic Indexing**: Books are indexed when created/updated/reviewed
- **Similarity Matching**: Cosine similarity for relevant results

### 👥 User Management
- **Authentication**: JWT-based login/signup system
- **Role-Based Access**: Admin-only endpoints for user management
- **User CRUD**: Create, update, delete users (admin only)
- **Role Assignment**: Assign roles to users

### 📄 Document Management
- **File Upload**: Upload documents with size tracking
- **File Download**: Download uploaded documents
- **S3 Integration**: Conditional AWS S3 storage for production
- **Local Development**: Simple file handling for development

### 🧪 Testing
- **Unit Tests**: Comprehensive pytest test suite
- **Mock Database**: Tests run without database dependencies
- **API Coverage**: All endpoints tested

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register new user |
| POST | `/auth/login` | User login |
| POST | `/auth/create-admin` | Create admin user |
| POST | `/auth/logout` | User logout |

### Books
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/books` | Create new book |
| GET | `/books` | List all books |
| GET | `/books/{id}` | Get book by ID |
| PUT | `/books/{id}` | Update book (auth required) |
| DELETE | `/books/{id}` | Delete book (auth required) |
| POST | `/books/{id}/generate-summary` | Generate AI summary |

### Reviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/books/{id}/reviews` | Add book review |
| GET | `/books/{id}/reviews` | Get book reviews |
| GET | `/books/{id}/summary` | Get review summary |

### Search & RAG
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/search` | Semantic book search |
| POST | `/reindex-all` | Reindex all books |
| POST | `/books/{id}/reindex` | Reindex specific book |
| GET | `/debug/embeddings` | Debug embeddings store |

### User Management (Admin Only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/users/` | Create user |
| GET | `/admin/users/` | List users |
| PUT | `/admin/users/{id}` | Update user |
| DELETE | `/admin/users/{id}` | Delete user |
| GET | `/admin/users/roles` | List roles |
| POST | `/admin/users/roles` | Create role |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload document |
| GET | `/documents/` | List documents |
| GET | `/documents/{id}/download` | Download document |
| DELETE | `/documents/{id}` | Delete document (auth required) |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/recommendations` | Get book recommendations |
| POST | `/generate-summary` | Generate content summary |

## Setup

### Prerequisites
- Python 3.8+
- PostgreSQL database
- OpenRouter API key (for LLaMA 3)

### Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd book_mgmt_agent
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Configuration**
Create `.env` file:
```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=book_mgmt
DB_USER=your_user
DB_PASSWORD=your_password

# OpenRouter (for AI features)
OPENROUTER_API_KEY=your_openrouter_key

# AWS S3 (Production only)
USE_S3=false
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
S3_BUCKET_NAME=your_bucket_name
AWS_REGION=us-east-1
```

4. **Database Setup**
```bash
# Create database tables
python -c "from app.database import engine, Base; from app.models import *; import asyncio; asyncio.run(Base.metadata.create_all(bind=engine.sync_engine))"

# Add file_size column (if needed)
python add_file_size.py
```

5. **Run Application**
```bash
uvicorn app.main:app --reload
```

## Development vs Production

### Development (Default)
- **File Storage**: Local (metadata only)
- **S3**: Disabled
- **Downloads**: Placeholder files with metadata
- **Dependencies**: Minimal (no boto3 required)

### Production
Set in `.env`:
```env
USE_S3=true
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
S3_BUCKET_NAME=your_bucket
```

- **File Storage**: AWS S3
- **Downloads**: Presigned S3 URLs
- **Dependencies**: Requires boto3

## Testing

Run all tests:
```bash
python run_tests.py
```

Or with pytest directly:
```bash
pytest tests/ -v
```

## Architecture

### RAG Pipeline
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector Store**: In-memory with scikit-learn cosine similarity
- **Indexing**: Automatic on book/review changes
- **Search**: Semantic similarity matching

### Authentication
- **JWT Tokens**: Stateless authentication
- **Role-Based**: Admin/user permissions
- **Secure**: bcrypt password hashing

### Database
- **PostgreSQL**: Primary database
- **SQLAlchemy**: ORM with async support
- **Models**: Books, Reviews, Users, Roles, Documents

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create feature branch
3. Add tests for new features
4. Run test suite
5. Submit pull request

## License

MIT License - see LICENSE file for details