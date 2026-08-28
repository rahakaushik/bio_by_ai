import os
import logging
import time

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

logger = logging.getLogger(__name__)

class AIArtist:
    def __init__(self, hf_api_key=None, gemini_api_key=None):
        gemini_api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
        if gemini_api_key and genai:
            self.client = genai.Client(api_key=gemini_api_key)
        else:
            self.client = None

    def generate_image_prompt(self, story_headline, story_body):
        if not self.client:
            return "Abstract digital art representing biology and longevity, futuristic, vibrant colors."
            
        prompt = f"""
        Based on the following science newsletter story, generate a highly descriptive prompt for an AI image generator to create an INFOGRAPHIC or SCIENTIFIC DIAGRAM.
        The style should be "clean, modern scientific infographic, flat vector style, data visualization, educational diagram, high-quality, text-free".
        Return ONLY the prompt text, nothing else.
        
        Headline: {story_headline}
        Story Snippet: {story_body[:500]}
        """
        try:
            response = self.client.models.generate_content(
                model='gemini-3.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error generating image prompt: {e}")
            return "Abstract digital art representing biology and longevity, futuristic, vibrant colors."

    def generate_image(self, prompt, output_filename):
        if not self.client:
            logger.warning("No Gemini API key provided. Skipping image generation.")
            return None
            
        logger.info(f"Generating image with prompt: {prompt}")
        
        try:
            result = self.client.models.generate_content(
                model='gemini-3.1-flash-image',
                contents=prompt
            )
            
            image_bytes = result.candidates[0].content.parts[0].inline_data.data
            with open(output_filename, "wb") as f:
                f.write(image_bytes)
            return output_filename
        except Exception as e:
            logger.error(f"Error generating image via Google Imagen: {e}")
            return None
