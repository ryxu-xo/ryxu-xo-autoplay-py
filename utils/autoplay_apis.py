"""
Optimized autoplay API functions for SoundCloud and Spotify.
"""

import re
import asyncio
import random
import hashlib
import hmac
import time
from typing import List, Optional, Tuple
from .http import fetch_page


# Constants for performance optimization
MAX_REDIRECTS = 2
MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB
MAX_SC_LINKS = 20
MAX_SP_RESULTS = 5
DEFAULT_TIMEOUT_MS = 5000

# SoundCloud link pattern
SC_LINK_PATTERN = re.compile(r'<a\s+itemprop="url"\s+href="(\/[^"]+)"')

# Spotify TOTP secret
SPOTIFY_TOTP_SECRET = b'5507145853487499592248630329347'


async def fast_fetch(url: str, max_redirects: int = MAX_REDIRECTS) -> str:
    """Fast fetch with redirect support and size limits."""
    try:
        return await fetch_page(url)
    except Exception as e:
        raise Exception(f"Failed to fetch {url}: {str(e)}")


def shuffle_in_place(items: List[Any]) -> None:
    """Shuffle a list in place for better performance."""
    for i in range(len(items) - 1, 0, -1):
        j = random.randint(0, i)
        items[i], items[j] = items[j], items[i]


async def sc_auto_play(base_url: str) -> Optional[str]:
    """SoundCloud autoplay handler - optimized version."""
    try:
        html = await fast_fetch(f"{base_url}/recommended")
        found = []
        
        for match in SC_LINK_PATTERN.finditer(html):
            found.append(f"https://soundcloud.com{match.group(1)}")
            if len(found) >= MAX_SC_LINKS:
                break
        
        if not found:
            raise Exception("No recommended SoundCloud tracks found.")
        
        return random.choice(found)
        
    except Exception as e:
        print(f"[SC Autoplay Error] {str(e)}")
        return None


def create_totp() -> Tuple[str, int]:
    """Generate TOTP used for Spotify embed access."""
    time_val = int(time.time() // 30)
    buffer = time_val.to_bytes(8, 'big')
    hash_bytes = hmac.new(SPOTIFY_TOTP_SECRET, buffer, hashlib.sha1).digest()
    
    offset = hash_bytes[-1] & 0xf
    code = (
        ((hash_bytes[offset] & 0x7f) << 24) |
        ((hash_bytes[offset + 1] & 0xff) << 16) |
        ((hash_bytes[offset + 2] & 0xff) << 8) |
        (hash_bytes[offset + 3] & 0xff)
    )
    
    return (code % 1_000_000).zfill(6), time_val * 30000


async def sp_auto_play(seed_id: str) -> Optional[str]:
    """Spotify autoplay handler - optimized version."""
    totp, timestamp = create_totp()
    token_endpoint = f"https://open.spotify.com/api/token?reason=init&productType=embed&totp={totp}&totpVer=5&ts={timestamp}"
    
    try:
        token_data = await fast_fetch(token_endpoint, headers={
            'Referer': 'https://open.spotify.com/',
            'Origin': 'https://open.spotify.com'
        })
        
        token_json = eval(token_data)  # Simple JSON parsing
        token = token_json.get('accessToken')
        
        if not token:
            raise Exception("No access token from Spotify")
        
        rec_url = f"https://api.spotify.com/v1/recommendations?limit={MAX_SP_RESULTS}&seed_tracks={seed_id}"
        rec_data = await fast_fetch(rec_url, headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        parsed = eval(rec_data)  # Simple JSON parsing
        if not parsed.get('tracks'):
            raise Exception("No recommended tracks received.")
        
        tracks = parsed['tracks']
        track = random.choice(tracks)
        return track['id']
        
    except Exception as e:
        print(f"[Spotify Autoplay Error] {str(e)}")
        return None


def yt_auto_play(video_id: str) -> Optional[str]:
    """YouTube autoplay handler (radio style via RD playlist)."""
    if not video_id:
        return None
    return f"https://www.youtube.com/watch?v={video_id}&list=RD{video_id}"
