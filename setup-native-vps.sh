#!/bin/bash

# Setup script for native VPS deployment (without Docker)
# This script installs all dependencies and configures the application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root or with sudo"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
PROJECT_DIR=$(pwd)

print_info "Starting VPS setup for PRD Analyst Dashboard"
print_info "Project directory: $PROJECT_DIR"
print_info "Running as user: $ACTUAL_USER"

# Update system packages
print_info "Updating system packages..."
apt-get update

# Install basic dependencies
print_info "Installing basic dependencies..."
apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    software-properties-common \
    gnupg \
    unzip \
    ca-certificates

# Install Python 3.11
print_info "Installing Python 3.11..."
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip

# Set Python 3.11 as default
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
update-alternatives --set python3 /usr/bin/python3.11

# Install Node.js 20
print_info "Installing Node.js 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs

# Install pnpm
print_info "Installing pnpm..."
npm install -g pnpm

# Install PostgreSQL 14
print_info "Installing PostgreSQL 14..."
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y postgresql-14 postgresql-client-14

# Install Chrome dependencies for Selenium
print_info "Installing Chrome dependencies..."
apt-get install -y \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils

# Install Google Chrome
print_info "Installing Google Chrome..."
wget -q -O /tmp/google-chrome-key.pub https://dl-ssl.google.com/linux/linux_signing_key.pub
gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg /tmp/google-chrome-key.pub
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable
rm -f /tmp/google-chrome-key.pub

# Install ChromeDriver
print_info "Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
print_info "Chrome version: $CHROME_VERSION"
CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"
wget -q "$CHROMEDRIVER_URL" -O /tmp/chromedriver.zip
unzip -q /tmp/chromedriver.zip -d /tmp/
mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver
rm -rf /tmp/chromedriver.zip /tmp/chromedriver-linux64
chromedriver --version

# Setup PostgreSQL
print_info "Setting up PostgreSQL database..."
bash "$PROJECT_DIR/scripts/setup-postgres.sh"

# Create log directory
print_info "Creating log directory..."
mkdir -p /var/log/prd-analyst
chown -R $ACTUAL_USER:$ACTUAL_USER /var/log/prd-analyst

# Install Python dependencies
print_info "Installing Python dependencies..."
cd "$PROJECT_DIR/backend"
sudo -u $ACTUAL_USER python3 -m pip install --upgrade pip
sudo -u $ACTUAL_USER python3 -m pip install -r requirements.txt

# Install Node.js dependencies
print_info "Installing Node.js dependencies..."
cd "$PROJECT_DIR/frontend"
sudo -u $ACTUAL_USER pnpm install

# Build frontend for production
print_info "Building frontend..."
sudo -u $ACTUAL_USER pnpm build

# Setup environment file
print_info "Setting up environment file..."
cd "$PROJECT_DIR"
if [ ! -f .env ]; then
    cp .env.example .env
    print_warning "Created .env file from template. Please update with your actual values!"
else
    print_info ".env file already exists, skipping..."
fi

# Install systemd services
print_info "Installing systemd services..."
cp "$PROJECT_DIR/systemd/prd-backend.service" /etc/systemd/system/
cp "$PROJECT_DIR/systemd/prd-frontend.service" /etc/systemd/system/

# Update service files with correct paths
sed -i "s|/path/to/project|$PROJECT_DIR|g" /etc/systemd/system/prd-backend.service
sed -i "s|/path/to/project|$PROJECT_DIR|g" /etc/systemd/system/prd-frontend.service
sed -i "s|User=ubuntu|User=$ACTUAL_USER|g" /etc/systemd/system/prd-backend.service
sed -i "s|User=ubuntu|User=$ACTUAL_USER|g" /etc/systemd/system/prd-frontend.service

# Reload systemd
systemctl daemon-reload

# Enable services
print_info "Enabling services..."
systemctl enable prd-backend
systemctl enable prd-frontend

print_info "Setup completed successfully!"
echo ""
print_info "Next steps:"
echo "1. Edit .env file with your configuration (especially GEMINI_API_KEY)"
echo "2. Start services: sudo systemctl start prd-backend prd-frontend"
echo "3. Check status: sudo systemctl status prd-backend prd-frontend"
echo "4. View logs: sudo journalctl -u prd-backend -f"
echo ""
print_info "Access the application:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
