import logging
import os
import json
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class AIWriter:
    def __init__(self, api_key=None, model_name="gemini-3.5-flash"):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        
    def write_story(self, paper):
        prompt = f"""
        You are a top-tier science journalist writing for "Bio By AI {{Longevity Edition}}".
        Your audience is scientists, biotech investors, and scientifically oriented public.
        
        Write a compelling, narrative-driven newsletter story based on the following paper. 
        
        REQUIREMENTS:
        1. Tone: Engaging, attention-grabbing, and heavily focused on STORYTELLING. Hook the reader immediately with why this matters to the real world or the future of medicine. 
        2. Style: Avoid dry, academic jargon where possible. Use analogies. It should read like a high-end feature in Wired or The Atlantic—exciting and visionary, but scientifically accurate. NO clickbait.
        3. Content: Explain the core discovery (mechanism of action) and the broader implications for the longevity field seamlessly within the narrative.
        4. Citations: Since we are writing a story about a single paper, do NOT use inline citation numbers (like [1]) in the text. However, you MUST provide a robust "Citations" section at the end to prevent hallucinations.
        
        Paper Title: {paper['title']}
        Journal: {paper['journal']}
        URL: {paper['url']}
        Abstract: {paper['abstract']}
        Editor's Note: {paper.get('editor_reasoning', '')}
        """
        
        if paper.get('original_news_url'):
            prompt += f"\nOriginal News Source: {paper['original_news_url']}"
            
        prompt += """
        Output format should be a JSON object with:
        - "headline": Catchy but accurate headline.
        - "why_it_matters": A 1-2 sentence summary of why investors/scientists should care.
        - "html_body": The HTML formatted story (using <p>, <strong>, <em>, <ul> etc.). Include the inline citations here.
        - "citations": An HTML formatted list of citations supporting the claims (e.g. <li>...</li>). Include both the primary paper and the original news source if applicable.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            story_data = json.loads(cleaned_text)
            
            paper["story"] = story_data
            return paper
        except Exception as e:
            logger.error(f"Error generating story for {paper.get('title')}: {e}")
            return paper
