import os
import sys

# Ensure src is in python path
sys.path.append("src")

from graph_builder import GraphBuilder
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    builder = GraphBuilder()
    
    # Mock story content to test the extraction
    mock_story = """
    A groundbreaking study published today demonstrates that rapamycin significantly inhibits the mTOR pathway in aging mice, 
    leading to a reduction in cellular senescence. The researchers observed that suppressing mTOR activity not only 
    extended lifespan but also delayed the onset of age-related diseases. This provides further evidence that 
    targeting cellular senescence is a viable strategy for extending healthspan.
    """
    
    mock_slug = "story_0.html"
    
    print("Testing Graph Extraction using Gemini...")
    builder.extract_and_merge(mock_story, mock_slug)
    
    print("\nExtraction complete! Check public/knowledge_graph.json to see the extracted nodes.")
    print("To view the graph visually, open templates/graph_template.html in your web browser.")
    print("Note: Browsers block local JSON fetching due to CORS. You may need to run a local server:")
    print("    python -m http.server --directory .")
    print("Then go to http://localhost:8000/templates/graph_template.html")
