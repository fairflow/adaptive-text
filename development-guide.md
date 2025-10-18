# Adaptive Text Resolution System - Development Guide

## Project Overview

This guide walks you through building a production-ready adaptive text resolution system with fine-grained user controls, micropayments, and content persistence. The system automatically adjusts text detail, formality, and reading level based on user preferences.

---

## Phase 1: Environment Setup (Week 1)

### 1.1 Install Core Dependencies

```bash
# Create project directory
mkdir adaptive-text-system
cd adaptive-text-system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install streamlit openai anthropic sqlite3
pip freeze > requirements.txt
```

### 1.2 Get API Keys

**OpenAI** (recommended for starting):
1. Visit https://platform.openai.com/api-keys
2. Create new secret key
3. Copy key starting with `sk-`
4. Set environment variable: `export OPENAI_API_KEY="sk-..."`

**Anthropic Claude** (alternative):
1. Visit https://console.anthropic.com/
2. Get API key
3. Set: `export ANTHROPIC_API_KEY="sk-ant-..."`

### 1.3 Project Structure

```
adaptive-text-system/
├── README.md
├── requirements.txt
├── adaptive_text_demo.py          # Streamlit demo (no API)
├── adaptive_text_integration.py   # Production integration
├── config.py                      # Configuration
├── database/
│   ├── __init__.py
│   ├── models.py                  # Database schemas
│   └── persistence.py             # DB operations
├── processors/
│   ├── __init__.py
│   ├── text_transformer.py        # LLM integration
│   └── cache_manager.py           # Caching logic
├── ui/
│   ├── __init__.py
│   ├── components.py              # Reusable UI widgets
│   └── pages.py                   # Page layouts
└── tests/
    ├── test_transform.py
    └── test_persistence.py
```

---

## Phase 2: Database Layer (Week 1-2)

### 2.1 Create Database Schemas

**File: `database/models.py`**

```python
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
```

### 2.2 Create Persistence Functions

**File: `database/persistence.py`**

```python
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
```

---

## Phase 3: Text Transformation Engine (Week 2-3)

### 3.1 LLM Integration

**File: `processors/text_transformer.py`**

```python
import openai
import os
from typing import Dict, Optional
from database.persistence import (
    get_cached_transform, save_cached_transform
)

class TextTransformer:
    """Transform text using LLM with caching"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 provider: str = "openai"):
        self.provider = provider
        
        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.client = openai.OpenAI(api_key=self.api_key)
            self.model = "gpt-4o-mini"
        elif provider == "anthropic":
            import anthropic
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.client = anthropic.Anthropic(api_key=self.api_key)
            self.model = "claude-3-5-sonnet-20241022"
    
    def transform(self, text: str, resolution: int = 2,
                 formality: int = 5, reading_age: int = 14) -> Dict:
        """
        Transform text with specified parameters
        
        Returns dict with: text, cached, tokens_used, model
        """
        
        # Check cache first
        cached = get_cached_transform(text, resolution, 
                                     formality, reading_age)
        if cached:
            return {
                "text": cached,
                "cached": True,
                "tokens_used": 0,
                "model": self.model
            }
        
        # Build transformation prompt
        prompt = self._build_prompt(text, resolution, 
                                   formality, reading_age)
        
        # Call LLM
        if self.provider == "openai":
            result = self._transform_openai(prompt)
        elif self.provider == "anthropic":
            result = self._transform_anthropic(prompt)
        
        # Save to cache
        save_cached_transform(
            text, resolution, formality, reading_age,
            result["text"], result["tokens_used"], self.model
        )
        
        result["cached"] = False
        return result
    
    def _build_prompt(self, text: str, resolution: int,
                     formality: int, reading_age: int) -> str:
        """Build transformation prompt"""
        
        resolution_map = {
            0: "Create a brief summary (20-30% of original)",
            1: "Create a condensed version (50% of original)",
            2: "Rewrite maintaining all information",
            3: "Expand with additional context and examples"
        }
        
        formality_desc = self._formality_description(formality)
        reading_desc = self._reading_level_description(reading_age)
        
        return f"""Transform this text with these requirements:

DETAIL LEVEL: {resolution_map[resolution]}
FORMALITY: {formality_desc}
READING LEVEL: {reading_desc}

RULES:
- Preserve all factual information
- Maintain logical structure
- Output ONLY the transformed text
- Do not add new information

ORIGINAL TEXT:
{text}

TRANSFORMED TEXT:"""
    
    def _formality_description(self, formality: int) -> str:
        if formality <= 3:
            return "Very casual, conversational. Use contractions, simple words."
        elif formality <= 5:
            return "Neutral professional tone. Clear and direct."
        elif formality <= 7:
            return "Formal business style. Avoid contractions."
        else:
            return "Very formal academic tone. Sophisticated vocabulary."
    
    def _reading_level_description(self, age: int) -> str:
        if age <= 10:
            return "Elementary (Grade 3-5). Very simple sentences."
        elif age <= 12:
            return "Middle school (Grade 6-8). Clear, accessible."
        elif age <= 15:
            return "High school (Grade 9-10). Standard complexity."
        else:
            return "College level (Grade 11+). Complex concepts OK."
    
    def _transform_openai(self, prompt: str) -> Dict:
        """Transform using OpenAI"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert text transformer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return {
            "text": response.choices[0].message.content.strip(),
            "tokens_used": response.usage.total_tokens,
            "model": self.model
        }
    
    def _transform_anthropic(self, prompt: str) -> Dict:
        """Transform using Anthropic Claude"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "text": response.content[0].text.strip(),
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "model": self.model
        }
```

---

## Phase 4: Streamlit Interface (Week 3-4)

### 4.1 Main Application

**File: `adaptive_text_demo.py`**

Use the complete code provided earlier. Key sections:

1. **Session State Management**
```python
if 'wallet_balance' not in st.session_state:
    st.session_state.wallet_balance = 100.0
if 'purchased_blocks' not in st.session_state:
    st.session_state.purchased_blocks = set()
```

2. **UI Controls**
```python
resolution = st.sidebar.slider("Resolution", 0, 3, 1)
formality = st.sidebar.slider("Formality", 1, 10, 5)
reading_age = st.sidebar.slider("Reading Age", 8, 18, 14)
```

3. **Content Display Logic**
```python
for block in article_blocks:
    cost = calculate_cost(resolution, formality, reading_age)
    is_owned = check_ownership(user_id, block_id, resolution)
    
    if is_owned:
        # Show full content
        st.markdown(transformed_content)
        st.download_button("Download", data=content)
    else:
        # Show preview + unlock button
        st.markdown(preview)
        if st.button(f"Unlock {cost} credits"):
            purchase_block(...)
```

---

## Phase 5: Testing & Optimization (Week 4-5)

### 5.1 Unit Tests

**File: `tests/test_transform.py`**

```python
import pytest
from processors.text_transformer import TextTransformer

def test_summarization():
    transformer = TextTransformer()
    text = "Long sample text..." * 50
    
    result = transformer.transform(text, resolution=0)
    
    assert len(result["text"]) < len(text) * 0.4
    assert "text" in result
    assert "tokens_used" in result

def test_formality_levels():
    transformer = TextTransformer()
    text = "Hey dude, check this out!"
    
    casual = transformer.transform(text, formality=1)
    formal = transformer.transform(text, formality=10)
    
    assert casual["text"] != formal["text"]

def test_caching():
    transformer = TextTransformer()
    text = "Sample text for caching test"
    
    result1 = transformer.transform(text, resolution=2)
    result2 = transformer.transform(text, resolution=2)
    
    assert not result1["cached"]
    assert result2["cached"]
    assert result2["tokens_used"] == 0
```

### 5.2 Performance Optimization

**Cache warming script:**

```python
def warm_cache(article_id: str):
    """Pre-generate common parameter combinations"""
    transformer = TextTransformer()
    blocks = get_article_blocks(article_id)
    
    # Common combinations
    configs = [
        (0, 3, 10),   # Summary, casual, elementary
        (1, 5, 14),   # Condensed, neutral, high school
        (2, 5, 14),   # Standard, neutral, high school
        (3, 8, 16),   # Expanded, formal, college
    ]
    
    for block in blocks:
        for res, form, age in configs:
            transformer.transform(
                block["content"], res, form, age
            )
    
    print(f"Warmed cache for {len(blocks)} blocks")
```

---

## Phase 6: Deployment (Week 5-6)

### 6.1 Streamlit Cloud Deployment

```bash
# Create .streamlit/config.toml
mkdir .streamlit
cat > .streamlit/config.toml << EOF
[server]
port = 8501
enableCORS = false

[theme]
primaryColor = "#0066CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F8F9FA"
textColor = "#212529"
EOF

# Deploy to Streamlit Cloud
# 1. Push to GitHub
# 2. Connect at share.streamlit.io
# 3. Add secrets in dashboard:
#    OPENAI_API_KEY = "sk-..."
```

### 6.2 Docker Deployment

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "adaptive_text_demo.py"]
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## Phase 7: Production Enhancements

### 7.1 Add Real Authentication

```python
# Using streamlit-authenticator
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    credentials,
    'adaptive_text_app',
    'auth_key_12345',
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login()

if authentication_status:
    user_id = username
    # Show main app
elif authentication_status == False:
    st.error('Username/password incorrect')
```

### 7.2 Integrate Real Payments

```python
# Stripe integration
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def create_payment_intent(amount_cents: int, user_email: str):
    return stripe.PaymentIntent.create(
        amount=amount_cents,
        currency="usd",
        customer=get_stripe_customer(user_email),
        metadata={"product": "text_credits"}
    )

def handle_payment_success(payment_intent_id: str, user_id: str):
    # Add credits to wallet
    add_credits(user_id, amount=10.0)
```

### 7.3 Analytics & Monitoring

```python
# Add usage tracking
def log_transform(user_id: str, block_id: str, 
                 resolution: int, cached: bool):
    analytics_db.insert({
        "timestamp": datetime.now(),
        "user_id": user_id,
        "block_id": block_id,
        "resolution": resolution,
        "cache_hit": cached
    })

# Monitor API costs
def get_cost_summary(date_from: str):
    total_tokens = db.query(
        "SELECT SUM(tokens_used) FROM content_cache "
        "WHERE timestamp >= ?"
    , (date_from,))
    
    estimated_cost = total_tokens * 0.00002  # GPT-4 pricing
    return estimated_cost
```

---

## Best Practices

### Security
- Never commit API keys
- Use environment variables
- Implement rate limiting
- Validate all user inputs
- Sanitize downloaded content

### Performance
- Cache aggressively
- Pre-generate common transformations
- Use connection pooling for database
- Implement request debouncing on sliders
- Lazy load content blocks

### Cost Management
- Set API spending limits
- Monitor token usage daily
- Implement quotas per user
- Use cheaper models for previews
- Batch similar requests

### UX
- Show loading states clearly
- Provide immediate feedback
- Save user preferences
- Enable keyboard shortcuts
- Make mobile-friendly

---

## Troubleshooting Guide

### Common Issues

**"No module named 'streamlit'"**
```bash
pip install -r requirements.txt
```

**"API key not found"**
```bash
export OPENAI_API_KEY="your-key"
# Add to ~/.bashrc or ~/.zshrc for persistence
```

**"Database is locked"**
```python
# Use check_same_thread=False
conn = sqlite3.connect('db.db', check_same_thread=False)
```

**Slow transformations**
```python
# Check cache hit rate
stats = get_cache_stats()
if stats["hit_rate"] < 0.5:
    # Warm cache for common configs
    warm_cache_for_article(article_id)
```

**High API costs**
```python
# Use cheaper model for summaries
if resolution == 0:
    model = "gpt-3.5-turbo"  # Cheaper
else:
    model = "gpt-4o-mini"
```

---

## Next Steps

1. **Week 1**: Set up environment, database
2. **Week 2**: Implement LLM integration with caching
3. **Week 3**: Build Streamlit interface
4. **Week 4**: Add micropayments, testing
5. **Week 5**: Deploy to Streamlit Cloud
6. **Week 6**: Add authentication, analytics

## Resources

- Streamlit Docs: https://docs.streamlit.io
- OpenAI API: https://platform.openai.com/docs
- SQLite Tutorial: https://docs.python.org/3/library/sqlite3.html
- Stripe Payments: https://stripe.com/docs/api

## Support

For issues or questions:
- Check the troubleshooting guide above
- Review example code in repository
- Test with mock LLM first (no API costs)
- Start simple, add features incrementally
