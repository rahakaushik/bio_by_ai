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
            
        max_attempts = 3
        current_prompt = prompt
        fallback_prompt = "Clean, modern scientific infographic, flat vector style, data visualization, educational diagram, high-quality, text-free, cellular biology, molecular signaling pathway, medical research diagram."

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Generating image (attempt {attempt}/{max_attempts}) with prompt: {current_prompt[:100]}...")
            try:
                result = self.client.models.generate_content(
                    model='gemini-3.1-flash-image',
                    contents=current_prompt
                )
                
                image_bytes = None
                if result and result.candidates:
                    candidate = result.candidates[0]
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                image_bytes = part.inline_data.data
                                break
                                
                if image_bytes:
                    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
                    with open(output_filename, "wb") as f:
                        f.write(image_bytes)
                    logger.info(f"Successfully generated and saved image to {output_filename}")
                    return output_filename
                else:
                    logger.warning(f"Attempt {attempt}: No inline image data in response candidates.")
            except Exception as e:
                logger.error(f"Attempt {attempt} failed generating image: {e}")
                
            if attempt < max_attempts:
                # Wait before retry to clear rate limits (e.g. 20s, 40s)
                sleep_secs = 20 * attempt
                logger.info(f"Sleeping for {sleep_secs}s before image retry...")
                time.sleep(sleep_secs)
                # On final retry, switch to sanitized fallback prompt in case content policy triggered
                if attempt == max_attempts - 1:
                    current_prompt = fallback_prompt
                    
        logger.error(f"Failed to generate image after {max_attempts} attempts.")
        return None
