#!/bin/bash

set -e

# Check and source .env file (not folder!)
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
    echo "Loaded .env: OK"
else
    echo "Warning: $ENV_FILE not found! Using fallbacks. Copy .env.example to .env and edit."
    POSTGRES_PASSWORD="gschn_demo"
    DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/gschn_demo"
    VITE_API_URL="http://127.0.0.1:8000"
    BACKEND_PORT=8000
fi

export PGPASSWORD="$POSTGRES_PASSWORD"

# Update system
sudo apt update && sudo apt upgrade -y

# Install deps
sudo apt install -y python3 python3-venv python3-pip nodejs npm postgresql git

# NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use node || nvm install node

# PostgreSQL setup
sudo systemctl start postgresql || sudo service postgresql start

# Set PG password (no prompt)
echo "Setting PG password..."
sudo -u postgres psql -c "ALTER USER postgres PASSWORD '$POSTGRES_PASSWORD';" 2>/dev/null || true

# Create DB
DB_EXISTS=$(sudo -u postgres psql -t -c "SELECT 1 FROM pg_database WHERE datname = 'gschn_demo';" 2>/dev/null || echo "")
if [ -z "$DB_EXISTS" ]; then
    sudo -u postgres createdb gschn_demo
    echo "DB gschn_demo created."
fi

# PG conf for md5 (no peer)
PG_VERSION=$(psql --version 2>/dev/null | grep -oP '\d+' | head -1 || echo "14")
PG_CONF="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"
sudo sed -i 's/local\s*all\s*postgres\s*peer/local   all             postgres                                md5/g' "$PG_CONF"
sudo systemctl reload postgresql || sudo service postgresql reload

# Backend setup
cd backend
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Frontend setup
cd frontend
npm ci  # Clean install
cd ..

# Run backend (nohup for stability)
cd backend
source .venv/bin/activate
echo "Starting backend on port $BACKEND_PORT..."
nohup uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Run frontend
cd frontend
echo "Starting frontend..."
nohup npm run dev -- --host 0.0.0.0 --port 5173 > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Cleanup trap
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; echo 'Cleanup done.'" EXIT

# Wait & status
echo "Project launched! Check logs: tail -f backend.log or frontend.log"
echo "Local: http://localhost:5173"
echo "Server: http://31.129.108.187:5173"
echo "Backend API: http://31.129.108.187:$BACKEND_PORT"
wait