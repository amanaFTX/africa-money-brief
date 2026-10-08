#!/usr/bin/env python3
"""Import a verified public HTTPS image into assets/briefs/ for GitHub Pages."""
import argparse
import hashlib
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--sha256", required=True)
    a = p.parse_args()
    parsed = urlparse(a.url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        p.error("A valid HTTPS image URL is required")
    if not a.name.startswith("amb-") or not a.name.endswith((".jpg", ".jpeg", ".png", ".webp")) or "/" in a.name or "\\" in a.name:
        p.error("Image name must be a safe amb-*.jpg/jpeg/png/webp filename")
    if len(a.sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in a.sha256):
        p.error("A 64-character SHA-256 checksum is required")
    req = Request(a.url, headers={"User-Agent": "AMB-Image-Importer/1.0"})
    with urlopen(req, timeout=30) as response:
        data = response.read(12 * 1024 * 1024 + 1)
    if len(data) > 12 * 1024 * 1024:
        raise ValueError("Image exceeds 12 MB")
    if hashlib.sha256(data).hexdigest().lower() != a.sha256.lower():
        raise ValueError("SHA-256 mismatch; refusing to publish")
    signatures = {
        ".jpg": data.startswith(bytes.fromhex("ffd8ff")),
        ".jpeg": data.startswith(bytes.fromhex("ffd8ff")),
        ".png": data.startswith(bytes.fromhex("89504e470d0a1a0a")),
        ".webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
    }
    if not signatures[Path(a.name).suffix]:
        raise ValueError("Image bytes do not match file extension")
    destination = Path("assets/briefs") / a.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    destination.write_bytes(data)
    print(f"Saved {destination} ({len(data)} bytes), SHA-256 verified")

if __name__ == "__main__":
    main()
