"""Retrieve public HTML job advertisements with conservative URL checks."""
import ipaddress
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

MAX_BYTES = 1_500_000
MAX_TEXT_CHARS = 24_000
MAX_REDIRECTS = 3


def _validate_public_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS job advertisement URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not supported.")
    if parsed.port not in (None, 80, 443):
        raise ValueError("Only standard HTTP/HTTPS ports are supported.")
    host = parsed.hostname
    if host.lower() in ("localhost", "localhost.localdomain") or host.lower().endswith(".local"):
        raise ValueError("Local network URLs are not allowed.")
    try:
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("The website hostname could not be resolved.") from exc
    if not addresses:
        raise ValueError("The website hostname could not be resolved.")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Local, private, or reserved network addresses are not allowed.")
    return url


def fetch_job_description(url):
    """Return cleaned job advertisement text; raise ValueError for unsupported pages."""
    url = url.strip()
    session = requests.Session()
    session.trust_env = False  # Avoid using proxy settings supplied by the environment.
    session.headers.update({"User-Agent": "Mozilla/5.0 (compatible; JobApplicationAssistant/1.0)"})
    try:
        for _ in range(MAX_REDIRECTS + 1):
            _validate_public_url(url)
            try:
                with session.get(url, timeout=(5, 12), allow_redirects=False, stream=True) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location")
                        if not location:
                            raise ValueError("The website redirected without a destination.")
                        url = urljoin(url, location)
                        continue
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "text/html" not in content_type:
                        raise ValueError("This link does not return an HTML page. Paste the job description instead.")
                    data = bytearray()
                    for part in response.iter_content(chunk_size=16384):
                        data.extend(part)
                        if len(data) > MAX_BYTES:
                            raise ValueError("The webpage is too large. Paste the job description instead.")
                    response.encoding = response.encoding or "utf-8"
                    html = bytes(data).decode(response.encoding, errors="replace")
                    soup = BeautifulSoup(html, "html.parser")
                    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg", "form"]):
                        tag.decompose()
                    main = soup.find("main") or soup.find("article") or soup.body or soup
                    text = "\n".join(line.strip() for line in main.get_text("\n").splitlines() if line.strip())
                    if len(text) < 150:
                        raise ValueError("Not enough readable job description text was found. Paste it manually instead.")
                    return text[:MAX_TEXT_CHARS], url
            except requests.RequestException as exc:
                raise ValueError("Unable to read this webpage. Try pasting the job description instead.") from exc
        raise ValueError("The website redirected too many times. Paste the job description instead.")
    finally:
        session.close()
