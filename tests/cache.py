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
