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
            "text": response.choices.message.content.strip(),
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
            "text": response.content.text.strip(),
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "model": self.model
        }

