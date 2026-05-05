# Flask PostgreSQL Docker Template

A production-ready Flask application template with PostgreSQL, pgAdmin, Alembic migrations, and automated backup/restore functionality.

## Features

- 🐍 Flask web application
- 🐘 PostgreSQL database with automatic migrations
- 🔧 pgAdmin for database management
- 💾 Automated backup and restore system
- 🐳 Docker containerization
- 🔄 Alembic database migrations
- 🛠️ Comprehensive Makefile with all commands
- 🔒 Proper permission management

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Make utility

### Initial Setup

1. Clone the repository
2. Initialize the project:
   ```bash
   make init
   ```
3. Edit `.env` file with your configurations
4. Start the application:
   ```bash
   make up
   ```

The application will be available at:
- **Flask App**: http://localhost:5000
- **pgAdmin**: http://localhost:5050

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
make logs-pgadmin  # View pgAdmin logs
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
make pgadmin-open   # Show pgAdmin connection info
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

## pgAdmin Access

Default credentials (change in `.env`):
- **Email**: admin@admin.com
- **Password**: admin
- **URL**: http://localhost:5050

### Connecting to Database in pgAdmin

1. Open pgAdmin at http://localhost:5050
2. Right-click "Servers" → "Register" → "Server"
3. General tab:
   - Name: `MyApp Database` (or any name)
4. Connection tab:
   - Host: `db`
   - Port: `5432`
   - Database: `myapp_db` (from .env)
   - Username: `postgres` (from .env)
   - Password: `postgres` (from .env)

## Environment Variables

Key variables in `.env`:

```bash
# Automatic user detection (usually correct)
UID=1000
GID=1000

# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key
APP_PORT=5000

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=myapp_db
POSTGRES_PORT=5432

# pgAdmin
PGADMIN_EMAIL=admin@admin.com
PGADMIN_PASSWORD=admin
PGADMIN_EXTERNAL_PORT=5050

# Backup
BACKUP_RETENTION_DAYS=7
```

## Project Structure

```
.
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # Database models
│   ├── routes.py             # Application routes
│   └── migrations/           # Alembic migrations
├── backups/                  # Database backups
├── docker-compose.yml        # Docker services configuration
├── Dockerfile               # Application container
├── entrypoint.sh            # Container startup script
├── requirements.txt         # Python dependencies
├── Makefile                 # All commands
├── .env                     # Environment variables (not in git)
└── .env.example             # Environment template

## Troubleshooting

### Permission Issues

If you encounter permission errors:
```bash
make fix-permissions
```

### Database Connection Issues

Check if database is ready:
```bash
make logs-db
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
2. Use strong passwords for database and pgAdmin
3. Don't commit `.env` to version control
4. Use environment-specific `.env` files
5. Consider using Docker secrets for sensitive data

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - Feel free to use this template for your projects.