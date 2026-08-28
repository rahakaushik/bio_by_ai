import logging
import os
import json
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class AIEditor:
    def __init__(self, api_key=None, model_name="gemini-3.5-flash"):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
    
    def evaluate_papers(self, papers, top_k=3):
        if not papers:
            return []
            
        logger.info(f"AI Editor evaluating {len(papers)} papers...")
        
        prompt = f"""
        You are the Chief Science Officer and Editor-in-Chief for a newsletter called "Bio By AI {{Longevity Edition}}".
        Your audience consists of scientists, biotech investors, and scientifically oriented public.
        
        Please review the following {len(papers)} research paper summaries (Title and Abstract).
        Score each paper from 1-10 on three criteria:
        1. Novelty (Is this a breakthrough or just incremental?)
        2. Market/Investment Potential (Is this translatable? Does it solve a major aging-related problem?)
        3. Scientific Rigor/Interest (Is it a robust study? Will scientists care?)
        
        Return ONLY a valid JSON array of objects representing the top {top_k} papers with the highest total score.
        Each JSON object must have:
        - "id": The integer ID from the input list below.
        - "reasoning": A 2-sentence explanation of why this was selected.
        - "total_score": The sum of the three scores.
        
        Here are the papers:
        """
        
        for i, paper in enumerate(papers):
            prompt += f"\n--- Paper ID: {i} ---\nTitle: {paper['title']}\nAbstract: {paper['abstract']}\nJournal: {paper['journal']}\n"
            
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            # Remove any markdown code block formatting
            cleaned_text = response.text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
                
            top_papers_json = json.loads(cleaned_text)
            
            selected_papers = []
            for item in top_papers_json:
                paper_id = item.get("id")
                if paper_id is not None and 0 <= paper_id < len(papers):
                    paper_data = papers[paper_id].copy()
                    paper_data["editor_reasoning"] = item.get("reasoning")
                    paper_data["total_score"] = item.get("total_score")
                    selected_papers.append(paper_data)
                    
            selected_papers.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            return selected_papers
            
        except Exception as e:
            logger.error(f"Error during AI evaluation: {e}")
            return papers[:top_k]
