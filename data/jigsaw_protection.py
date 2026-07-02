"""Jigsaw Partitioning protection module.

Generates NxN tile grids from source images, exposes each tile as an
individually protected asset with signed URLs, and builds randomized
manifests for the frontend.
"""

import os
import secrets
import time
import hashlib
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


def _limit_registry(max_entries: int = 500) -> None:
    if len(JIGSAW_TILE_REGISTRY) > max_entries:
        oldest = sorted(
            JIGSAW_TILE_REGISTRY.items(),
            key=lambda x: x[1]["created"],
        )[: len(JIGSAW_TILE_REGISTRY) - max_entries]
        for tile_id, _ in oldest:
            del JIGSAW_TILE_REGISTRY[tile_id]


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

                    tile_id = secrets.token_hex(8)
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

        manifest_tiles: List[Dict[str, Any]] = []
        for tile in tiles:
            tile_info: Dict[str, Any] = {
                "id": tile["id"],
                "row": tile["row"],
                "col": tile["col"],
                "width": tile["width"],
                "height": tile["height"],
                "grid_width": tile["grid_width"],
                "grid_height": tile["grid_height"],
                "image_width": tile["image_width"],
                "image_height": tile["image_height"],
                "placement_meta": {
                    "grid_row": tile["row"],
                    "grid_col": tile["col"],
                    "order_index": tile["row"] * tile["grid_width"] + tile["col"],
                },
            }

            if ENABLE_SIGNED_TILE_URLS:
                from data.protected_media import build_signed_url

                tile_url = build_signed_url(tile["id"], 60, url_for_func, "jigsaw_tile")
            else:
                tile_url = url_for_func("jigsaw_tile", tile_id=tile["id"])

            tile_info["tile_url"] = tile_url
            manifest_tiles.append(tile_info)

        if ENABLE_RANDOM_DOM_ORDER:
            import random

            random.shuffle(manifest_tiles)

        return {
            "grid_size": self.grid_size,
            "image_width": tiles[0]["image_width"],
            "image_height": tiles[0]["image_height"],
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
