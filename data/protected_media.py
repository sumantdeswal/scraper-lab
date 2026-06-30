import hashlib
import hmac
import os
import time
from typing import Any, Dict, List, Optional

from flask import request, session

PROTECTED_MEDIA_SECRET = os.environ.get("PROTECTED_MEDIA_SECRET", "protected-media-demo-secret").encode("utf-8")

PROTECTED_ASSETS: List[Dict[str, Any]] = [
    {
        "id": "signed-demo",
        "kind": "signed",
        "title": "Signed URL",
        "description": "A server-generated signature must accompany every request.",
        "image": "images/look1.jpg",
    },
    {
        "id": "expiring-demo",
        "kind": "expiring",
        "title": "Expiring URL",
        "description": "The link becomes invalid after a short countdown.",
        "image": "images/look2.jpg",
    },
    {
        "id": "cookie-demo",
        "kind": "cookie",
        "title": "Cookie-Protected",
        "description": "The asset only opens when the required browser cookie is present.",
        "image": "images/look3.jpg",
    },
    {
        "id": "auth-demo",
        "kind": "auth",
        "title": "Authorization",
        "description": "The browser must present a bearer token before the file can load.",
        "image": "images/look1.jpg",
    },
    {
        "id": "session-demo",
        "kind": "session",
        "title": "Session-Based",
        "description": "Access is only granted after the browser has established a session.",
        "image": "images/look2.jpg",
    },
    {
        "id": "expiring-video",
        "kind": "expiring",
        "title": "Expiring Video",
        "description": "A video file delivered through an expiring signed URL.",
        "image": "videos/demo.mp4",
    },
    {
        "id": "signed-hls",
        "kind": "signed",
        "title": "Signed HLS",
        "description": "An HLS manifest protected by a signature.",
        "image": "videos/hls/demo.m3u8",
    },
]


def _sign_payload(payload: str) -> str:
    return hmac.new(PROTECTED_MEDIA_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest()


def validate_expiration(expires: Optional[str]) -> bool:
    if not expires:
        return False

    try:
        expires_value = int(expires)
    except (TypeError, ValueError):
        return False

    return expires_value >= int(time.time())


def validate_signed_request(image_id: str, token: Optional[str], expires: Optional[str]) -> bool:
    if not token or not expires:
        return False

    if not validate_expiration(expires):
        return False

    expected_token = _sign_payload(f"{image_id}:{int(expires)}")
    return hmac.compare_digest(expected_token, token)


def validate_cookie_request() -> bool:
    return request.cookies.get("protected_media_cookie") == "authenticated"


def validate_session_request() -> bool:
    return bool(session.get("protected_media_session"))


def validate_authorization_request() -> bool:
    return request.headers.get("Authorization") == "Bearer demo-access-token"


def build_signed_url(image_id: str, expires_in: int, url_for_func, endpoint_name: str) -> str:
    expires = int(time.time()) + expires_in
    token = _sign_payload(f"{image_id}:{expires}")
    return url_for_func(endpoint_name, image_id=image_id, token=token, expires=expires)


def build_protected_manifest(url_for_func) -> List[Dict[str, Any]]:
    manifest = []

    for asset in PROTECTED_ASSETS:
        if asset["kind"] == "signed":
            image_url = build_signed_url(asset["id"], 90, url_for_func, "protected_media_signed_image")
        elif asset["kind"] == "expiring":
            image_url = build_signed_url(asset["id"], 20, url_for_func, "protected_media_expiring_image")
        elif asset["kind"] == "cookie":
            image_url = url_for_func("protected_media_cookie_image", image_id=asset["id"])
        elif asset["kind"] == "auth":
            image_url = url_for_func("protected_media_auth_image", image_id=asset["id"])
        else:
            image_url = url_for_func("protected_media_session_image", image_id=asset["id"])

        manifest.append(
            {
                "id": asset["id"],
                "kind": asset["kind"],
                "title": asset["title"],
                "description": asset["description"],
                "image": asset["image"],
                "image_url": image_url,
            }
        )

    return manifest


def initialize_protection_context(response) -> None:
    """Establish the demo session and cookie on the challenge page so the protected image requests can validate them."""
    session["protected_media_session"] = True
    response.set_cookie(
        "protected_media_cookie",
        "authenticated",
        httponly=True,
        samesite="Lax",
        secure=request.is_secure,
    )
    response.headers["Cache-Control"] = "no-store, private"


def get_asset(image_id: str) -> Optional[Dict[str, Any]]:
    for asset in PROTECTED_ASSETS:
        if asset["id"] == image_id:
            return asset
    return None


def serve_protected_image(image_id: str, policy: str) -> Optional[object]:
    """Return the static file for an image when the request passes the appropriate protection check."""
    if policy in {"signed", "expiring"}:
        # Signed and expiring URLs require a server-side signature that must match the image id and expiry timestamp.
        if not validate_signed_request(
            image_id,
            request.args.get("token"),
            request.args.get("expires"),
        ):
            return False

    asset = get_asset(image_id)
    if asset is None:
        return None

    if policy == "cookie":
        # Cookie-protected images are only accessible when the browser has the expected session cookie set.
        if not validate_cookie_request():
            return False
    elif policy == "auth":
        # Authorization-protected images require a bearer token in the request headers.
        if not validate_authorization_request():
            return False
    elif policy == "session":
        # Session-based protection relies on the browser having established a server-side session.
        if not validate_session_request():
            return False

    return asset["image"]
