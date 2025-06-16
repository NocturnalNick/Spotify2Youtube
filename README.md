# Spotify to YouTube Music Playlist Transfer

A command-line tool to transfer your Spotify playlists to YouTube Music with support for manual track matching.

## Features

- Transfer entire Spotify playlists to YouTube Music
- Preserve playlist names and descriptions
- Simple command-line interface with progress tracking
- Manual matching for tracks that can't be found automatically
- Saves unmatched tracks to a file for later reference
- Handles large playlists with pagination
- Caches Spotify playlist data to reduce API calls
- Option to limit the number of tracks to transfer

## Prerequisites

- Python 3.7 or higher
- A Spotify Developer account
- A YouTube/Google account

## Installation

### Option 1: Using the Helper Script (Recommended)

1. Clone this repository or download the source code
2. Make the script executable (Linux/macOS):
   ```bash
   chmod +x spotify2youtube.sh
   ```
3. Run the script:
   ```bash
   ./spotify2youtube.sh SPOTIFY_PLAYLIST_ID
   ```

The first time you run the script, it will:
- Create a Python virtual environment
- Install all required dependencies
- Help you set up the `.env` file with your API credentials
- Guide you through the YouTube Music OAuth authentication

### Option 2: Manual Setup

1. Clone this repository or download the source code
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your `.env` file as described in the Configuration section
5. Run the script:
   ```bash
   python spotify2youtube.py SPOTIFY_PLAYLIST_ID
   ```

## Setup

### 1. Spotify API Setup

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Log in with your Spotify account
3. Click "Create an App"
4. Fill in the app details (name and description can be anything)
5. Once created, note down your Client ID and Client Secret
6. Click "Edit Settings" and add `http://127.0.0.1:8888/callback` to the Redirect URIs

### 2. YouTube Music Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3:
   - Go to "APIs & Services" > "Library"
   - Search for "YouTube Data API v3" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "TVs and Limited Input devices" as the application type
   - Note down the Client ID and Client Secret

### 3. First-Time Setup

Run the following command to set up authentication:

```bash
# This will open a browser window for YouTube Music authentication
ytmusicapi oauth
```

Follow the prompts to log in to your Google account and grant the necessary permissions. This will create an `oauth.json` file in your current directory.

## First Run

When you run the tool for the first time using the helper script:

1. It will create a Python virtual environment (if it doesn't exist)
2. Install all required dependencies
3. Help you set up the `.env` file with your API credentials
4. Guide you through the YouTube Music OAuth authentication process
5. Save the authentication details to `oauth.json` for future use

If you're running the Python script directly, you'll need to manually:
1. Set up the virtual environment and install dependencies
2. Create and configure the `.env` file
3. Run `ytmusicapi oauth` to authenticate with YouTube Music

## Configuration

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit the `.env` file and add your credentials:
   ```
   # Spotify API credentials
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
   
   # YouTube Data API credentials
   YOUTUBE_CLIENT_ID=your_youtube_client_id
   YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
   ```

## Usage

### Basic Usage (with helper script)

```bash
# Basic usage (creates a public playlist by default)
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID

# With custom name and privacy settings
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID --playlist-name "My Playlist" --privacy unlisted
```

Example:
```bash
./spotify2youtube.sh 37i9dQZF1DXcBWIGoYBM5M --privacy unlisted
```

### Manual Execution

If you prefer to run the Python script directly:

```bash
# Basic usage
python spotify2youtube.py SPOTIFY_PLAYLIST_ID

# With options
python spotify2youtube.py SPOTIFY_PLAYLIST_ID \
    --playlist-name "My Playlist" \
    --privacy unlisted \
    --description "My playlist description"
```

### Privacy Options

You can specify the privacy status of the created YouTube Music playlist:

```bash
# Create a private playlist
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID --privacy private

# Create an unlisted playlist (visible only with link)
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID --privacy unlisted
```

### Caching and Track Limits

The tool caches Spotify playlist data by default to reduce API calls. You can control this behavior:

```bash
# Disable caching (fetch fresh data from Spotify)
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID --no-cache

# Limit the number of tracks to transfer (e.g., first 10 tracks)
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID --limit 10

# Combine options (limit to 20 tracks with no caching)
./spotify2youtube.sh SPOTIFY_PLAYLIST_ID --limit 20 --no-cache
```

Cache files are stored in the `.spotify_cache` directory and are valid for 7 days by default.

### Options

- `--playlist-name`: Specify a custom name for the YouTube Music playlist
- `--privacy`: Set playlist privacy to 'public', 'private', or 'unlisted' (default: public)
- `--description`: Add a custom description to the playlist

Example with options:
```bash
python spotify2youtube.py 37i9dQZF1DXcBWIGoYBM5M \
    --playlist-name "My Awesome Playlist" \
    --privacy unlisted \
    --description "Transferred from Spotify"
```

### Finding a Spotify Playlist ID

1. Open the Spotify app or web player
2. Right-click on a playlist
3. Select "Share" > "Copy Playlist Link"
4. The ID is the string of characters after `playlist/` and before any `?`

Example: `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M` → `37i9dQZF1DXcBWIGoYBM5M`

## Manual Track Matching

If some tracks can't be found automatically, the tool will:

1. Show you a list of tracks that couldn't be found
2. Give you the option to manually provide YouTube links/IDs for these tracks
3. Allow you to skip tracks that can't be matched
4. Save a list of all unmatched tracks to `unmatched_tracks.json` for future reference

### Example Manual Match

```
Could not find: Song Name by Artist Name
Please enter a YouTube URL or video ID (or press Enter to skip):
> https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

You can provide either:
- A full YouTube URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
- A youtu.be short URL (e.g., `https://youtu.be/dQw4w9WgXcQ`)
- Just the video ID (e.g., `dQw4w9WgXcQ`)

## Troubleshooting

### Helper Script Issues

- **Permission denied** when running the script:
  ```bash
  chmod +x spotify2youtube.sh
  ```

- **Command not found** on Windows:
  - Use Git Bash, WSL, or run with `bash spotify2youtube.sh`
  - Alternatively, follow the manual setup instructions

### Spotify "Invalid Client" Error
- Make sure you're using `http://127.0.0.1:8888/callback` (not `localhost`)
- Verify the redirect URI in your Spotify Developer Dashboard matches exactly
- Try clearing your browser cookies or using a private/incognito window

### YouTube Music Authentication Issues
- Delete the `oauth.json` file and run the helper script again
- Make sure you've set up the YouTube Data API credentials correctly
- Ensure your Google account has access to YouTube Music
- If using the helper script, it will automatically handle the OAuth setup

### Tracks Not Found
- Check the `unmatched_tracks.json` file for a list of tracks that couldn't be matched
- Use the manual matching feature to add these tracks
- Some tracks might not be available on YouTube Music due to regional restrictions or catalog differences

### Rate Limiting
- Both Spotify and YouTube Music have rate limits
- If you encounter rate limiting, wait a few minutes and try again
- The script includes automatic retries for failed requests
- **Rate limiting**: If you encounter rate limits, wait a few minutes and try again

## Common Issues & Solutions

### "INVALID_CLIENT: Insecure redirect URI"
This occurs when the redirect URI in your Spotify Developer Dashboard doesn't match exactly what's in your `.env` file. Make sure both use `http://127.0.0.1:8888/callback` (not `localhost`).

### YouTube Music API Errors
If you see errors related to YouTube Music API initialization, make sure:
1. You've run `ytmusicapi oauth` to create the `oauth.json` file
2. Your YouTube Data API credentials are correctly set in the `.env` file
3. The YouTube Data API is enabled in your Google Cloud Console

## License

MIT

## Acknowledgments

- [Spotipy](https://github.com/plamere/spotipy) - Spotify Web API client
- [ytmusicapi](https://github.com/sigma67/ytmusicapi) - YouTube Music API client
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
