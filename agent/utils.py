"""
Utility functions for the AI Research Agent.

Provides helper functions for common operations including:
- JSON reading/writing
- CSV export
- URL validation
- Retry mechanisms

All functions are designed to be reusable and extensible.
"""

import json
import csv
import re
import time
import hashlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from functools import wraps

import requests
from urllib.parse import urlparse


T = TypeVar("T")


# ============================================================================
# JSON Operations
# ============================================================================


def read_json(file_path: Union[str, Path], encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        encoding: File encoding (default: utf-8)
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, "r", encoding=encoding) as f:
        return json.load(f)


def write_json(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    indent: int = 2,
    ensure_ascii: bool = False,
) -> None:
    """
    Write data to a JSON file.
    
    Args:
        data: Data to write
        file_path: Path to the output JSON file
        encoding: File encoding (default: utf-8)
        indent: JSON indentation level (default: 2)
        ensure_ascii: If True, escape non-ASCII characters (default: False)
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)


def append_json(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    encoding: str = "utf-8",
) -> None:
    """
    Append data to a JSON file (as a new line in JSONL format).
    
    Args:
        data: Data to append
        file_path: Path to the JSONL file
        encoding: File encoding (default: utf-8)
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, "a", encoding=encoding) as f:
        f.write(json.dumps(data, ensure_ascii=False, default=str) + "\n")


# ============================================================================
# CSV Operations
# ============================================================================


def export_to_csv(
    data: List[Dict[str, Any]],
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> None:
    """
    Export list of dictionaries to CSV file.
    
    Args:
        data: List of dictionaries to export
        file_path: Path to the output CSV file
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter (default: comma)
        
    Raises:
        ValueError: If data is empty or not a list
    """
    if not data or not isinstance(data, list):
        raise ValueError("Data must be a non-empty list of dictionaries")
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract fieldnames from the first item
    fieldnames = list(data[0].keys())
    
    with open(file_path, "w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


def read_csv(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    delimiter: str = ",",
) -> List[Dict[str, str]]:
    """
    Read CSV file and return as list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter (default: comma)
        
    Returns:
        List of dictionaries representing CSV rows
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    with open(file_path, "r", encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


# ============================================================================
# URL Validation
# ============================================================================


def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([
            result.scheme in ["http", "https"],
            result.netloc,
        ])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize URL by adding https:// if missing.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL with scheme
    """
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def get_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        parsed = urlparse(normalize_url(url))
        return parsed.netloc.lower()
    except Exception:
        return ""


# ============================================================================
# Retry Mechanisms
# ============================================================================


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
) -> Callable:
    """
    Decorator for retrying function execution with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Multiplier for delay after each retry (default: 2.0)
        exceptions: Tuple of exceptions to catch and retry (default: Exception)
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry(max_attempts=3, delay=1.0, backoff=2.0)
        def fetch_data():
            # Your code here
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


def retry_with_logger(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    logger: Optional[Callable] = None,
) -> Callable:
    """
    Decorator for retrying with logging support.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
        logger: Optional logging function
        
    Returns:
        Decorated function with retry and logging logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if logger:
                        logger(
                            f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}"
                        )
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


# ============================================================================
# Hashing and ID Generation
# ============================================================================


def generate_hash(text: str, algorithm: str = "md5") -> str:
    """
    Generate hash for a given string.
    
    Args:
        text: String to hash
        algorithm: Hash algorithm (default: md5)
        
    Returns:
        Hexadecimal hash string
    """
    hash_func = getattr(hashlib, algorithm)
    return hash_func(text.encode()).hexdigest()


def generate_id(prefix: str = "app") -> str:
    """
    Generate unique identifier with timestamp.
    
    Args:
        prefix: Prefix for the ID (default: "app")
        
    Returns:
        Unique identifier string
    """
    timestamp = int(time.time() * 1000)
    return f"{prefix}_{timestamp}"


# ============================================================================
# Data Transformation
# ============================================================================


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    separator: str = "_",
) -> Dict[str, Any]:
    """
    Flatten nested dictionary.
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator (default: "_")
        
    Returns:
        Flattened dictionary
    """
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: List[T], chunk_size: int) -> List[List[T]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    # Remove extra whitespace
    text = " ".join(text.split())
    # Remove special characters (keep alphanumeric, spaces, and common punctuation)
    text = re.sub(r"[^\w\s\-.,!?@#$%^&*()+=]", "", text)
    return text.strip()


# ============================================================================
# HTTP Utilities
# ============================================================================


def make_request(
    url: str,
    method: str = "GET",
    timeout: int = 30,
    headers: Optional[Dict[str, str]] = None,
    **kwargs: Any,
) -> requests.Response:
    """
    Make HTTP request with error handling.
    
    Args:
        url: URL to request
        method: HTTP method (default: GET)
        timeout: Request timeout in seconds (default: 30)
        headers: Optional request headers
        **kwargs: Additional arguments for requests
        
    Returns:
        Response object
        
    Raises:
        requests.RequestException: If request fails
    """
    if headers is None:
        headers = {}
    
    response = requests.request(
        method=method,
        url=url,
        timeout=timeout,
        headers=headers,
        **kwargs,
    )
    response.raise_for_status()
    return response