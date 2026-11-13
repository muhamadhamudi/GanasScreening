import io, secrets
import qrcode
from flask import current_app, has_request_context, request

def new_token():
    return secrets.token_urlsafe(32)

def screening_url(token):
    base = current_app.config.get("PUBLIC_BASE_URL") or ""
    if base:
        return f"{base}/s/{token}"
    if has_request_context():
        return f"{request.host_url.rstrip('/')}/s/{token}"
    return f"{current_app.config.get('PREFERRED_URL_SCHEME', 'http')}://localhost:5000/s/{token}"

def qr_png_bytes(url):
    image = qrcode.make(url)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
