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

The tool now uses browser-based authentication for YouTube Music, which is more reliable and doesn't require Google Cloud API credentials.

#### Browser Authentication Setup (Recommended)

1. Open [https://music.youtube.com](https://music.youtube.com) in Firefox and log in to your Google account
2. Open Developer Tools (Ctrl-Shift-I) and go to the Network tab
3. Filter by `/browse` to find authenticated POST requests
4. Click on any `/browse` request, then right-click > Copy > Copy Request Headers
5. Run the authentication command (the headers should be in your clipboard):
   ```bash
   pbpaste | ytmusicapi browser
   ```
   
   **Note for macOS users**: The terminal has a 1024 character limit for pasting. Use `pbpaste |` to pipe clipboard contents.
   
   **Note for other users**: If you're not on macOS, you can run:
   ```bash
   ytmusicapi browser
   ```
   Then paste the headers manually when prompted.

This will create a `browser.json` file with your authentication credentials. The authentication remains valid for about 2 years unless you log out of YouTube Music in your browser.

#### Alternative: Google Cloud API Setup (Legacy)

If you prefer the OAuth method, you can still set up Google Cloud credentials:

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

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file and add your Spotify credentials:
   ```
   # Spotify API credentials
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8888/callback
   ```
   
   **Note**: YouTube Data API credentials are no longer required if using browser authentication.

3. Set up YouTube Music authentication using the browser method (see section 2 above):
   ```bash
   # Make sure you have copied headers from Firefox first
   pbpaste | ytmusicapi browser
   ```
   - This will create a `browser.json` file in your current directory
   - The file contains your authentication tokens and should not be shared

## First Run

### Using the Helper Script (Recommended)

1. Make the script executable:
   ```bash
   chmod +x spotify2youtube.sh
   ```

2. Run the script with a Spotify playlist ID:
   ```bash
   ./spotify2youtube.sh SPOTIFY_PLAYLIST_ID
   ```

3. On first run, it will:
   - Create a Python virtual environment (if it doesn't exist)
   - Install all required dependencies
   - Guide you through the authentication process
   - Cache your credentials for future use

### Running Directly with Python

If you prefer to run the Python script directly:

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your `.env` file as described in the Configuration section

4. Run the script:
   ```bash
   python spotify2youtube.py SPOTIFY_PLAYLIST_ID
   ```

## Configuration

### Environment Variables

The following environment variables are required in your `.env` file:

- `SPOTIPY_CLIENT_ID`: Your Spotify application's client ID
- `SPOTIPY_CLIENT_SECRET`: Your Spotify application's client secret
- `SPOTIPY_REDIRECT_URI`: Must be set to `http://127.0.0.1:8888/callback`

**Note**: YouTube Data API credentials (`YOUTUBE_CLIENT_ID` and `YOUTUBE_CLIENT_SECRET`) are optional and only needed if you prefer the OAuth authentication method instead of browser-based authentication.

### Authentication Files

- `browser.json`: Generated by running `pbpaste | ytmusicapi browser`, contains your YouTube Music authentication tokens (recommended method)
- `oauth.json`: Generated by running `ytmusicapi oauth`, contains OAuth credentials (legacy method)
- `.cache-*`: Spotify OAuth cache files (automatically created on first run)

**Important**: Never commit authentication files to version control. They are already excluded in `.gitignore`.

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

**Browser Authentication Issues**:
- Delete the `browser.json` file and run the browser authentication again
- Make sure you're using Firefox (recommended) and have copied the request headers correctly
- Ensure you're logged into YouTube Music in your browser before copying headers
- On macOS, use `pbaste | ytmusicapi browser` to avoid clipboard size limits

**OAuth Authentication Issues** (legacy method):
- Delete the `oauth.json` file and run `ytmusicapi oauth` again
- Make sure you've set up the YouTube Data API credentials correctly
- Ensure your Google account has access to YouTube Music

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

**Browser Authentication Method** (recommended):
1. Make sure you've run `pbpaste | ytmusicapi browser` to create the `browser.json` file
2. Verify you copied the headers from a valid authenticated request to `/browse`
3. Try re-authenticating if you get HTTP 400 errors

**OAuth Authentication Method** (legacy):
1. Make sure you've run `ytmusicapi oauth` to create the `oauth.json` file
2. Your YouTube Data API credentials are correctly set in the `.env` file
3. The YouTube Data API is enabled in your Google Cloud Console

## License

MIT

## Acknowledgments

- [Spotipy](https://github.com/plamere/spotipy) - Spotify Web API client
- [ytmusicapi](https://github.com/sigma67/ytmusicapi) - YouTube Music API client
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal output
