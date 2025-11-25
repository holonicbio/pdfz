"""ID generation utilities.

This module provides functions for generating unique identifiers
used throughout the system for documents, sessions, and operations.

All IDs follow a consistent format: prefix-random_hex

Usage:
    from docling_hybrid.common.ids import generate_id, generate_timestamp_id
    
    doc_id = generate_id("doc")      # "doc-a1b2c3d4"
    run_id = generate_timestamp_id("run")  # "run-1699564800-a1b2"
"""

import secrets
import time


def generate_id(prefix: str, length: int = 8) -> str:
    """Generate a unique ID with prefix.
    
    Creates a random hexadecimal ID with the specified prefix.
    IDs are suitable for use as document identifiers, session IDs, etc.
    
    Args:
        prefix: ID prefix (e.g., "doc", "sess", "page")
        length: Length of random part in characters (default: 8)
            Must be even number (uses hex encoding)
    
    Returns:
        ID string in format "prefix-randomhex"
    
    Examples:
        >>> generate_id("doc")
        'doc-7f4e3d2a'
        
        >>> generate_id("sess", length=12)
        'sess-a1b2c3d4e5f6'
        
        >>> # IDs are unique
        >>> id1 = generate_id("test")
        >>> id2 = generate_id("test")
        >>> id1 != id2
        True
    
    Note:
        The probability of collision for 8-character hex IDs is extremely low
        (1 in 4 billion for any two IDs). For higher assurance, use length=16.
    """
    if length < 2:
        length = 2
    if length % 2 != 0:
        length += 1  # Ensure even length for hex encoding
    
    random_part = secrets.token_hex(length // 2)
    return f"{prefix}-{random_part}"


def generate_timestamp_id(prefix: str, random_length: int = 4) -> str:
    """Generate ID with timestamp for temporal ordering.
    
    Creates an ID that includes a Unix timestamp, useful when IDs need
    to be sortable by creation time. The random suffix prevents collisions
    when multiple IDs are created in the same second.
    
    Args:
        prefix: ID prefix (e.g., "run", "batch")
        random_length: Length of random suffix in characters (default: 4)
    
    Returns:
        ID string in format "prefix-timestamp-randomhex"
    
    Examples:
        >>> generate_timestamp_id("run")
        'run-1699564800-a1b2'
        
        >>> generate_timestamp_id("batch", random_length=8)
        'batch-1699564800-a1b2c3d4'
        
        >>> # IDs are sortable by time (when compared as strings)
        >>> import time
        >>> id1 = generate_timestamp_id("run")
        >>> time.sleep(1)
        >>> id2 = generate_timestamp_id("run")
        >>> id1 < id2  # Earlier ID sorts before later ID
        True
    
    Note:
        Timestamp is Unix epoch time (seconds since 1970-01-01 UTC).
        Resolution is 1 second; use random suffix to prevent collisions
        within the same second.
    """
    if random_length < 2:
        random_length = 2
    if random_length % 2 != 0:
        random_length += 1
    
    timestamp = int(time.time())
    random_part = secrets.token_hex(random_length // 2)
    return f"{prefix}-{timestamp}-{random_part}"


def generate_doc_id(filename: str | None = None) -> str:
    """Generate a document ID, optionally incorporating filename.
    
    Creates a document ID that can optionally include a sanitized
    version of the filename for easier identification.
    
    Args:
        filename: Optional filename to incorporate (sanitized)
    
    Returns:
        Document ID string
    
    Examples:
        >>> generate_doc_id()
        'doc-a1b2c3d4'
        
        >>> generate_doc_id("my_paper.pdf")
        'doc-my_paper-a1b2c3d4'
    """
    if filename:
        # Sanitize filename: remove extension, replace special chars
        import re
        base = filename.rsplit(".", 1)[0]  # Remove extension
        base = re.sub(r"[^a-zA-Z0-9_-]", "_", base)  # Replace special chars
        base = base[:20]  # Limit length
        random_part = secrets.token_hex(4)
        return f"doc-{base}-{random_part}"
    else:
        return generate_id("doc")


def generate_page_id(doc_id: str, page_num: int) -> str:
    """Generate a page ID within a document.
    
    Creates a deterministic page ID based on document ID and page number.
    This allows page IDs to be reconstructed without storing them.
    
    Args:
        doc_id: Document ID
        page_num: Page number (1-indexed)
    
    Returns:
        Page ID string
    
    Examples:
        >>> generate_page_id("doc-a1b2c3d4", 1)
        'doc-a1b2c3d4:p1'
        
        >>> generate_page_id("doc-a1b2c3d4", 42)
        'doc-a1b2c3d4:p42'
    """
    return f"{doc_id}:p{page_num}"
