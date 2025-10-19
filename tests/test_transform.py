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
