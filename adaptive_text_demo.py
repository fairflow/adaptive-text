
"""
Adaptive Text Resolution Viewer with Mock Micropayments
A demonstration of variable-detail text display with user controls
"""

import streamlit as st
import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple

# Initialize session state for mock payments
if 'wallet_balance' not in st.session_state:
    st.session_state.wallet_balance = 100.0  # Starting credits

if 'purchased_blocks' not in st.session_state:
    st.session_state.purchased_blocks = set()

if 'db_initialized' not in st.session_state:
    init_database()
    st.session_state.db_initialized = True


# Database setup for persistence
def init_database():
    """Initialize SQLite database for storing purchased content"""
    conn = sqlite3.connect('adaptive_text_purchases.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            user_id TEXT,
            block_id TEXT,
            article_id TEXT,
            resolution_level INTEGER,
            purchase_date TEXT,
            cost REAL,
            PRIMARY KEY (user_id, block_id, resolution_level)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS content_cache (
            block_id TEXT,
            resolution_level INTEGER,
            formality INTEGER,
            reading_age INTEGER,
            content TEXT,
            PRIMARY KEY (block_id, resolution_level, formality, reading_age)
        )
    """)

    conn.commit()
    conn.close()


def mock_llm_transform(text: str, resolution: int, formality: int, reading_age: int) -> str:
    """
    Mock LLM transformation - in production, this would call OpenAI/Anthropic API
    For demo purposes, we simulate different versions based on parameters
    """

    # Base text versions (simulating LLM output at different resolutions)
    transformations = {
        0: lambda t: " ".join(t.split()[:max(5, len(t.split()) // 4)]) + "...",  # Summary
        1: lambda t: " ".join(t.split()[:max(15, len(t.split()) // 2)]) + "...",  # Condensed
        2: lambda t: t,  # Original
        3: lambda t: t + " This version includes additional context and examples for deeper understanding.",  # Expanded
    }

    # Apply resolution transformation
    result = transformations.get(resolution, lambda t: t)(text)

    # Apply formality modifier (mock)
    if formality < 3:
        result = result.replace("demonstrates", "shows").replace("utilizes", "uses")
    elif formality > 7:
        result = result.replace("shows", "demonstrates").replace("uses", "utilizes")

    # Apply reading age modifier (mock)
    if reading_age < 12:
        result = result.replace("demonstrates", "shows").replace("comprehensive", "complete")

    return result


def calculate_cost(resolution: int, formality: int, reading_age: int) -> float:
    """Calculate mock cost based on parameters"""
    base_costs = {0: 0.0, 1: 0.5, 2: 1.0, 3: 2.0}
    modifier = (abs(formality - 5) + abs(reading_age - 14)) * 0.1
    return base_costs.get(resolution, 1.0) + modifier


def purchase_block(block_id: str, article_id: str, resolution: int, cost: float):
    """Record a block purchase in database and session"""
    user_id = "demo_user"  # In production, use actual auth

    conn = sqlite3.connect('adaptive_text_purchases.db', check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO purchases 
        (user_id, block_id, article_id, resolution_level, purchase_date, cost)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, block_id, article_id, resolution, datetime.now().isoformat(), cost))

    conn.commit()
    conn.close()

    st.session_state.purchased_blocks.add((block_id, resolution))
    st.session_state.wallet_balance -= cost


def is_block_purchased(block_id: str, resolution: int) -> bool:
    """Check if block at resolution is already purchased"""
    return (block_id, resolution) in st.session_state.purchased_blocks


# Sample article content
SAMPLE_ARTICLE = {
    "title": "The Future of Adaptive Text Systems",
    "blocks": [
        {
            "id": "block_1",
            "content": "Adaptive text systems represent a paradigm shift in how digital content is consumed. These systems dynamically adjust the level of detail, formality, and complexity based on user preferences and available screen space. By leveraging modern Large Language Models, content can be automatically condensed or expanded while maintaining semantic coherence."
        },
        {
            "id": "block_2", 
            "content": "The technical implementation relies on controllable text generation, where attributes like formality and reading level are explicitly targeted during the transformation process. State-of-the-art approaches use transformer-based models fine-tuned on style transfer datasets such as GYAFC (Grammarly's Yahoo Answers Formality Corpus). These models can reliably convert between casual and formal registers while preserving factual content."
        },
        {
            "id": "block_3",
            "content": "Monetization through micropayments creates a sustainable model for content creators. Users pay incrementally for higher resolution or specialized transformations (expert terminology, simplified explanations). The granular pricing—down to individual blocks or even character-level changes—allows precise value alignment. Purchased content persists across sessions, ensuring users never pay twice for the same material."
        },
        {
            "id": "block_4",
            "content": "Future developments may include multi-modal extensions, where images and videos undergo similar adaptive transformations. Semantic interpolation between text variants could enable smooth transitions as users adjust controls. Machine learning personalization could predict optimal settings based on individual reading patterns, creating truly adaptive experiences that serve both casual browsers and deep researchers from the same source material."
        }
    ]
}


def main():
    st.set_page_config(page_title="Adaptive Text Viewer", layout="wide")

    # Header
    st.title("🔍 Adaptive Text Resolution Viewer")
    st.markdown("*Experience variable-detail content with fine-grained control*")

    # Sidebar controls
    st.sidebar.header("Content Controls")

    resolution = st.sidebar.slider(
        "📊 Resolution Level",
        min_value=0,
        max_value=3,
        value=1,
        help="0=Summary, 1=Condensed, 2=Standard, 3=Expanded"
    )

    formality = st.sidebar.slider(
        "🎩 Formality",
        min_value=1,
        max_value=10,
        value=5,
        help="1=Very Casual, 10=Very Formal"
    )

    reading_age = st.sidebar.slider(
        "📚 Reading Age",
        min_value=8,
        max_value=18,
        value=14,
        help="Target reading comprehension age"
    )

    # Wallet display
    st.sidebar.divider()
    st.sidebar.header("💰 Mock Wallet")
    st.sidebar.metric("Balance", f"{st.session_state.wallet_balance:.2f} credits")
    st.sidebar.caption(f"Blocks purchased: {len(st.session_state.purchased_blocks)}")

    # Reset button
    if st.sidebar.button("Reset Wallet & Purchases"):
        st.session_state.wallet_balance = 100.0
        st.session_state.purchased_blocks = set()
        st.rerun()

    # Article display
    st.header(SAMPLE_ARTICLE["title"])

    # Display resolution legend
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("**Level 0**: Summary")
    with col2:
        st.info("**Level 1**: Condensed")
    with col3:
        st.info("**Level 2**: Standard")
    with col4:
        st.info("**Level 3**: Expanded")

    st.divider()

    # Display each block
    for idx, block in enumerate(SAMPLE_ARTICLE["blocks"], 1):
        block_id = block["id"]

        # Calculate cost for current settings
        cost = calculate_cost(resolution, formality, reading_age)
        is_purchased = is_block_purchased(block_id, resolution)
        is_free = resolution == 0  # Summary level is always free

        # Block header
        col_title, col_price = st.columns([3, 1])
        with col_title:
            st.subheader(f"Section {idx}")
        with col_price:
            if is_free:
                st.success("FREE")
            elif is_purchased:
                st.success("OWNED")
            else:
                st.warning(f"🔒 {cost:.2f} credits")

        # Content display
        if is_free or is_purchased:
            # Show transformed content
            transformed = mock_llm_transform(
                block["content"],
                resolution,
                formality,
                reading_age
            )
            st.markdown(transformed)

            # Download button for owned content
            if is_purchased or is_free:
                st.download_button(
                    label=f"📥 Download Section {idx}",
                    data=transformed,
                    file_name=f"section_{idx}_res{resolution}.txt",
                    mime="text/plain",
                    key=f"download_{block_id}_{resolution}"
                )
        else:
            # Show locked preview
            preview = mock_llm_transform(block["content"], 0, formality, reading_age)
            st.markdown(f"*{preview}*")
            st.caption("↑ Free preview. Unlock full content below ↓")

            # Purchase button
            col_buy, col_info = st.columns([1, 3])
            with col_buy:
                if st.button(f"Unlock for {cost:.2f} credits", key=f"buy_{block_id}_{resolution}"):
                    if st.session_state.wallet_balance >= cost:
                        purchase_block(block_id, "article_1", resolution, cost)
                        st.success(f"Unlocked Section {idx}!")
                        st.rerun()
                    else:
                        st.error("Insufficient credits!")
            with col_info:
                st.caption(f"Unlock this section at resolution level {resolution}")

        st.divider()

    # Footer info
    st.info("""
    **How it works:**
    - **Resolution Level**: Controls amount of detail (summary → expanded)
    - **Formality**: Adjusts language style (casual → formal)
    - **Reading Age**: Simplifies/complexifies vocabulary
    - **Micropayments**: Pay only for content you unlock
    - **Persistence**: Purchased blocks remain accessible across sessions
    - **Downloads**: Save unlocked content locally
    """)

    # Technical note
    with st.expander("🔧 Implementation Notes"):
        st.markdown("""
        ### Production Implementation

        In a real system, replace `mock_llm_transform()` with actual API calls:

        ```python
        import openai

        def llm_transform(text, resolution, formality, reading_age):
            client = openai.OpenAI(api_key="YOUR_API_KEY")

            prompt = f'''
            Transform this text with the following parameters:
            - Resolution: {resolution} (0=summary, 3=expanded)
            - Formality: {formality}/10
            - Reading age: {reading_age}

            Original text:
            {text}

            Provide only the transformed text.
            '''

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )

            return response.choices[0].message.content
        ```

        ### Database Schema
        - `purchases`: Tracks user ownership of blocks
        - `content_cache`: Stores pre-generated transformations

        ### Cost Optimization
        - Pre-generate common transformations
        - Cache LLM outputs in database
        - Batch process articles on upload
        """)


if __name__ == "__main__":
    main()
