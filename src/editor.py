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
            
        manual_papers = [p for p in papers if p.get("manual_override")]
        auto_papers = [p for p in papers if not p.get("manual_override")]
        
        selected_papers = manual_papers.copy()
        for mp in selected_papers:
            mp["editor_reasoning"] = "Manually curated by the Editor-in-Chief."
            mp["total_score"] = 30
            
        remaining_slots = top_k - len(selected_papers)
        
        if remaining_slots <= 0 or not auto_papers:
            return selected_papers[:top_k]
            
        logger.info(f"AI Editor evaluating {len(auto_papers)} auto-fetched papers for {remaining_slots} slots...")
        
        prompt = f"""
        You are the Chief Science Officer and Editor-in-Chief for a newsletter called "Bio By AI {{Longevity Edition}}".
        Your audience consists of scientists, biotech investors, and scientifically oriented public.
        
        Please review the following {len(auto_papers)} research paper summaries (Title and Abstract).
        Score each paper from 1-10 on three criteria:
        1. Novelty (Is this a breakthrough or just incremental?)
        2. Market/Investment Potential (Is this translatable? Does it solve a major aging-related problem?)
        3. Scientific Rigor/Interest (Is it a robust study? Will scientists care?)
        
        Return ONLY a valid JSON array of objects representing the top {remaining_slots} papers with the highest total score.
        Each JSON object must have:
        - "id": The integer ID from the input list below.
        - "reasoning": A 2-sentence explanation of why this was selected.
        - "total_score": The sum of the three scores.
        
        Here are the papers:
        """
        
        for i, paper in enumerate(auto_papers):
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
            
            for item in top_papers_json:
                paper_id = item.get("id")
                if paper_id is not None and 0 <= paper_id < len(auto_papers):
                    paper_data = auto_papers[paper_id].copy()
                    paper_data["editor_reasoning"] = item.get("reasoning")
                    paper_data["total_score"] = item.get("total_score")
                    selected_papers.append(paper_data)
                    
            selected_papers.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            return selected_papers
            
        except Exception as e:
            logger.error(f"Error during AI evaluation: {e}")
            selected_papers.extend(auto_papers[:remaining_slots])
            return selected_papers
