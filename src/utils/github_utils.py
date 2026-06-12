import re
from urllib.parse import urlparse

def parse_github_url(url: str) -> str:
    """
    Parses a GitHub URL and returns the repository name.
    Example: https://github.com/langchain-ai/langchain -> langchain-ai/langchain
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    parts = path.split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    raise ValueError(f"Invalid GitHub URL: {url}")
