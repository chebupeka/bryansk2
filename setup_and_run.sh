#!/bin/bash

set -e

#Update system
sudo apt update
sudo apt upgrade -y

#Install dependencies
sudo apt install -y python3 python3-venv python3-pip nodejs npm postgresql git
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
nvm use node

# Setup PostgreSQL
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'gschn_demo';" || true

# Check if DB exists, create if not (no delete!)
DB_EXISTS=$(sudo -u postgres psql -t -c "SELECT 1 FROM pg_database WHERE datname = 'gschn_demo';")
if [ -z "$DB_EXISTS" ]; then
    sudo -u postgres psql -c "CREATE DATABASE gschn_demo;"
fi

# Find PG version and set PG_CONF correctly
PG_VERSION=$(psql --version | grep -oP '\d+' | head -n 1)
PG_CONF="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

# Change peer to md5 in pg_hba.conf
sudo sed -i 's|local[[:space:]]\+all[[:space:]]\+postgres[[:space:]]\+peer|local   all             postgres                                md5|g' "$PG_CONF"
sudo service postgresql reload

#Setup backend
cd backend
if [ ! -d ".env" ]; then
    python3 -m venv .env
fi
source .env/bin/activate
pip install -r requirements.txt
deactivate
cd ..

#Setup Frontend
cd frontend
npm install
cd ..

#Run Backend in background
cd backend
source .env/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

#Run Frontend in background
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

#Wait for processes
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait

echo "Project is up!"
echo "Backend: https://localhost:8000"
echo "Frontend: https://localhost:5173"