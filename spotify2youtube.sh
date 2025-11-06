#!/bin/bash
# Spotify to YouTube Music Playlist Transfer - Helper Script

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python 3 is installed
if ! command_exists python3; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command_exists pip3; then
    echo "pip3 is required but not installed. Please install pip3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "\n✅ Setup complete! You're ready to use the tool.\n"
else
    # Activate existing virtual environment
    source venv/bin/activate
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Setting up environment..."
    cp .env.example .env
    echo -e "\n⚠️  Please edit the .env file with your API credentials before continuing.\n"
    
    # Open the .env file in the default editor if possible
    if command_exists nano; then
        read -p "Would you like to edit the .env file now? [Y/n] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [ -z "$REPLY" ]; then
            nano .env
        fi
    fi
    
    echo -e "\nAfter editing the .env file, run this script again to start the transfer."
    exit 0
fi

# Check if oauth.json exists
if [ ! -f "oauth.json" ]; then
    echo "Setting up YouTube Music authentication..."
    echo "This will open a browser window for authentication."
    
    # Install ytmusicapi if not already installed
    pip install ytmusicapi >/dev/null
    
    # Run the OAuth flow
    ytmusicapi oauth
    
    if [ ! -f "oauth.json" ]; then
        echo -e "\n❌ Authentication failed. Please try again."
        exit 1
    fi
    
    echo -e "\n✅ Authentication successful!\n"
fi

# Run the script with provided arguments
echo "Starting Spotify to YouTube Music Playlist Transfer..."
python3 spotify2youtube.py "$@"

deactivate 2>/dev/null || true
