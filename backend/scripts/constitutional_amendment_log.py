#!/usr/bin/env python3
"""
Constitutional Amendment Logging System

This script provides logging functionality for constitutional amendments,
storing amendment attempts in SQLite database.
"""

import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Database schema for amendment logging
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS constitutional_amendments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    amendment_id TEXT UNIQUE NOT NULL,
    amendment_type TEXT NOT NULL,
    title TEXT,
    description TEXT,
    author_id TEXT,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    validation_results TEXT,
    changed_files TEXT,
    created_at_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_amendments_amendment_id ON constitutional_amendments(amendment_id);
CREATE INDEX IF NOT EXISTS idx_amendments_type ON constitutional_amendments(amendment_type);
CREATE INDEX IF NOT EXISTS idx_amendments_status ON constitutional_amendments(status);
CREATE INDEX IF NOT EXISTS idx_amendments_created_at ON constitutional_amendments(created_at);
"""


class ConstitutionalAmendmentLog:
    """SQLite-based logging system for constitutional amendments."""
    
    def __init__(self, db_path: str = "constitutional_amendment_log.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the amendment logging database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript(DB_SCHEMA)
        
        conn.commit()
        conn.close()
        
        print(f"✅ Amendment logging database initialized: {self.db_path}")
    
    def log_amendment(self, amendment_id: str, amendment_type: str, status: str, 
                     title: Optional[str] = None, description: Optional[str] = None,
                     author_id: Optional[str] = None, validation_results: Optional[Dict] = None,
                     changed_files: Optional[List[str]] = None) -> bool:
        """Log an amendment attempt to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Prepare data
            created_at = datetime.now().isoformat()
            validation_results_json = json.dumps(validation_results) if validation_results else None
            changed_files_json = json.dumps(changed_files) if changed_files else None
            
            # Insert amendment record
            cursor.execute('''
                INSERT OR REPLACE INTO constitutional_amendments (
                    amendment_id, amendment_type, title, description, author_id,
                    created_at, status, validation_results, changed_files
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                amendment_id,
                amendment_type,
                title,
                description,
                author_id,
                created_at,
                status,
                validation_results_json,
                changed_files_json
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Amendment logged: {amendment_id} ({amendment_type}) - {status}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to log amendment: {e}")
            return False
    
    def fetch_amendments(self, limit: Optional[int] = None, 
                        amendment_type: Optional[str] = None,
                        status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch amendments from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build query
            query = "SELECT * FROM constitutional_amendments WHERE 1=1"
            params = []
            
            if amendment_type:
                query += " AND amendment_type = ?"
                params.append(amendment_type)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY created_at DESC"
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            
            # Convert to list of dictionaries
            amendments = []
            for row in rows:
                amendment = dict(zip(columns, row))
                
                # Parse JSON fields
                if amendment.get('validation_results'):
                    try:
                        amendment['validation_results'] = json.loads(amendment['validation_results'])
                    except json.JSONDecodeError:
                        amendment['validation_results'] = None
                
                if amendment.get('changed_files'):
                    try:
                        amendment['changed_files'] = json.loads(amendment['changed_files'])
                    except json.JSONDecodeError:
                        amendment['changed_files'] = None
                
                amendments.append(amendment)
            
            conn.close()
            return amendments
            
        except Exception as e:
            print(f"❌ Failed to fetch amendments: {e}")
            return []
    
    def get_amendment(self, amendment_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific amendment by ID."""
        amendments = self.fetch_amendments()
        for amendment in amendments:
            if amendment['amendment_id'] == amendment_id:
                return amendment
        return None
    
    def update_amendment_status(self, amendment_id: str, status: str) -> bool:
        """Update the status of an amendment."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE constitutional_amendments 
                SET status = ? 
                WHERE amendment_id = ?
            ''', (status, amendment_id))
            
            if cursor.rowcount == 0:
                print(f"⚠️  No amendment found with ID: {amendment_id}")
                conn.close()
                return False
            
            conn.commit()
            conn.close()
            
            print(f"✅ Amendment status updated: {amendment_id} -> {status}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update amendment status: {e}")
            return False
    
    def get_amendment_stats(self) -> Dict[str, Any]:
        """Get statistics about amendments."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total amendments
            cursor.execute("SELECT COUNT(*) FROM constitutional_amendments")
            total_amendments = cursor.fetchone()[0]
            
            # Amendments by type
            cursor.execute('''
                SELECT amendment_type, COUNT(*) 
                FROM constitutional_amendments 
                GROUP BY amendment_type
            ''')
            amendments_by_type = dict(cursor.fetchall())
            
            # Amendments by status
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM constitutional_amendments 
                GROUP BY status
            ''')
            amendments_by_status = dict(cursor.fetchall())
            
            # Recent amendments (last 30 days)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM constitutional_amendments 
                WHERE created_at >= datetime('now', '-30 days')
            ''')
            recent_amendments = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_amendments": total_amendments,
                "amendments_by_type": amendments_by_type,
                "amendments_by_status": amendments_by_status,
                "recent_amendments": recent_amendments
            }
            
        except Exception as e:
            print(f"❌ Failed to get amendment stats: {e}")
            return {}
    
    def display_amendments(self, amendments: List[Dict[str, Any]]) -> None:
        """Display a list of amendments."""
        if not amendments:
            print("📋 No amendments found")
            return
        
        print(f"📋 AMENDMENTS ({len(amendments)} found)")
        print("=" * 50)
        
        for amendment in amendments:
            print(f"\n🔖 Amendment ID: {amendment['amendment_id']}")
            print(f"   Type: {amendment['amendment_type']}")
            print(f"   Status: {amendment['status']}")
            print(f"   Created: {amendment['created_at']}")
            
            if amendment.get('title'):
                print(f"   Title: {amendment['title']}")
            
            if amendment.get('author_id'):
                print(f"   Author: {amendment['author_id']}")
            
            if amendment.get('changed_files'):
                print(f"   Changed Files: {len(amendment['changed_files'])}")
    
    def display_stats(self, stats: Dict[str, Any]) -> None:
        """Display amendment statistics."""
        print("📊 AMENDMENT STATISTICS")
        print("=" * 25)
        print(f"Total Amendments: {stats.get('total_amendments', 0)}")
        print(f"Recent Amendments (30 days): {stats.get('recent_amendments', 0)}")
        
        if stats.get('amendments_by_type'):
            print(f"\nBy Type:")
            for amendment_type, count in stats['amendments_by_type'].items():
                print(f"  {amendment_type}: {count}")
        
        if stats.get('amendments_by_status'):
            print(f"\nBy Status:")
            for status, count in stats['amendments_by_status'].items():
                print(f"  {status}: {count}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Constitutional Amendment Logging System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python constitutional_amendment_log.py --log --id amendment_001 --type core-principle --status pending
  python constitutional_amendment_log.py --fetch --limit 10
  python constitutional_amendment_log.py --fetch --type core-principle
  python constitutional_amendment_log.py --stats
  python constitutional_amendment_log.py --get amendment_001
        """
    )
    
    parser.add_argument(
        '--log', '-l',
        action='store_true',
        help='Log an amendment'
    )
    
    parser.add_argument(
        '--fetch', '-f',
        action='store_true',
        help='Fetch amendments'
    )
    
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show amendment statistics'
    )
    
    parser.add_argument(
        '--get', '-g',
        help='Get specific amendment by ID'
    )
    
    parser.add_argument(
        '--id', '-i',
        help='Amendment ID (for logging)'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['core-principle', 'implementation', 'feature', 'documentation'],
        help='Amendment type (for logging)'
    )
    
    parser.add_argument(
        '--status', '-u',
        choices=['pending', 'approved', 'rejected', 'in_review'],
        help='Amendment status (for logging)'
    )
    
    parser.add_argument(
        '--title', '-n',
        help='Amendment title (for logging)'
    )
    
    parser.add_argument(
        '--description', '-d',
        help='Amendment description (for logging)'
    )
    
    parser.add_argument(
        '--author', '-a',
        help='Amendment author ID (for logging)'
    )
    
    parser.add_argument(
        '--limit', '-m',
        type=int,
        help='Limit number of amendments to fetch'
    )
    
    parser.add_argument(
        '--filter-type', '-y',
        choices=['core-principle', 'implementation', 'feature', 'documentation'],
        help='Filter amendments by type (for fetch)'
    )
    
    parser.add_argument(
        '--filter-status', '-x',
        choices=['pending', 'approved', 'rejected', 'in_review'],
        help='Filter amendments by status (for fetch)'
    )
    
    args = parser.parse_args()
    
    logger = ConstitutionalAmendmentLog()
    
    if args.log:
        if not args.id or not args.type or not args.status:
            print("❌ --log requires --id, --type, and --status")
            sys.exit(1)
        
        success = logger.log_amendment(
            amendment_id=args.id,
            amendment_type=args.type,
            status=args.status,
            title=args.title,
            description=args.description,
            author_id=args.author
        )
        
        if not success:
            sys.exit(1)
    
    elif args.fetch:
        amendments = logger.fetch_amendments(
            limit=args.limit,
            amendment_type=args.filter_type,
            status=args.filter_status
        )
        logger.display_amendments(amendments)
    
    elif args.stats:
        stats = logger.get_amendment_stats()
        logger.display_stats(stats)
    
    elif args.get:
        amendment = logger.get_amendment(args.get)
        if amendment:
            logger.display_amendments([amendment])
        else:
            print(f"❌ Amendment not found: {args.get}")
            sys.exit(1)
    
    else:
        print("❌ Must specify one of: --log, --fetch, --stats, or --get")
        sys.exit(1)


if __name__ == "__main__":
    main()
