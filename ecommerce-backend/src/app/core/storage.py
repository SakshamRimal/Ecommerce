"""Async MinIO (S3 Signature V4) object storage helper for product image uploads.

Uploads binary image files to a MinIO bucket using pure async HTTP (`httpx.AsyncClient`)
and AWS Signature Version 4 (`AWS4-HMAC-SHA256`) so the event loop is never blocked.
Automatically creates the target bucket and enables anonymous public-read access on
first upload, with a local disk fallback if MinIO is unreachable.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
from urllib.parse import quote, urlsplit
import uuid

import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger("storage")

ALLOWED_IMAGE_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "image/avif": ".avif",
}
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
LOCAL_FALLBACK_DIR = Path("/tmp/commercify-uploads")

_bucket_initialized = False


def _sign(key: bytes, msg: str) -> bytes:
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_signature_key(secret_key: str, date_stamp: str, region: str, service: str) -> bytes:
    k_date = _sign(("AWS4" + secret_key).encode("utf-8"), date_stamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, service)
    return _sign(k_service, "aws4_request")


def _build_s3_v4_headers(
    *,
    method: str,
    endpoint: str,
    canonical_uri: str,
    canonical_querystring: str,
    payload: bytes,
    access_key: str,
    secret_key: str,
    region: str,
    content_type: str | None = None,
) -> dict[str, str]:
    parsed = urlsplit(endpoint)
    host = parsed.netloc
    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")
    payload_hash = hashlib.sha256(payload).hexdigest()

    headers_to_sign: dict[str, str] = {
        "host": host,
        "x-amz-content-sha256": payload_hash,
        "x-amz-date": amz_date,
    }
    if content_type:
        headers_to_sign["content-type"] = content_type

    sorted_keys = sorted(headers_to_sign.keys())
    canonical_headers = "".join(f"{k}:{headers_to_sign[k]}\n" for k in sorted_keys)
    signed_headers = ";".join(sorted_keys)

    canonical_request = "\n".join(
        [
            method.upper(),
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash,
        ]
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date_stamp}/{region}/s3/aws4_request"
    string_to_sign = "\n".join(
        [
            algorithm,
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ]
    )

    signing_key = _get_signature_key(secret_key, date_stamp, region, "s3")
    signature = hmac.new(
        signing_key, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    authorization = (
        f"{algorithm} Credential={access_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    out = {
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "Authorization": authorization,
    }
    if content_type:
        out["Content-Type"] = content_type
    return out


async def _ensure_bucket_Ready(client: httpx.AsyncClient) -> None:
    global _bucket_initialized
    if _bucket_initialized:
        return

    settings = get_settings()
    endpoint = settings.minio_endpoint.rstrip("/")
    bucket = settings.minio_bucket
    uri = f"/{quote(bucket)}"

    head_headers = _build_s3_v4_headers(
        method="HEAD",
        endpoint=endpoint,
        canonical_uri=uri,
        canonical_querystring="",
        payload=b"",
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        region=settings.minio_region,
    )
    resp = await client.head(f"{endpoint}{uri}", headers=head_headers)

    if resp.status_code == 404:
        put_headers = _build_s3_v4_headers(
            method="PUT",
            endpoint=endpoint,
            canonical_uri=uri,
            canonical_querystring="",
            payload=b"",
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            region=settings.minio_region,
        )
        create_resp = await client.put(f"{endpoint}{uri}", headers=put_headers)
        create_resp.raise_for_status()

    # Apply public-read policy so storefront browsers can load product images directly
    policy_doc = json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket}/*"],
                }
            ],
        }
    ).encode("utf-8")

    policy_headers = _build_s3_v4_headers(
        method="PUT",
        endpoint=endpoint,
        canonical_uri=uri,
        canonical_querystring="policy=",
        payload=policy_doc,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        region=settings.minio_region,
        content_type="application/json",
    )
    await client.put(
        f"{endpoint}{uri}?policy=",
        content=policy_doc,
        headers=policy_headers,
    )
    _bucket_initialized = True


async def upload_image_to_minio(
    filename: str | None,
    content: bytes,
    content_type: str,
) -> tuple[str, str, str]:
    """Upload an image to MinIO and return (image_url, bucket, object_key)."""
    settings = get_settings()
    ext = ALLOWED_IMAGE_CONTENT_TYPES.get(content_type.lower(), ".jpg")
    object_key = f"{uuid.uuid4().hex}{ext}"
    bucket = settings.minio_bucket
    endpoint = settings.minio_endpoint.rstrip("/")
    public_base = settings.minio_public_url.rstrip("/")
    uri = f"/{quote(bucket)}/{quote(object_key)}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await _ensure_bucket_Ready(client)
            put_headers = _build_s3_v4_headers(
                method="PUT",
                endpoint=endpoint,
                canonical_uri=uri,
                canonical_querystring="",
                payload=content,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                region=settings.minio_region,
                content_type=content_type,
            )
            resp = await client.put(
                f"{endpoint}{uri}",
                content=content,
                headers=put_headers,
            )
            resp.raise_for_status()
            image_url = f"{public_base}/{bucket}/{object_key}"
            logger.info(
                "product_image_uploaded_minio",
                bucket=bucket,
                object_key=object_key,
                size_bytes=len(content),
            )
            return image_url, bucket, object_key
    except Exception as exc:
        logger.warning(
            "minio_unavailable_using_local_fallback",
            error=str(exc),
            object_key=object_key,
        )
        LOCAL_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        (LOCAL_FALLBACK_DIR / object_key).write_bytes(content)
        return f"/api/v1/products/media/{object_key}", "local-fallback", object_key
