"""Jigsaw Partitioning protection module.

Generates NxN tile grids from source images, exposes each tile as an
individually protected asset with signed URLs, and builds randomized
manifests for the frontend.
"""

import os
import secrets
import time
import hashlib
import random
from typing import Any, Dict, List, Optional
from io import BytesIO

from PIL import Image

# ---------------------------------------------------------------------------
# Configuration (environment-driven)
# ---------------------------------------------------------------------------
USE_TILED_DELIVERY = os.environ.get("USE_TILED_DELIVERY", "true").lower() == "true"
GRID_SIZE = int(os.environ.get("GRID_SIZE", "4"))
ENABLE_SIGNED_TILE_URLS = os.environ.get("ENABLE_SIGNED_TILE_URLS", "true").lower() == "true"
ENABLE_RANDOM_DOM_ORDER = os.environ.get("ENABLE_RANDOM_DOM_ORDER", "true").lower() == "true"

JIGSAW_TILE_DIR = os.path.join("static", ".jigsaw_tiles")
os.makedirs(JIGSAW_TILE_DIR, exist_ok=True)

# In-memory tile registry: tile_id -> metadata dict
JIGSAW_TILE_REGISTRY: Dict[str, Dict[str, Any]] = {}

# In-memory nonce registry: nonce -> {tile_ids, expires, consumed_tiles, fully_consumed}
JIGSAW_NONCE_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _limit_registry(max_entries: int = 500) -> None:
    if len(JIGSAW_TILE_REGISTRY) > max_entries:
        oldest = sorted(
            JIGSAW_TILE_REGISTRY.items(),
            key=lambda x: x[1]["created"],
        )[: len(JIGSAW_TILE_REGISTRY) - max_entries]
        for tile_id, _ in oldest:
            del JIGSAW_TILE_REGISTRY[tile_id]


def _cleanup_expired_nonces() -> None:
    now = time.time()
    expired = [k for k, v in JIGSAW_NONCE_REGISTRY.items() if v["expires"] < now]
    for k in expired:
        del JIGSAW_NONCE_REGISTRY[k]


def generate_tile_id() -> str:
    return secrets.token_hex(16)


class JigsawTileProvider:
    def __init__(self, image_path: str, grid_size: int = GRID_SIZE):
        self.image_path = image_path
        self.grid_size = grid_size
        self._tiles: Optional[List[Dict[str, Any]]] = None

    def generate_tiles(self) -> List[Dict[str, Any]]:
        if self._tiles is not None:
            return self._tiles

        tiles: List[Dict[str, Any]] = []

        with Image.open(self.image_path) as img:
            sw, sh = img.size
            tw = sw // self.grid_size
            th = sh // self.grid_size

            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    left = col * tw
                    upper = row * th
                    right = left + tw
                    lower = upper + th
                    tile_img = img.crop((left, upper, right, lower))

                    buf = BytesIO()
                    tile_img.save(buf, format="PNG")
                    buf.seek(0)
                    tile_bytes = buf.getvalue()

                    tile_id = generate_tile_id()
                    filename = f"{tile_id}.png"
                    filepath = os.path.join(JIGSAW_TILE_DIR, filename)
                    with open(filepath, "wb") as f:
                        f.write(tile_bytes)

                    entry: Dict[str, Any] = {
                        "id": tile_id,
                        "row": row,
                        "col": col,
                        "filename": filename,
                        "filepath": filepath,
                        "width": tw,
                        "height": th,
                        "grid_width": self.grid_size,
                        "grid_height": self.grid_size,
                        "image_width": sw,
                        "image_height": sh,
                        "bytes": tile_bytes,
                        "mime": "image/png",
                        "created": time.time(),
                    }

                    JIGSAW_TILE_REGISTRY[tile_id] = entry
                    tiles.append(entry)

        self._tiles = tiles
        _limit_registry()
        return tiles

    def build_tile_manifest(self, url_for_func, session_id: Optional[str] = None) -> Dict[str, Any]:
        tiles = self.generate_tiles()
        tile_ids = [t["id"] for t in tiles]
        nonce = create_manifest_nonce(tile_ids, ttl=30)

        orders = list(range(self.grid_size * self.grid_size))
        random.shuffle(orders)

        manifest_tiles: List[Dict[str, Any]] = []
        for idx, tile in enumerate(tiles):
            if ENABLE_SIGNED_TILE_URLS:
                from data.protected_media import build_signed_url

                tile_url = build_signed_url(tile["id"], 60, url_for_func, "jigsaw_tile")
            else:
                tile_url = url_for_func("jigsaw_tile", tile_id=tile["id"])

            sep = "&" if "?" in tile_url else "?"
            tile_url = f"{tile_url}{sep}nonce={nonce}"

            tile_info: Dict[str, Any] = {
                "id": tile["id"],
                "tile_url": tile_url,
                "row": tile["row"],
                "col": tile["col"],
            }

            manifest_tiles.append(tile_info)

        if ENABLE_RANDOM_DOM_ORDER:
            random.shuffle(manifest_tiles)

        return {
            "grid_size": self.grid_size,
            "image_width": tiles[0]["image_width"],
            "image_height": tiles[0]["image_height"],
            "nonce": nonce,
            "tiles": manifest_tiles,
        }

    @staticmethod
    def serve_tile(tile_id: str) -> Optional[Dict[str, Any]]:
        entry = JIGSAW_TILE_REGISTRY.get(tile_id)
        if not entry:
            return None
        return {
            "bytes": entry["bytes"],
            "mime": entry["mime"],
        }


def build_jigsaw_manifest(url_for_func, image_path: str, grid_size: int = GRID_SIZE) -> Dict[str, Any]:
    provider = JigsawTileProvider(image_path, grid_size)
    return provider.build_tile_manifest(url_for_func)


def serve_jigsaw_tile(tile_id: str) -> Optional[Dict[str, Any]]:
    return JigsawTileProvider.serve_tile(tile_id)


def create_manifest_nonce(tile_ids: List[str], ttl: int = 30) -> str:
    nonce = secrets.token_hex(32)
    expires = int(time.time()) + ttl
    JIGSAW_NONCE_REGISTRY[nonce] = {
        "tile_ids": set(tile_ids),
        "expires": expires,
        "consumed_tiles": set(),
        "fully_consumed": False,
    }
    _cleanup_expired_nonces()
    return nonce


def consume_nonce_for_tile(nonce: str, tile_id: str) -> bool:
    entry = JIGSAW_NONCE_REGISTRY.get(nonce)
    if not entry:
        return False
    if entry["fully_consumed"]:
        return False
    if entry["expires"] < time.time():
        del JIGSAW_NONCE_REGISTRY[nonce]
        return False
    if tile_id not in entry["tile_ids"]:
        return False
    if tile_id in entry["consumed_tiles"]:
        return False
    entry["consumed_tiles"].add(tile_id)
    if len(entry["consumed_tiles"]) == len(entry["tile_ids"]):
        entry["fully_consumed"] = True
    return True
