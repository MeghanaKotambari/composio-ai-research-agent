"""
Documentation Cache for the AI Research Agent.

Caches documentation by URL inside output/cache/ to avoid
downloading the same documentation more than once during a run.

All stages (Fetch, Verification, Retry, Analytics) share the same cache.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)


class DocumentationCache:
    """
    Disk-based cache for fetched documentation pages.
    
    Caches by URL hash in output/cache/ directory.
    Thread-safe for sequential usage.
    """

    def __init__(self, cache_dir: Optional[Path] = None) -> None:
        """
        Initialize the documentation cache.
        
        Args:
            cache_dir: Directory for cache files (defaults to output/cache/)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else (
            settings.OUTPUT_DIR / "cache"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Documentation cache initialized at {self.cache_dir}")

    def _url_to_key(self, url: str) -> str:
        """Convert a URL to a cache key (hashed filename)."""
        normalized = url.strip().lower()
        if not normalized.startswith(("http://", "https://")):
            normalized = "https://" + normalized
        url_hash = hashlib.md5(normalized.encode()).hexdigest()
        return url_hash

    def _cache_path(self, key: str) -> Path:
        """Get the cache file path for a given key."""
        return self.cache_dir / f"{key}.json"

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached documentation for a URL.
        
        Args:
            url: The documentation URL
            
        Returns:
            Cached result dict if found, None otherwise
        """
        # Check memory cache first
        if url in self._memory_cache:
            logger.debug(f"Cache hit (memory): {url}")
            return self._memory_cache[url]

        # Check disk cache
        key = self._url_to_key(url)
        cache_file = self._cache_path(key)

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._memory_cache[url] = data
                logger.debug(f"Cache hit (disk): {url}")
                return data
            except Exception as e:
                logger.warning(f"Failed to read cache for {url}: {e}")
                return None

        logger.debug(f"Cache miss: {url}")
        return None

    def set(self, url: str, data: Dict[str, Any]) -> None:
        """
        Store documentation in the cache.
        
        Args:
            url: The documentation URL
            data: The result dict to cache
        """
        # Store in memory
        self._memory_cache[url] = data

        # Store on disk
        key = self._url_to_key(url)
        cache_file = self._cache_path(key)

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.debug(f"Cached: {url} -> {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to write cache for {url}: {e}")

    def has(self, url: str) -> bool:
        """Check if a URL is cached."""
        return self.get(url) is not None

    def clear(self) -> None:
        """Clear all cached documentation."""
        self._memory_cache.clear()
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        logger.info("Documentation cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        disk_files = list(self.cache_dir.glob("*.json"))
        return {
            "memory_entries": len(self._memory_cache),
            "disk_files": len(disk_files),
            "cache_dir": str(self.cache_dir),
        }