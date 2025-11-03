# My fastapi project




## Prerequisites

- `Python 3.9+`
- `Poetry 1.2+`
- `Postgresql 10+`


## Development

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

**Required Variables:**
- `DATABASE_URI` - PostgreSQL connection string (e.g., `postgresql+asyncpg://user:password@localhost:5432/openalpha`)
- `SECRET_KEY` - Secure random string for JWT tokens and session security
- `REDIS_URL` - Redis connection string (e.g., `redis://localhost:6379`)
- `FIRST_SUPERUSER_EMAIL` - Email for initial admin user
- `FIRST_SUPERUSER_PASSWORD` - Password for initial admin user
- `DEFAULT_FROM_EMAIL` - Default email address for sending emails

**Optional Variables:**
- `ENVIRONMENT` - Environment mode: `dev` or `prod` (default: `dev`)
- `DEBUG` - Enable debug mode (default: `false`)
- `SERVER_HOST` - Server host URL (default: `http://localhost:8000`)
- `BACKEND_CORS_ORIGINS` - Comma-separated list of allowed CORS origins
- `RESEND_API_KEY` - API key for Resend email service (for future stories)
- `SENTRY_DSN` - Sentry DSN for error tracking in production

**Example `.env` file:**
```shell
DATABASE_URI=postgresql+asyncpg://openalpha_user:openalpha_password@localhost:5432/openalpha
SECRET_KEY=your-secret-key-here-generate-a-secure-random-string
REDIS_URL=redis://localhost:6379
ENVIRONMENT=dev
DEBUG=true
SERVER_HOST=http://localhost:8000
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
RESEND_API_KEY=
DEFAULT_FROM_EMAIL=noreply@openalpha.com
DEFAULT_FROM_NAME=OpenAlpha
EMAILS_ENABLED=false
FIRST_SUPERUSER_EMAIL=admin@openalpha.com
FIRST_SUPERUSER_PASSWORD=changeme123
SENTRY_DSN=
```

### Database setup

This project uses SQLAlchemy 2.0.x with Alembic for migrations.

**Create your first migration:**
```shell
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

**Adding new migrations:**
```shell
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

**Rollback migrations:**
```shell
alembic downgrade -1
```

### Run the FastAPI app

**Development mode (with auto-reload):**
```shell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```shell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Cli

There is a manage.py file at the root of the project, it contains a basic cli to hopefully
help you manage your project more easily. To get all available commands type this:

```shell
python manage.py --help
```

## Credits

This package was created with [Cookiecutter](https://github.com/cookiecutter/cookiecutter) and the [cookiecutter-fastapi](https://github.com/tobi-de/cookiecutter-fastapi) project template.
