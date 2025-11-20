#!/usr/bin/env python3
"""
Spotify to YouTube Music Playlist Transfer Tool

This script transfers playlists from Spotify to YouTube Music.
"""
import os
import sys
import json
import click
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import re

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm

# Initialize console for rich output
console = Console()

def setup_environment() -> bool:
    """Set up environment variables from .env file."""
    env_path = Path('.env')
    if not env_path.exists():
        console.print("[yellow]Warning:[/yellow] No .env file found. Please create one from .env.example")
        return False
    load_dotenv()
    return True

def initialize_spotify() -> Optional[spotipy.Spotify]:
    """Initialize and return Spotify client."""
    try:
        client_id = os.getenv('SPOTIPY_CLIENT_ID')
        client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        redirect_uri = 'http://127.0.0.1:8888/callback'  # Using 127.0.0.1 instead of localhost
        
        console.print(f"[yellow]Initializing Spotify with redirect_uri: {redirect_uri}")
        
        sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='playlist-read-private',
            show_dialog=True  # Force showing the auth dialog
        )
        
        # Get the authorization URL to see what's being used
        auth_url = sp_oauth.get_authorize_url()
        console.print(f"[yellow]Auth URL: {auth_url}")
        
        sp = spotipy.Spotify(auth_manager=sp_oauth)
        return sp
    except Exception as e:
        console.print(f"[red]Error initializing Spotify client:[/red] {e}")
        import traceback
        traceback.print_exc()
        return None

def initialize_ytmusic() -> Optional[YTMusic]:
    """Initialize and return YouTube Music client."""
    try:
        # Check if browser.json file exists, if not, guide the user to create it
        if not os.path.exists('browser.json'):
            console.print("[yellow]YouTube Music authentication required.[/yellow]")
            console.print("Please run the following command in your terminal to authenticate:")
            console.print("  pbpaste | ytmusicapi browser")
            console.print("\nSteps:")
            console.print("1. Open https://music.youtube.com in Firefox and log in")
            console.print("2. Open Developer Tools (Ctrl-Shift-I) and go to Network tab")
            console.print("3. Filter by '/browse' and find a POST request")
            console.print("4. Right click > Copy > Copy Request Headers")
            console.print("5. Run the command above (the headers should be in your clipboard)")
            console.print("\nAfter authenticating, a file named 'browser.json' will be created in this directory.")
            console.print("Once you've completed the authentication, run this script again.")
            return None
            
        # Initialize with browser authentication
        return YTMusic('browser.json')
        
    except Exception as e:
        console.print(f"[red]Error initializing YouTube Music client:[/red] {e}")
        import traceback
        traceback.print_exc()
        console.print("Please make sure you have the latest version of ytmusicapi installed.")
        return None

def get_spotify_playlist(sp: spotipy.Spotify, playlist_id: str, use_cache: bool = True, cache_expiry_days: int = 7, limit: int = None) -> Tuple[Dict, List[Dict]]:
    """Fetch playlist details and tracks from Spotify with optional caching.
    
    Args:
        sp: Authenticated Spotify client
        playlist_id: ID of the Spotify playlist
        use_cache: Whether to use cached data if available
        cache_expiry_days: Number of days to consider cache valid
        limit: Maximum number of tracks to fetch
        
    Returns:
        Tuple of (playlist_details, tracks)
    """
    # Create cache directory if it doesn't exist
    cache_dir = Path('.spotify_cache')
    cache_dir.mkdir(exist_ok=True)
    
    # Create a unique cache key based on playlist ID
    cache_key = hashlib.md5(playlist_id.encode()).hexdigest()
    cache_file = cache_dir / f"{cache_key}.json"
    
    # Try to load from cache if enabled
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # Check if cache is still valid
            cache_time = datetime.fromisoformat(cached_data['cached_at'])
            if datetime.now() - cache_time < timedelta(days=cache_expiry_days):
                console.print("[yellow]Using cached Spotify playlist data[/yellow]")
                return cached_data['playlist'], cached_data['tracks']
                
        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[yellow]Cache file corrupted, fetching fresh data: {e}[/yellow]")
    
    # If we get here, either cache is disabled or invalid
    try:
        # Get playlist details
        playlist = sp.playlist(playlist_id)
        
        # Get all tracks with pagination
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
        
        # Apply track limit if specified
        if limit:
            tracks = tracks[:limit]
        
        # Save to cache
        cache_data = {
            'playlist': playlist,
            'tracks': tracks,
            'cached_at': datetime.now().isoformat(),
            'playlist_id': playlist_id
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        return playlist, tracks
        
    except Exception as e:
        console.print(f"[red]Error fetching Spotify playlist:[/red] {e}")
        raise

def search_youtube_music_track(ytmusic: YTMusic, track_name: str, artist_name: str) -> Optional[dict]:
    """
    Search for a track on YouTube Music and return the best match video info.
    Returns a dict with 'videoId', 'title', 'artist', and 'duration_seconds' if found, None otherwise.
    """
    query = f"{track_name} {artist_name}"
    results = ytmusic.search(query, limit=5)

    # Look for a track result (type 'song' in YTMusic)
    for result in results:
        if result.get('resultType') == 'song':
            duration_text = result.get('duration')  # e.g. '3:45' or '1:02:03'
            duration_seconds = None
            if duration_text:
                try:
                    parts = [int(p) for p in duration_text.split(':')]
                    if len(parts) == 3:
                        duration_seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
                    elif len(parts) == 2:
                        duration_seconds = parts[0] * 60 + parts[1]
                except (ValueError, TypeError):
                    duration_seconds = None

            return {
                'videoId': result['videoId'],
                'title': result.get('title', 'Unknown Title'),
                'artist': result.get('artists', [{}])[0].get('name', 'Unknown Artist'),
                'duration_seconds': duration_seconds,
            }
    return None


def parse_variance(value: Optional[str]) -> Tuple[Optional[float], str]:
    """Parse a variance specification like '5s' or '5%' into a numeric value and mode.

    Returns (amount, mode) where mode is 'seconds' or 'percent'. If value is None or
    invalid, returns (None, 'seconds').
    """
    if not value:
        return None, 'seconds'

    value = value.strip().lower()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)(s|sec|secs|second|seconds|%|percent|perc)?", value)
    if not match:
        return None, 'seconds'

    num_str, suffix = match.groups()
    try:
        amount = float(num_str)
    except ValueError:
        return None, 'seconds'

    if not suffix:
        # Default to seconds if no suffix
        return amount, 'seconds'

    if suffix in {'%', 'percent', 'perc'}:
        return amount, 'percent'

    # Any time-related suffix is treated as seconds
    return amount, 'seconds'

def prompt_for_youtube_link(track_name: str, artist_name: str) -> Optional[str]:
    """Prompt user to enter a YouTube URL or video ID for a track that couldn't be found."""
    console.print(f"\n[yellow]Could not find: {track_name} by {artist_name}[/yellow]")
    console.print("Please enter a YouTube URL or video ID (or press Enter to skip):")
    
    while True:
        user_input = input("> ").strip()
        
        if not user_input:
            return None
            
        # Extract video ID from various YouTube URL formats
        video_id = None
        if 'youtube.com/watch?v=' in user_input:
            video_id = user_input.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in user_input:
            video_id = user_input.split('youtu.be/')[-1].split('?')[0]
        elif len(user_input) == 11:  # Direct video ID
            video_id = user_input
            
        if video_id and len(video_id) == 11:
            return video_id
            
        console.print("[red]Invalid YouTube URL or video ID. Please try again or press Enter to skip.[/red]")

def create_youtube_music_playlist(ytmusic: YTMusic, title: str, description: str = "", privacy_status: str = "PRIVATE") -> str:
    """Create a new YouTube Music playlist and return its ID.
    
    Args:
        ytmusic: Initialized YTMusic client
        title: Title of the playlist
        description: Optional description for the playlist
        privacy_status: Privacy status ('PUBLIC', 'PRIVATE', or 'UNLISTED')
        
    Returns:
        str: ID of the created playlist
    """
    try:
        playlist_id = ytmusic.create_playlist(title, description, privacy_status=privacy_status)
        return playlist_id
    except Exception as e:
        console.print(f"[red]Error creating YouTube Music playlist:[/red] {e}")
        raise

def add_tracks_to_playlist(ytmusic: YTMusic, playlist_id: str, video_ids: List[str], progress=None, task=None):
    """
    Add tracks to a YouTube Music playlist.
    
    Args:
        ytmusic: Initialized YTMusic client
        playlist_id: ID of the YouTube Music playlist
        video_ids: List of YouTube video IDs to add
        progress: Optional Rich Progress object for progress tracking
        task: Optional Progress task ID
    """
    if not video_ids:
        console.print("[yellow]No video IDs to add to playlist[/yellow]")
        return

    try:
        # Ensure we're only working with valid video IDs
        valid_video_ids = [vid for vid in video_ids if vid and isinstance(vid, str) and len(vid) == 11]
        
        if not valid_video_ids:
            console.print("[yellow]No valid video IDs to add to playlist[/yellow]")
            return
            
        # YouTube Music API has a limit of 100 tracks per request
        for i in range(0, len(valid_video_ids), 100):
            batch = valid_video_ids[i:i+100]
            
            try:
                # Add tracks to playlist
                result = ytmusic.add_playlist_items(playlist_id, batch)
                
                # Check for errors in the response
                if 'status' in result and result['status'] == 'STATUS_SUCCEEDED':
                    console.print(f"[green]Added {len(batch)} tracks to playlist[/green]")
                else:
                    console.print(f"[yellow]Warning: Some tracks may not have been added: {result}")
                
                # Update progress if provided
                if progress and task:
                    progress.update(task, advance=len(batch))
                    
            except Exception as e:
                console.print(f"[red]Error adding batch {i//100 + 1}: {e}")
                # Try to continue with the next batch
                continue
                
    except Exception as e:
        console.print(f"[red]Error in add_tracks_to_playlist: {e}[/red]")
        console.print_exception()
        raise
    return True

@click.command()
@click.argument('spotify_playlist_id')
@click.option('--playlist-name', help='Name for the YouTube Music playlist')
@click.option('--privacy', 
              type=click.Choice(['public', 'private', 'unlisted'], case_sensitive=False),
              default='public',
              help='Privacy status of the playlist (public/private/unlisted)')
@click.option('--description', default='', help='Description for the playlist')
@click.option('--no-cache', is_flag=True, help='Disable caching of Spotify playlist data')
@click.option('--limit', type=int, default=None, help='Maximum number of tracks to transfer')
@click.option('--variance', 'variance_opt', default=None,
              help='Allowed duration variance between Spotify and YouTube matches, e.g. "5s" or "5%%"')
@click.option('--debug-variance', is_flag=True, default=False,
              help='Print per-track details about duration variance checks')
def main(spotify_playlist_id: str, playlist_name: str = None, privacy: str = 'public', 
         description: str = '', no_cache: bool = False, limit: int = None,
         variance_opt: Optional[str] = None, debug_variance: bool = False):
    """Transfer a Spotify playlist to YouTube Music.
    
    Args:
        spotify_playlist_id: ID of the Spotify playlist to transfer
        playlist_name: Custom name for the YouTube Music playlist (default: same as Spotify)
        privacy: Privacy status of the playlist ('public', 'private', or 'unlisted')
        description: Optional description for the playlist
        no_cache: If True, disable caching of Spotify playlist data
        limit: Maximum number of tracks to transfer (None for all)
    """
    console.print("Starting Spotify to YouTube Music playlist transfer...")
    
    # Initialize clients
    sp = initialize_spotify()
    if not sp:
        return
        
    ytmusic = initialize_ytmusic()
    if not ytmusic:
        return
    
    # Get Spotify playlist details (always fetch full playlist for caching)
    try:
        playlist, all_tracks = get_spotify_playlist(
            sp, 
            spotify_playlist_id, 
            use_cache=not no_cache
        )
        
        if not playlist_name:
            playlist_name = playlist.get('name', 'Untitled Playlist')
        
        if not description:
            description = f"Transferred from Spotify: {playlist.get('description', '')}"
        
        # Apply limit only to processing, not to fetching
        tracks = all_tracks[:limit] if limit else all_tracks
        if limit and len(all_tracks) > limit:
            console.print(f"[yellow]Processing {limit} out of {len(all_tracks)} tracks[/yellow]")
        
        # Show playlist info
        console.print(f"\n[bold]Playlist:[/bold] {playlist_name}")
        console.print(f"[bold]Tracks:[/bold] {len(tracks)}")
        console.print(f"[bold]Description:[/bold] {description[:100]}..." if description else "")
        
        if not Confirm.ask("\nDo you want to continue with the transfer?", default=True):
            console.print("Transfer cancelled.")
            return
            
        # Determine variance settings (CLI overrides env)
        env_variance = os.getenv('VARIANCE')
        env_variance_mode = os.getenv('VARIANCE_MODE')  # optional explicit mode

        variance_str = variance_opt or env_variance
        variance_amount, variance_mode = parse_variance(variance_str)

        # If no valid variance provided via CLI/env, default to 3 seconds
        if variance_amount is None:
            variance_amount = 3.0
            variance_mode = 'seconds'

        # Allow explicit env mode override
        if env_variance_mode:
            mode = env_variance_mode.strip().lower()
            if mode in {'seconds', 'second', 'sec', 's'}:
                variance_mode = 'seconds'
            elif mode in {'percent', '%', 'perc'}:
                variance_mode = 'percent'

        if variance_amount is not None:
            if variance_mode == 'seconds':
                console.print(f"[blue]Duration variance checking enabled:[/blue] ±{variance_amount} seconds")
            else:
                console.print(f"[blue]Duration variance checking enabled:[/blue] ±{variance_amount}%")
        else:
            console.print("[blue]Duration variance checking disabled (no valid variance specified)[/blue]")

        if debug_variance:
            console.print("[magenta]Debug variance logging is ON[/magenta]")

        # Search for each track on YouTube Music
        video_ids = []
        unmatched_tracks = []
        duration_mismatches = []
        duration_skipped = []
        
        with Progress() as progress:
            task = progress.add_task("Searching for tracks...", total=len(tracks))
            
            for item in tracks:
                track = item.get('track', {})
                if not track:
                    progress.console.print(f"[yellow]Skipping non-track item[/yellow]")
                    progress.update(task, advance=1)
                    continue
                
                track_name = track.get('name', 'Unknown Track')
                artist_name = track.get('artists', [{}])[0].get('name', 'Unknown Artist')
                spotify_duration_ms = track.get('duration_ms') or 0
                
                progress.console.print(f"Searching for: {track_name} - {artist_name}")
                
                track_info = search_youtube_music_track(ytmusic, track_name, artist_name)
                if track_info and 'videoId' in track_info:
                    video_ids.append(track_info['videoId'])
                    console.print(f"[green]✓ Found: {track_name} - {artist_name}[/green]")

                    # If variance checking is enabled and we have both durations, compare
                    if variance_amount is not None:
                        yt_duration_sec = track_info.get('duration_seconds')

                        if not spotify_duration_ms:
                            duration_skipped.append({
                                'track_name': track_name,
                                'artist_name': artist_name,
                                'reason': 'missing Spotify duration',
                            })
                            if debug_variance:
                                console.print(
                                    f"[magenta][variance-debug][/magenta] Skipping variance check for "
                                    f"{track_name} - {artist_name}: missing Spotify duration"
                                )
                        elif yt_duration_sec is None:
                            duration_skipped.append({
                                'track_name': track_name,
                                'artist_name': artist_name,
                                'reason': 'missing YouTube duration',
                            })
                            if debug_variance:
                                console.print(
                                    f"[magenta][variance-debug][/magenta] Skipping variance check for "
                                    f"{track_name} - {artist_name}: missing YouTube duration"
                                )
                        else:
                            spotify_duration_sec = spotify_duration_ms / 1000.0
                            diff_sec = abs(spotify_duration_sec - yt_duration_sec)

                            if debug_variance:
                                if variance_mode == 'seconds':
                                    console.print(
                                        f"[magenta][variance-debug][/magenta] {track_name} - {artist_name}: "
                                        f"Spotify={spotify_duration_sec:.1f}s, YT={yt_duration_sec:.1f}s, "
                                        f"diff={diff_sec:.1f}s, threshold={variance_amount} seconds"
                                    )
                                else:
                                    diff_pct = (diff_sec / spotify_duration_sec) * 100.0 if spotify_duration_sec > 0 else 0.0
                                    console.print(
                                        f"[magenta][variance-debug][/magenta] {track_name} - {artist_name}: "
                                        f"Spotify={spotify_duration_sec:.1f}s, YT={yt_duration_sec:.1f}s, "
                                        f"diff={diff_sec:.1f}s ({diff_pct:.1f}%), threshold={variance_amount}%"
                                    )

                            is_mismatch = False
                            if variance_mode == 'seconds':
                                if diff_sec > variance_amount:
                                    is_mismatch = True
                            else:  # percent
                                if spotify_duration_sec > 0:
                                    diff_pct = (diff_sec / spotify_duration_sec) * 100.0
                                    if diff_pct > variance_amount:
                                        is_mismatch = True

                            if is_mismatch:
                                duration_mismatches.append({
                                    'track_name': track_name,
                                    'artist_name': artist_name,
                                    'spotify_duration_sec': spotify_duration_sec,
                                    'yt_duration_sec': yt_duration_sec,
                                    'diff_sec': diff_sec,
                                })
                else:
                    console.print(f"[yellow]✗ Not found: {track_name} - {artist_name}[/yellow]")
                    unmatched_tracks.append(f"{track_name} - {artist_name}")
                
                progress.update(task, advance=1)
        
        # Show summary of found tracks
        console.print(f"\n[yellow]Found {len(video_ids)}/{len(tracks)} tracks on YouTube Music[/yellow]")
        
        if not video_ids:
            console.print("[red]No tracks found to add to playlist. Exiting...[/red]")
            return
            
        # Create YouTube Music playlist
        privacy_status = privacy.upper()  # Convert to uppercase for the API
        privacy_display = {'PUBLIC': 'public', 'PRIVATE': 'private', 'UNLISTED': 'unlisted'}.get(privacy_status, privacy_status)
        console.print(f"\nCreating YouTube Music playlist with {len(video_ids)} tracks...")
        
        console.print(f"\nCreating {privacy_display} YouTube Music playlist: {playlist_name}")
        yt_playlist_id = create_youtube_music_playlist(ytmusic, playlist_name, description, privacy_status=privacy_status)
        if not yt_playlist_id:
            console.print("[red]Failed to create YouTube Music playlist.[/red]")
            return
            
        # Add tracks to playlist
        with console.status(f"Adding {len(video_ids)} tracks to playlist...") as status:
            add_tracks_to_playlist(ytmusic, yt_playlist_id, video_ids)
            
        console.print(f"\n[green]Successfully added {len(video_ids)} tracks to the playlist![/green]")
        
        # Show unmatched tracks if any
        if unmatched_tracks:
            console.print("\n[yellow]Failed to find the following tracks on YouTube Music:[/yellow]")
            for track in unmatched_tracks:
                console.print(f"- {track}")

        # Show duration mismatches if any
        if duration_mismatches:
            console.print("\n[yellow]Tracks with significant duration differences:[/yellow]")
            for entry in duration_mismatches:
                sp_len = entry['spotify_duration_sec']
                yt_len = entry['yt_duration_sec']
                diff = entry['diff_sec']
                console.print(
                    f"- {entry['track_name']} - {entry['artist_name']} "
                    f"(Spotify: {sp_len:.1f}s, YouTube: {yt_len:.1f}s, diff: {diff:.1f}s)"
                )

        # Show tracks where duration comparison was skipped
        if duration_skipped:
            console.print("\n[yellow]Tracks where duration comparison was skipped:[/yellow]")
            for entry in duration_skipped:
                console.print(
                    f"- {entry['track_name']} - {entry['artist_name']} "
                    f"(reason: {entry['reason']})"
                )

        console.print("\n[green]Transfer complete![/green]")
        
    except Exception as e:
        console.print(f"[red]An error occurred:[/red] {e}")
        console.print_exception()
        return

if __name__ == "__main__":
    # Load environment variables first
    if not setup_environment():
        console.print("[red]Error:[/red] Failed to load environment variables. Please check your .env file.")
        sys.exit(1)
    main()
