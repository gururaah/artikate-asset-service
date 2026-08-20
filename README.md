# Field Asset Check-Out Service (FastAPI)

Internal REST API that tracks physical equipment checked out to and returned by employees[cite: 1]. Built using FastAPI, SQLAlchemy 2.0, PostgreSQL, Celery, and Docker.

## Tech Stack
- **Framework:** FastAPI
- **Database ORM:** SQLAlchemy 2.0 (PostgreSQL 15)
- **Migrations:** Alembic
- **Background Workers:** Celery & Redis
- **Containerisation:** Docker & Docker Compose

---

## Setup Instructions (Docker)
To bring up the stack cleanly from a clone:

1. **Clone the repository and navigate inside:**
   ```bash
   git clone <your-repo-url>
   cd artikate_fastapi