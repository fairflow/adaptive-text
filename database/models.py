import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

class DatabaseManager:
    def __init__(self, db_path: str = "adaptive_text.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Purchases table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                block_id TEXT NOT NULL,
                article_id TEXT NOT NULL,
                resolution_level INTEGER NOT NULL,
                formality INTEGER,
                reading_age INTEGER,
                purchase_date TEXT NOT NULL,
                cost REAL NOT NULL,
                UNIQUE(user_id, block_id, resolution_level)
            )
        """)
        
        # Content cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_hash TEXT NOT NULL,
                resolution INTEGER NOT NULL,
                formality INTEGER NOT NULL,
                reading_age INTEGER NOT NULL,
                transformed_text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                tokens_used INTEGER,
                model_version TEXT,
                UNIQUE(text_hash, resolution, formality, reading_age)
            )
        """)
        
        # Articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT,
                created_date TEXT NOT NULL,
                updated_date TEXT,
                metadata TEXT
            )
        """)
        
        # Blocks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocks (
                id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                original_content TEXT NOT NULL,
                block_type TEXT DEFAULT 'paragraph',
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        # User wallet table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                user_id TEXT PRIMARY KEY,
                balance REAL NOT NULL DEFAULT 0.0,
                currency TEXT DEFAULT 'credits',
                last_updated TEXT
            )
        """)
        
        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_purchases_user 
            ON purchases(user_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_hash 
            ON content_cache(text_hash)
        """)
        
        conn.commit()
        conn.close()

# Initialize on import
db_manager = DatabaseManager()
