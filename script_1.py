
# Create additional integration example with real OpenAI API

integration_code = '''
"""
Production-Ready Integration with OpenAI API
Demonstrates real LLM-based text transformation
"""

import openai
import os
from typing import Dict, List
import json
import sqlite3
from datetime import datetime

class AdaptiveTextProcessor:
    """
    Production class for adaptive text processing with LLM integration
    """
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.cache_db = "text_transform_cache.db"
        self._init_cache()
    
    def _init_cache(self):
        """Initialize cache database to avoid redundant API calls"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transform_cache (
                text_hash TEXT,
                resolution INTEGER,
                formality INTEGER,
                reading_age INTEGER,
                transformed_text TEXT,
                timestamp TEXT,
                tokens_used INTEGER,
                PRIMARY KEY (text_hash, resolution, formality, reading_age)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_text_hash(self, text: str) -> str:
        """Generate hash of input text for caching"""
        import hashlib
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _check_cache(self, text: str, resolution: int, 
                     formality: int, reading_age: int) -> str:
        """Check if transformation exists in cache"""
        text_hash = self._get_text_hash(text)
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT transformed_text FROM transform_cache
            WHERE text_hash = ? AND resolution = ? 
            AND formality = ? AND reading_age = ?
        """, (text_hash, resolution, formality, reading_age))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def _save_to_cache(self, text: str, resolution: int, formality: int,
                       reading_age: int, transformed: str, tokens: int):
        """Save transformation to cache"""
        text_hash = self._get_text_hash(text)
        
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO transform_cache
            (text_hash, resolution, formality, reading_age, 
             transformed_text, timestamp, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (text_hash, resolution, formality, reading_age,
              transformed, datetime.now().isoformat(), tokens))
        
        conn.commit()
        conn.close()
    
    def transform_text(self, text: str, resolution: int = 2,
                      formality: int = 5, reading_age: int = 14) -> Dict:
        """
        Transform text using OpenAI API with specified parameters
        
        Args:
            text: Original text to transform
            resolution: 0=summary, 1=condensed, 2=standard, 3=expanded
            formality: 1-10 scale (1=very casual, 10=very formal)
            reading_age: Target reading age (8-18)
        
        Returns:
            Dict with transformed text and metadata
        """
        
        # Check cache first
        cached = self._check_cache(text, resolution, formality, reading_age)
        if cached:
            return {
                "text": cached,
                "cached": True,
                "tokens_used": 0
            }
        
        # Build prompt based on parameters
        resolution_map = {
            0: "Create a brief summary (20-30% of original length)",
            1: "Create a condensed version (40-60% of original length)",
            2: "Rewrite at standard detail level (preserve all key information)",
            3: "Create an expanded version with additional context and examples"
        }
        
        formality_guidance = self._get_formality_guidance(formality)
        reading_level_guidance = self._get_reading_level_guidance(reading_age)
        
        prompt = f"""Transform the following text according to these specifications:

RESOLUTION: {resolution_map[resolution]}
FORMALITY: {formality_guidance}
READING LEVEL: {reading_level_guidance}

IMPORTANT RULES:
- Preserve all factual information and key points
- Maintain logical flow and coherence
- Do not add information not present in the original
- Output only the transformed text, no explanations

ORIGINAL TEXT:
{text}

TRANSFORMED TEXT:"""

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use gpt-4 for better quality
                messages=[
                    {"role": "system", "content": "You are an expert text transformer that precisely follows specifications while preserving content accuracy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=1500
            )
            
            transformed = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens
            
            # Save to cache
            self._save_to_cache(text, resolution, formality, 
                              reading_age, transformed, tokens_used)
            
            return {
                "text": transformed,
                "cached": False,
                "tokens_used": tokens_used,
                "model": "gpt-4o-mini"
            }
            
        except Exception as e:
            return {
                "text": text,
                "error": str(e),
                "cached": False
            }
    
    def _get_formality_guidance(self, formality: int) -> str:
        """Generate formality guidance for prompt"""
        if formality <= 3:
            return "Very casual, conversational tone. Use contractions, simple words, informal expressions."
        elif formality <= 5:
            return "Moderately casual. Conversational but clear. Some contractions okay."
        elif formality <= 7:
            return "Neutral professional tone. Avoid slang and contractions. Clear and direct."
        else:
            return "Very formal, academic tone. Use sophisticated vocabulary, no contractions, formal structure."
    
    def _get_reading_level_guidance(self, reading_age: int) -> str:
        """Generate reading level guidance for prompt"""
        if reading_age <= 10:
            return "Elementary level: Very simple sentences, common words, short paragraphs. Flesch-Kincaid Grade 3-5."
        elif reading_age <= 12:
            return "Middle school level: Clear sentences, accessible vocabulary, concrete examples. Flesch-Kincaid Grade 6-8."
        elif reading_age <= 15:
            return "High school level: Standard complexity, general vocabulary. Flesch-Kincaid Grade 9-10."
        else:
            return "College level: Complex sentences, sophisticated vocabulary, abstract concepts. Flesch-Kincaid Grade 11+."
    
    def batch_transform(self, blocks: List[Dict], resolution: int,
                       formality: int, reading_age: int) -> List[Dict]:
        """
        Transform multiple text blocks efficiently
        
        Args:
            blocks: List of dicts with 'id' and 'content' keys
            resolution, formality, reading_age: Same as transform_text
        
        Returns:
            List of transformed blocks with metadata
        """
        results = []
        
        for block in blocks:
            result = self.transform_text(
                block["content"],
                resolution,
                formality,
                reading_age
            )
            
            results.append({
                "id": block["id"],
                "original": block["content"],
                "transformed": result["text"],
                "cached": result.get("cached", False),
                "tokens": result.get("tokens_used", 0),
                "error": result.get("error")
            })
        
        return results
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), SUM(tokens_used) FROM transform_cache")
        count, total_tokens = cursor.fetchone()
        
        conn.close()
        
        return {
            "cached_transformations": count or 0,
            "total_tokens_saved": total_tokens or 0,
            "estimated_cost_saved": (total_tokens or 0) * 0.00002  # Rough GPT-4 estimate
        }


# Example usage
if __name__ == "__main__":
    # Initialize processor
    processor = AdaptiveTextProcessor(api_key="YOUR_API_KEY_HERE")
    
    # Sample text
    sample_text = """
    Artificial intelligence has revolutionized numerous industries through 
    machine learning algorithms that can process vast amounts of data. 
    These systems learn patterns and make predictions with increasing accuracy 
    over time, enabling applications from medical diagnosis to autonomous vehicles.
    """
    
    # Transform to summary at casual formality for age 10
    result = processor.transform_text(
        text=sample_text,
        resolution=0,  # Summary
        formality=3,   # Casual
        reading_age=10  # Elementary
    )
    
    print("SUMMARY (Casual, Age 10):")
    print(result["text"])
    print(f"\\nTokens used: {result['tokens_used']}")
    print(f"Cached: {result['cached']}")
    
    print("\\n" + "="*60 + "\\n")
    
    # Transform to expanded at formal tone for age 16
    result2 = processor.transform_text(
        text=sample_text,
        resolution=3,  # Expanded
        formality=9,   # Very formal
        reading_age=16  # Advanced
    )
    
    print("EXPANDED (Formal, Age 16):")
    print(result2["text"])
    print(f"\\nTokens used: {result2['tokens_used']}")
    
    print("\\n" + "="*60 + "\\n")
    
    # Show cache stats
    stats = processor.get_cache_stats()
    print("CACHE STATISTICS:")
    print(f"Cached transformations: {stats['cached_transformations']}")
    print(f"Total tokens saved: {stats['total_tokens_saved']}")
    print(f"Estimated cost saved: ${stats['estimated_cost_saved']:.4f}")
'''

# Save integration code
with open('adaptive_text_integration.py', 'w') as f:
    f.write(integration_code)

print("✓ Created: adaptive_text_integration.py")
print("\nThis production integration includes:")
print("- Full OpenAI API integration")
print("- SQLite caching to minimize API costs")
print("- Batch processing for multiple blocks")
print("- Formality & reading level control via prompts")
print("- Token usage tracking")
print("- Error handling")
print("\nTo use:")
print("1. pip install openai")
print("2. Set OPENAI_API_KEY environment variable")
print("3. Run: python adaptive_text_integration.py")
