import os
import sys
import json
from jinja2 import Environment, FileSystemLoader

sys.path.append("src")
from writer import AIWriter

def test_writer_with_kg():
    print("Initializing AI Writer...")
    writer = AIWriter()
    
    # Create a mock paper about Rapamycin and mTOR (which we know is in our mock KG)
    mock_paper = {
        "title": "Novel Insights into Rapamycin-Mediated mTOR Inhibition and Lifespan Extension",
        "journal": "Nature Aging",
        "abstract": "This study demonstrates that a novel dosing schedule of rapamycin effectively inhibits mTOR complex 1 (mTORC1) in aged mice without the typical metabolic side effects. The results show a 15% increase in remaining lifespan and a significant reduction in markers of cellular senescence.",
        "url": "https://example.com/fake-rapamycin-paper",
        "editor_reasoning": "High relevance to longevity therapeutics."
    }
    
    print(f"\nWriting story for: {mock_paper['title']}")
    print("The AI is cross-referencing your knowledge_graph.json...")
    
    # This will trigger the KG context injection
    result_paper = writer.write_story(mock_paper)
    
    story = result_paper.get("story", {})
    
    print("\n--- GENERATED STORY DATA ---")
    print(f"Headline: {story.get('headline')}")
    
    kg_insights = story.get('kg_insights', '')
    if kg_insights:
        print("\n--- SUCCESS: KG INSIGHTS GENERATED! ---")
        print(kg_insights)
    else:
        print("\n--- NO KG INSIGHTS GENERATED --- (The AI deemed past context irrelevant)")
        
    print("\n----------------------------")
    print("Done testing!")

if __name__ == "__main__":
    test_writer_with_kg()
