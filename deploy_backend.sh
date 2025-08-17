#!/bin/bash

# Clone the repository
git clone https://github.com/GlacierEQ/FILEBOSS.git /home/ubuntu/app

# Install dependencies
/home/ubuntu/app/venv/bin/pip install -r /home/ubuntu/app/requirements.txt

# Create .env file
tee /home/ubuntu/app/.env <<EOF
DATABASE_URL=postgresql+asyncpg://fileboss:your-db-password@your-rds-endpoint/fileboss
SECRET_KEY=a-secure-random-secret-key
EOF

# Run database migrations
/home/ubuntu/app/venv/bin/alembic upgrade head

# Restart Supervisor
sudo supervisorctl restart fileboss
