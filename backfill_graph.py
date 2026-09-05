import os
import sys
import requests
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

sys.path.append("src")
from graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://rahakaushik.github.io/bio_by_ai/"

def backfill_graph():
    builder = GraphBuilder()
    
    # 1. Fetch main index to find all editions
    logger.info(f"Fetching {BASE_URL}")
    resp = requests.get(BASE_URL)
    
    if resp.status_code != 200:
        logger.error("Could not fetch the live website. Make sure it is published.")
        return
        
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Find all edition URLs from the dropdown
    edition_urls = [BASE_URL] # Include the main front page
    select = soup.find('select')
    if select:
        for option in select.find_all('option'):
            val = option.get('value')
            if val and "index.html" in val:
                # Resolve relative URL
                full_url = urljoin(BASE_URL, val)
                if full_url not in edition_urls:
                    edition_urls.append(full_url)
                    
    logger.info(f"Found {len(edition_urls)} editions to scan.")
    
    # 2. Find all stories in all editions
    story_urls = []
    for edition_url in edition_urls:
        logger.info(f"Scanning edition: {edition_url}")
        e_resp = requests.get(edition_url)
        if e_resp.status_code == 200:
            e_soup = BeautifulSoup(e_resp.text, 'html.parser')
            for a in e_soup.find_all('a', href=True):
                href = a['href']
                if 'story_' in href and href.endswith('.html'):
                    story_full_url = urljoin(edition_url, href)
                    if story_full_url not in story_urls:
                        story_urls.append(story_full_url)
                        
    logger.info(f"Found {len(story_urls)} unique stories.")
    
    # 3. Fetch each story and extract graph
    for story_url in story_urls:
        logger.info(f"Processing story: {story_url}")
        s_resp = requests.get(story_url)
        if s_resp.status_code == 200:
            s_soup = BeautifulSoup(s_resp.text, 'html.parser')
            # The story text is typically in <div class="story">
            story_div = s_soup.find('div', class_='story')
            if story_div:
                text = story_div.get_text(separator=' ', strip=True)
                # We need a slug for the node links. Let's use the absolute URL for simplicity
                # Or just the relative path from root
                relative_slug = story_url.replace(BASE_URL, "")
                
                logger.info(f"Extracting entities from {relative_slug}...")
                builder.extract_and_merge(text, relative_slug)
            else:
                logger.warning(f"Could not find story text in {story_url}")

if __name__ == "__main__":
    backfill_graph()
    print("\nBackfill complete! Check public/knowledge_graph.json")
