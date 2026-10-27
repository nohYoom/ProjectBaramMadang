"""
Database management helper module for Project Baram Madang.
Provides connection handling, schema initialization, and dictionary-based CRUD operations.
"""

import os
import re
import json
import sqlite3
from typing import Any, Dict, List, Optional, Union

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

# Read database name from config if available, default to 'school_media.db'
try:
    from config import Config
    DEFAULT_DB_NAME = getattr(Config, 'DATABASE', 'school_media.db')
except Exception:
    DEFAULT_DB_NAME = 'school_media.db'

DB_PATH = os.path.join(BASE_DIR, DEFAULT_DB_NAME)


def get_db(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys enabled and row_factory configured."""
    target_path = db_path or DB_PATH
    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database tables, indexes, and views from schema.sql."""
    with get_db(db_path) as conn:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())


def reset_database(db_path: Optional[str] = None, seed_defaults: bool = True) -> None:
    """
    Drop all existing tables, views, and indexes, and recreate them from schema.sql.
    Optionally seeds default constants from config.py.
    """
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        # Drop views
        cursor.execute("DROP VIEW IF EXISTS v_account_contributions;")
        cursor.execute("DROP VIEW IF EXISTS v_media;")
        
        # Drop tables
        cursor.execute("DROP TABLE IF EXISTS media;")
        cursor.execute("DROP TABLE IF EXISTS account;")
        cursor.execute("DROP TABLE IF EXISTS constant;")
        
        # Recreate schema
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
            
    if seed_defaults:
        seed_default_constants(db_path)


def seed_default_constants(db_path: Optional[str] = None) -> None:
    """Populate default constants from config.py."""
    media_types = ['articles', 'photos', 'videos']
    categories = ['science', 'campus', 'robotics', 'events', 'general']

    try:
        from config import Config
        media_types = getattr(Config, 'MEDIA_TYPES', media_types)
        categories = getattr(Config, 'CATEGORIES', categories)
    except Exception:
        pass

    defaults = [
        {
            'key': 'media_types',
            'value': json.dumps(media_types),
            'description': 'Supported media types for content uploads'
        },
        {
            'key': 'categories',
            'value': json.dumps(categories),
            'description': 'Content category filters'
        },
        {
            'key': 'site_name',
            'value': 'Baram Madang',
            'description': 'Platform site title'
        }
    ]

    for item in defaults:
        add_constant(item, db_path=db_path)


def sanitize_filename(name: str) -> str:
    """Sanitize title or filename for filesystem safety."""
    cleaned = re.sub(r'[^\w\-\.]', '_', name.strip())
    return re.sub(r'_+', '_', cleaned)


def build_media_vm_path(media_id: Union[int, str], title: str, extension: str = 'pdf') -> str:
    """
    Generate file path matching VM layout:
    media/[media id]/title.[file extension]
    """
    ext = extension.lstrip('.')
    clean_title = sanitize_filename(title)
    return f"media/{media_id}/{clean_title}.{ext}"


def add_account(data: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Insert or replace an account dictionary into the database.
    
    Accepts keys:
      - account_id (optional, auto-generated if omitted)
      - google_account_id / google_id
      - display_name / name / author_name
      - email
    """
    account_id = data.get('account_id') or data.get('id')
    google_account_id = data.get('google_account_id') or data.get('google_id')
    display_name = data.get('display_name') or data.get('name') or data.get('author_name')
    email = data.get('email')

    if not google_account_id:
        raise ValueError("Field 'google_account_id' is required for an account.")
    if not display_name:
        raise ValueError("Field 'display_name' is required for an account.")

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        if account_id:
            query = """
                INSERT INTO account (account_id, google_account_id, display_name, email)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(account_id) DO UPDATE SET
                    google_account_id = excluded.google_account_id,
                    display_name = excluded.display_name,
                    email = excluded.email;
            """
            cursor.execute(query, (account_id, google_account_id, display_name, email))
            assigned_id = account_id
        else:
            query = """
                INSERT INTO account (google_account_id, display_name, email)
                VALUES (?, ?, ?)
                ON CONFLICT(google_account_id) DO UPDATE SET
                    display_name = excluded.display_name,
                    email = excluded.email;
            """
            cursor.execute(query, (google_account_id, display_name, email))
            assigned_id = cursor.lastrowid

    return get_account(assigned_id, db_path=db_path)


def add_media(data: Dict[str, Any], db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Insert or replace a media dictionary into the database.
    
    Accepts keys:
      - media_id (optional, auto-generated if omitted)
      - type / media_type: 'articles', 'images', 'zines', etc.
      - title: Title of the media
      - filter: Category or filter tag (e.g. 'MUN', 'science')
      - publication_date / date: Publication date string (YYYY-MM-DD)
      - file_path / path / data: File path on VM (e.g. 'media/[media id]/title.pdf')
      - author_id / author: ID of author from account table
      - extension: (optional) If file_path is omitted, uses title + extension to generate VM path
    """
    media_id = data.get('media_id') or data.get('id')
    media_type = data.get('type') or data.get('media_type') or data.get('type of media')
    title = data.get('title')
    media_filter = data.get('filter') or data.get('category')
    pub_date = data.get('publication_date') or data.get('date') or data.get('publication date')
    file_path = data.get('file_path') or data.get('path') or data.get('data') or data.get('data for media')
    author_id = data.get('author_id') or data.get('author') or data.get('account_id')
    extension = data.get('extension') or data.get('ext') or 'pdf'

    if not media_type:
        raise ValueError("Field 'type' (media type) is required.")
    if not title:
        raise ValueError("Field 'title' is required.")

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        
        if media_id:
            # Generate file_path if not explicitly provided
            if not file_path:
                file_path = build_media_vm_path(media_id, title, extension)
                
            query = """
                INSERT INTO media (media_id, type, title, filter, publication_date, file_path, author_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(media_id) DO UPDATE SET
                    type = excluded.type,
                    title = excluded.title,
                    filter = excluded.filter,
                    publication_date = excluded.publication_date,
                    file_path = excluded.file_path,
                    author_id = excluded.author_id;
            """
            cursor.execute(query, (media_id, media_type, title, media_filter, pub_date, file_path, author_id))
            assigned_id = media_id
        else:
            query = """
                INSERT INTO media (type, title, filter, publication_date, file_path, author_id)
                VALUES (?, ?, ?, ?, ?, ?);
            """
            cursor.execute(query, (media_type, title, media_filter, pub_date, file_path, author_id))
            assigned_id = cursor.lastrowid
            
            # If file_path was not provided, set the standard VM path using assigned_id
            if not file_path:
                computed_path = build_media_vm_path(assigned_id, title, extension)
                cursor.execute("UPDATE media SET file_path = ? WHERE media_id = ?;", (computed_path, assigned_id))

    return get_media(assigned_id, db_path=db_path)


def add_constant(data: Union[Dict[str, Any], tuple], db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Insert or update a constant key-value record.
    Supports:
      - dict: {'key': 'site_name', 'value': 'Baram Madang', 'description': '...'}
      - dict: {'site_name': 'Baram Madang'} (key is the dict key)
    """
    if isinstance(data, dict):
        if 'key' in data and 'value' in data:
            key = str(data['key'])
            val = data['value']
            desc = data.get('description', '')
        else:
            # Format: {'key_name': value}
            key = list(data.keys())[0]
            val = data[key]
            desc = ''
    elif isinstance(data, (list, tuple)) and len(data) >= 2:
        key = str(data[0])
        val = data[1]
        desc = data[2] if len(data) > 2 else ''
    else:
        raise ValueError("Invalid constant format. Provide {'key': ..., 'value': ...} or {'key': value}.")

    # Stringify val if dict or list
    if isinstance(val, (dict, list)):
        val_str = json.dumps(val)
    else:
        val_str = str(val)

    with get_db(db_path) as conn:
        cursor = conn.cursor()
        query = """
            INSERT INTO constant (key, value, description)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                description = CASE WHEN excluded.description != '' THEN excluded.description ELSE constant.description END;
        """
        cursor.execute(query, (key, val_str, desc))

    return {'key': key, 'value': val_str, 'description': desc}


def get_account(account_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve an account by ID along with its list of contributed media."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM account WHERE account_id = ?;", (account_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        acc_dict = dict(row)
        
        # Fetch list of contributed articles/media
        cursor.execute("SELECT media_id, type, title, publication_date FROM media WHERE author_id = ?;", (account_id,))
        media_rows = cursor.fetchall()
        acc_dict['articles_contributed'] = [dict(m) for m in media_rows]
        return acc_dict


def get_media(media_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve media details by ID, including author display name."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM v_media WHERE media_id = ?;", (media_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_all_accounts(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all accounts with their list of contributed media."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT account_id FROM account ORDER BY account_id ASC;")
        ids = [r['account_id'] for r in cursor.fetchall()]
        return [get_account(aid, db_path=db_path) for aid in ids]


def get_all_media(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all media rows with author display names."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM v_media ORDER BY media_id ASC;")
        return [dict(r) for r in cursor.fetchall()]


def get_all_constants(db_path: Optional[str] = None) -> Dict[str, Any]:
    """Return all constants as a dictionary of key-value pairs."""
    with get_db(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM constant;")
        result = {}
        for row in cursor.fetchall():
            val = row['value']
            try:
                result[row['key']] = json.loads(val)
            except Exception:
                result[row['key']] = val
        return result
