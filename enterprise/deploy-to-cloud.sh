#!/bin/bash
# ==============================================================================
# Local AI Studio - Cloud Server Deployment Script (Ubuntu / Debian)
# ==============================================================================
# Run this script on a fresh AWS EC2, Google Cloud Compute Engine, or DigitalOcean 
# droplet to automatically install dependencies and deploy the Enterprise Edition.
# ==============================================================================

set -e

echo "🚀 Starting Enterprise Deployment for Local AI Studio..."

# 1. Update the server and install Git and prerequisites
echo "📦 Installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y git curl apt-transport-https ca-certificates software-properties-common

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
fi

# 3. Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 4. Clone the repository
# Note: Ensure the target server has permissions to clone the repository.
REPO_DIR="local-ai-studio"
if [ ! -d "$REPO_DIR" ]; then
    echo "📂 Cloning repository..."
    git clone https://github.com/dragpk247/local-ai-studio.git
fi

cd $REPO_DIR/enterprise

# 5. Start the Enterprise Containers
echo "🚢 Spinning up the Docker containers..."
sudo docker-compose up -d --build

echo ""
echo "✅ Deployment Successful!"
echo "🌐 Your Local AI Studio is now running."
echo "🔒 Note: If you left the OAuth proxy configured, the app will be running on port 80 and will ask for a Google Login."
