async def generate_summary_llama3(content: str) -> str:
    """Minimal summary generation without external API"""
    # Simple extractive summary - take first few sentences
    sentences = content.split('.')
    summary_sentences = []
    
    for sentence in sentences[:3]:
        if len(sentence.strip()) > 10:
            summary_sentences.append(sentence.strip())
    
    if not summary_sentences:
        return "Summary not available for this content."
    
    return '. '.join(summary_sentences) + '.'

async def generate_summary(content: str) -> str:
    """Fallback to minimal summary"""
    return await generate_summary_llama3(content)