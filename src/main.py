import logging
import os
import sys
import time

# Ensure src is in path if running from root
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fetcher import ResearchFetcher
from editor import AIEditor
from writer import AIWriter
from artist import AIArtist
from publisher import Publisher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Bio By AI pipeline...")
    
    fetcher = ResearchFetcher(days_back=7)
    raw_papers = fetcher.run()
    
    if not raw_papers:
        logger.warning("No papers found this week!")
        return

    editor = AIEditor()
    top_papers = editor.evaluate_papers(raw_papers, top_k=3)
    
    writer = AIWriter()
    artist = AIArtist()
    
    from graph_builder import GraphBuilder
    import datetime
    graph_builder = GraphBuilder()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    os.makedirs("public/images", exist_ok=True)
    
    for i, paper in enumerate(top_papers):
        logger.info(f"Writing story for: {paper['title']}")
        paper = writer.write_story(paper)
        
        if "story" in paper:
            headline = paper["story"].get("headline", "")
            body = paper["story"].get("html_body", "")
            
            # Extract and update Knowledge Graph
            text_for_graph = headline + "\n" + body
            paper_slug = f"editions/{today_str}/story_{i}.html"
            logger.info(f"Updating Knowledge Graph with story_{i}...")
            graph_builder.extract_and_merge(text_for_graph, paper_slug)
            
            image_prompt = artist.generate_image_prompt(headline, body)
            image_filename = f"public/images/story_{i}_{int(time.time())}.jpg"
            
            saved_path = artist.generate_image(image_prompt, image_filename)
            if saved_path:
                paper["image_path"] = saved_path.replace("public/", "")
                
    publisher = Publisher()
    publisher.publish(top_papers)
    logger.info("Pipeline complete!")

if __name__ == "__main__":
    main()
