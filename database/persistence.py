import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Tuple

def get_connection(db_path: str = "adaptive_text.db") -> sqlite3.Connection:
    """Get database connection with row factory"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_text(text: str) -> str:
    """Generate SHA-256 hash of text"""
    return hashlib.sha256(text.encode()).hexdigest()

# Purchase operations
def record_purchase(user_id: str, block_id: str, article_id: str,
                   resolution: int, formality: int, reading_age: int,
                   cost: float) -> bool:
    """Record a block purchase"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO purchases
            (user_id, block_id, article_id, resolution_level,
             formality, reading_age, purchase_date, cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, block_id, article_id, resolution,
              formality, reading_age, datetime.now().isoformat(), cost))
        
        # Deduct from wallet
        cursor.execute("""
            UPDATE wallets SET balance = balance - ?,
            last_updated = ?
            WHERE user_id = ?
        """, (cost, datetime.now().isoformat(), user_id))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Purchase error: {e}")
        return False
    finally:
        conn.close()

def check_ownership(user_id: str, block_id: str, 
                   resolution: int) -> bool:
    """Check if user owns this block at this resolution"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 1 FROM purchases
        WHERE user_id = ? AND block_id = ? 
        AND resolution_level >= ?
    """, (user_id, block_id, resolution))
    
    result = cursor.fetchone() is not None
    conn.close()
    return result

def get_user_purchases(user_id: str) -> List[Dict]:
    """Get all purchases for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT block_id, article_id, resolution_level,
               purchase_date, cost
        FROM purchases
        WHERE user_id = ?
        ORDER BY purchase_date DESC
    """, (user_id,))
    
    purchases = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return purchases

# Cache operations
def get_cached_transform(text: str, resolution: int,
                        formality: int, reading_age: int) -> Optional[str]:
    """Retrieve cached transformation"""
    text_hash = hash_text(text)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT transformed_text FROM content_cache
        WHERE text_hash = ? AND resolution = ?
        AND formality = ? AND reading_age = ?
    """, (text_hash, resolution, formality, reading_age))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['transformed_text'] if result else None

def save_cached_transform(text: str, resolution: int, formality: int,
                         reading_age: int, transformed: str,
                         tokens_used: int, model: str):
    """Save transformation to cache"""
    text_hash = hash_text(text)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO content_cache
        (text_hash, resolution, formality, reading_age,
         transformed_text, timestamp, tokens_used, model_version)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (text_hash, resolution, formality, reading_age,
          transformed, datetime.now().isoformat(), tokens_used, model))
    
    conn.commit()
    conn.close()

# Wallet operations
def get_wallet_balance(user_id: str) -> float:
    """Get user wallet balance"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT balance FROM wallets WHERE user_id = ?
    """, (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result['balance'] if result else 0.0

def create_wallet(user_id: str, initial_balance: float = 100.0):
    """Create wallet for new user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR IGNORE INTO wallets (user_id, balance, last_updated)
        VALUES (?, ?, ?)
    """, (user_id, initial_balance, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
