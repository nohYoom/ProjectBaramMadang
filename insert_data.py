#!/usr/bin/env python3
"""
Manual Dictionary Insertion Script for Baram Madang SQL Database.

How to use:
1. Open this file and edit/add your dictionaries in the `MY_ACCOUNTS`, `MY_MEDIA`,
   and `MY_CONSTANTS` sections below.
2. Run this script in your terminal:
       python insert_data.py
3. The script will insert or update the records and display the database contents.

You can also view current records without inserting new ones:
       python insert_data.py --show
"""

import sys
import json
import argparse
from typing import Any, Dict, List, Union
from db import (
    add_account,
    add_media,
    add_constant,
    get_all_accounts,
    get_all_media,
    get_all_constants,
    build_media_vm_path,
    DB_PATH
)

# =========================================================================
# ✏️ MANUALLY ADD YOUR DICTIONARIES HERE
# =========================================================================

# -------------------------------------------------------------------------
# ACCOUNTS
# -------------------------------------------------------------------------
# Format A: Keyed by account_id (e.g. {1: {...}, 2: {...}})
# Format B: List of dicts (e.g. [{'account_id': 1, ...}])
#
# Fields:
#   - google_account_id (required): unique Google account ID / sub
#   - display_name (required): author name displayed on site
#   - email (optional)
# -------------------------------------------------------------------------
MY_ACCOUNTS: Union[Dict[Any, Dict[str, Any]], List[Dict[str, Any]]] = {
    1: {
        "google_account_id": "google_1082938491029384",
        "display_name": "Test Author",
        "email": "author@school.edu"
    },
    2: {
        "google_account_id": "google_2093847501928374",
        "display_name": "Campus Reporter Kim",
        "email": "kim@school.edu"
    }
}


# -------------------------------------------------------------------------
# MEDIA
# -------------------------------------------------------------------------
# Format A: Keyed by media_id (as in diagram "dictionary name is media id")
# Format B: List of dicts
#
# Fields:
#   - type: 'articles', 'images', 'zines', 'photos', 'videos'
#   - title: Title of the media
#   - filter: Tag / category filter (e.g. 'MUN', 'science', 'campus', 'robotics')
#   - publication_date: Date string (e.g. '2026-10-17')
#   - author_id: Reference to account_id
#   - file_path: (optional) Path on VM: 'media/[media id]/title.[extension]'
#   - extension: (optional) If file_path is omitted, automatically computes:
#                'media/[media_id]/[sanitized_title].[extension]'
# -------------------------------------------------------------------------
MY_MEDIA: Union[Dict[Any, Dict[str, Any]], List[Dict[str, Any]]] = {
    1: {
        "type": "articles",
        "title": "Sample Article Title",
        "filter": "MUN",
        "publication_date": "2026-10-17",
        "author_id": 1,
        "extension": "pdf"
        # Auto-generates file_path: media/1/Sample_Article_Title.pdf
    },
    2: {
        "type": "zines",
        "title": "School Autumn Zine",
        "filter": "campus",
        "publication_date": "2026-10-25",
        "author_id": 2,
        "file_path": "media/2/School_Autumn_Zine.epub"
    }
}


# -------------------------------------------------------------------------
# CONSTANTS ("cosntant" in diagram)
# -------------------------------------------------------------------------
# Key-value system settings, announcements, or custom metadata
# Format: {'key_name': 'value' or ['list', 'items'] or {'nested': 'dict'}}
# -------------------------------------------------------------------------
MY_CONSTANTS: Dict[str, Any] = {
    "welcome_message": "Welcome to Baram Madang School Media Archive",
    "featured_filter": "MUN"
}


# =========================================================================
# HELPER FUNCTIONS TO PROCESS DICTIONARIES
# =========================================================================

def insert_accounts_data(accounts_input: Union[Dict[Any, Dict[str, Any]], List[Dict[str, Any]]]):
    """Insert account dictionaries."""
    if not accounts_input:
        return []

    results = []
    if isinstance(accounts_input, dict):
        for acc_id, acc_data in accounts_input.items():
            item = dict(acc_data)
            if 'account_id' not in item and isinstance(acc_id, int):
                item['account_id'] = acc_id
            inserted = add_account(item)
            results.append(inserted)
    elif isinstance(accounts_input, list):
        for item in accounts_input:
            inserted = add_account(item)
            results.append(inserted)
    return results


def insert_media_data(media_input: Union[Dict[Any, Dict[str, Any]], List[Dict[str, Any]]]):
    """Insert media dictionaries."""
    if not media_input:
        return []

    results = []
    if isinstance(media_input, dict):
        for m_id, m_data in media_input.items():
            item = dict(m_data)
            if 'media_id' not in item and isinstance(m_id, int):
                item['media_id'] = m_id
            inserted = add_media(item)
            results.append(inserted)
    elif isinstance(media_input, list):
        for item in media_input:
            inserted = add_media(item)
            results.append(inserted)
    return results


def insert_constants_data(constants_input: Dict[str, Any]):
    """Insert constant key-value dictionaries."""
    if not constants_input:
        return []

    results = []
    for k, v in constants_input.items():
        if isinstance(v, dict) and 'value' in v:
            res = add_constant({'key': k, **v})
        else:
            res = add_constant({'key': k, 'value': v})
        results.append(res)
    return results


def print_database_contents():
    """Pretty-print all records currently stored in the database."""
    print("\n" + "=" * 70)
    print("📊 CURRENT SQL DATABASE STATE")
    print("=" * 70)

    # 1. Accounts
    accounts = get_all_accounts()
    print(f"\n👤 ACCOUNTS ({len(accounts)}):")
    if not accounts:
        print("   (No accounts yet)")
    else:
        for acc in accounts:
            contrib_count = len(acc.get('articles_contributed', []))
            print(f"   • Account ID {acc['account_id']}:")
            print(f"       Google ID:     {acc['google_account_id']}")
            print(f"       Display Name:  {acc['display_name']}")
            print(f"       Email:         {acc.get('email')}")
            print(f"       Contributions: {contrib_count} media item(s)")
            if contrib_count > 0:
                for c in acc['articles_contributed']:
                    print(f"         - [{c['type']}] #{c['media_id']} {c['title']} ({c.get('publication_date')})")

    # 2. Media
    media_items = get_all_media()
    print(f"\n📁 MEDIA ({len(media_items)}):")
    if not media_items:
        print("   (No media items yet)")
    else:
        for item in media_items:
            print(f"   • Media ID {item['media_id']}:")
            print(f"       Type:             {item['type']}")
            print(f"       Title:            {item['title']}")
            print(f"       Filter:           {item.get('filter')}")
            print(f"       Publication Date: {item.get('publication_date')}")
            print(f"       File Path (VM):   {item.get('file_path')}")
            print(f"       Author ID:        {item.get('author_id')} ({item.get('author_name', 'Unknown')})")

    # 3. Constants
    constants = get_all_constants()
    print(f"\n⚙️ CONSTANTS ({len(constants)}):")
    if not constants:
        print("   (No constants yet)")
    else:
        for k, v in constants.items():
            print(f"   • {k}: {v}")
    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Insert dictionaries into Baram Madang SQL database")
    parser.add_argument(
        '--show',
        action='store_true',
        help='Only print current database contents without adding new data'
    )
    args = parser.parse_args()

    print(f"Connecting to database: {DB_PATH}")

    if args.show:
        print_database_contents()
        return

    print("\n🚀 Inserting configured dictionaries into SQL...")

    try:
        inserted_accounts = insert_accounts_data(MY_ACCOUNTS)
        print(f"✅ Accounts: Processed {len(inserted_accounts)} record(s)")

        inserted_media = insert_media_data(MY_MEDIA)
        print(f"✅ Media:    Processed {len(inserted_media)} record(s)")

        inserted_consts = insert_constants_data(MY_CONSTANTS)
        print(f"✅ Constant: Processed {len(inserted_consts)} record(s)")

        print("\nAll dictionaries successfully inserted/updated!")
        print_database_contents()

    except Exception as e:
        print(f"\n❌ Insertion error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
