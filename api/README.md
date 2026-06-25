# ThromboTrack API

Python Flask-based REST API and PostgreSQL database to send and receive data from the frontend Expo web app, housed in a Docker container.

## Description

The API is a multi-container Docker Compose application, a virtual machine, with two separate containers within it. `web` is a container with a Debian image that runs the Python Flask backend, and `db` is an Alpine Linux container for the PostgreSQL database. `docker-compose.yml` describes the Docker Compose stack including ports, volumes, and environment variables. `Dockerfile` describes the sequence of commands that the virtual machine runs on boot, installing Python and PostgreSQL and then running `entrypoint.sh`, a shell script that starts the database on the VM's port 5432 and then starts the Flask server on the VM's port 5000.

## Getting Started

### Prerequisites

- Python 3.13
- Docker and Docker Compose
- Make utility

### Initial Setup

1. Clone the repository
2. Create a virtual environment and install dependencies
   - These are for Pylance/typing reasons-- the Docker container downloads its own dependencies
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Initialize the project:
   ```bash
   make init
   ```
4. Fill out `AUTHORITY`, `CLIENT_ID`, and `CLIENT_SECRET` (from Azure) in `.env`
5. Start the application:
   ```bash
   make up
   ```

The application will be available at:

- **Flask App**: http://localhost:5000 (or whatever port you defined in `.env`)
- **PostgreSQL Database**: postgresql://postgres:postgres@db:5432/ecmo_db

## Project Structure

```
.
├── app/
│   ├── detection/            # Oxygenator detection and image cropping
│   ├── migrations/           # Alembic database migrations
│   ├── routes/               # API endpoints (input and output)
│   ├── segmentation/         # Thrombus/fibrin segmentation
│   ├── services/             # Endpoint handlers
│   ├── utils/                # Helper functions
│   ├── __init__.py           # Flask app factory, CORS setup
│   ├── dto.py                # Typed response payloads
│   ├── helpers.py            # General helper functions
│   ├── models.py             # Database models
│   ├── schemas.py            # Marshmallow schemas for models
│   └── migrations/           # Alembic migrations
├── backups/                  # Database backups
├── docker-compose.yml        # Docker services configuration
├── Dockerfile                # Application container
├── entrypoint.sh             # Container startup script
├── alembic.ini               # Alembic configuration (database migrations)
├── requirements.txt          # Python dependencies
└── Makefile                  # All commands
```

## Accessing the Database

It is very useful to have direct access to the database for debugging and testing. I recommend installing [DBeaver](https://dbeaver.io) for a GUI to view tables and run queries. You can add a connection as follows:

1. New Database Connection
2. PostgreSQL
3. Host: localhost, port: 5432
4. Database: ecmo_db
5. Username: postgres
6. Password: postgres

## Suggested Documentation

- [SQLAlchemy](https://docs.sqlalchemy.org/en/20/)
- [Marshmallow](https://marshmallow.readthedocs.io/en/latest/)
- [Flask](https://flask.palletsprojects.com/en/stable/)

## Available Commands

### Project Setup

```bash
make init              # Initialize the entire project
make init-env          # Create .env from template
make init-migrations   # Initialize migrations structure
make fix-permissions   # Fix directory permissions
```

### Container Management

```bash
make build      # Build Docker images
make up         # Start all containers
make down       # Stop all containers
make restart    # Restart all containers
make ps         # Show container status
make status     # Show complete system status
```

### Development

```bash
make dev        # Start development environment with logs
make logs       # View application logs
make logs-db    # View database logs
make shell      # Open bash in web container
make shell-db   # Open PostgreSQL shell
```

### Database Migrations

```bash
make migrate MSG="description"  # Create new migration
make upgrade                    # Apply all pending migrations
make downgrade                  # Rollback last migration
make migrate-status            # Check current migration
make migrate-history           # Show migration history
```

### Backup & Restore

```bash
make backup                        # Create database backup
make backup-list                   # List all backups
make backup-clean                  # Remove old backups
make restore FILE=backup_file.sql.gz  # Restore from backup
```

Backups are stored in `./backups/` directory with format: `backup_YYYYMMDD_HHMMSS.sql.gz`

### Database Management

```bash
make db-reset       # Complete database reset (creates backup first)
```

### Production

```bash
make prod       # Build and start in production mode
```

### Cleanup

```bash
make clean      # Remove containers, images, volumes
make clean-all  # Complete cleanup including data
```

### Reset Everything

For a fresh start:

```bash
make clean-all
make init
make up
```

## Backup Strategy

The system includes automatic backup capabilities:

1. **Manual Backup**: `make backup`
2. **Before Reset**: Automatic backup before `make db-reset`
3. **Retention**: Old backups are cleaned based on `BACKUP_RETENTION_DAYS`

## Security Notes

⚠️ **Important for Production**:

1. Change `SECRET_KEY` in `.env`
2. Use strong passwords for database
3. Don't commit `.env` to version control
4. Use environment-specific `.env` files
5. Consider using Docker secrets for sensitive data

Created from [Flask PostgreSQL Docker Template](https://github.com/manzolo/docker-python-flask-postgres-template)
