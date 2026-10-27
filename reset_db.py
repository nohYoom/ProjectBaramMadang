#!/usr/bin/env python3
"""
Script to reset the SQLite database for Project Baram Madang.
Drops all existing tables and views, and re-initializes them according to schema.sql.

Usage:
    python reset_db.py [--no-seed]
"""

import sys
import argparse
from db import reset_database, get_db, DB_PATH

def main():
    parser = argparse.ArgumentParser(description="Reset Baram Madang SQL Database")
    parser.add_argument(
        '--no-seed',
        action='store_true',
        help='Skip seeding default constants (media_types, categories, site_name)'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("🔄 Resetting Baram Madang SQL Database...")
    print(f"📁 Target Database: {DB_PATH}")
    print("=" * 60)

    try:
        reset_database(seed_defaults=not args.no_seed)
        
        # Verify created tables and views
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name;")
            objects = cursor.fetchall()

        print("\n✅ Database reset successfully! Initialized objects:")
        for obj in objects:
            print(f"  • [{obj['type'].upper()}] {obj['name']}")

        if not args.no_seed:
            print("\n🌱 Seeded default constants into 'constant' table.")

        print("\nReady for manual dictionary insertion via insert_data.py!\n")

    except Exception as e:
        print(f"\n❌ Error resetting database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
