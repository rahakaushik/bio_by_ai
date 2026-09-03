import requests
import datetime
from dateutil.relativedelta import relativedelta
import xml.etree.ElementTree as ET
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchFetcher:
    def __init__(self, days_back=7):
        self.days_back = days_back
        self.end_date = datetime.date.today()
        self.start_date = self.end_date - relativedelta(days=self.days_back)
        self.keywords = ["longevity", "aging", "healthspan", "senescence", "lifespan", "rejuvenation"]
    
    def fetch_pubmed(self):
        logger.info("Fetching from PubMed...")
        # Build NCBI eSearch query
        keyword_query = " OR ".join(self.keywords)
        # Format date for pubmed: YYYY/MM/DD
        term = f"({keyword_query}) AND (\"{self.start_date.strftime('%Y/%m/%d')}\"[Date - Publication] : \"{self.end_date.strftime('%Y/%m/%d')}\"[Date - Publication])"
        
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": term,
            "retmode": "json",
            "retmax": 50 # Let's fetch top 50 matches to evaluate
        }
        
        search_resp = requests.get(search_url, params=search_params)
        search_resp.raise_for_status()
        id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])
        
        if not id_list:
            return []
            
        # Fetch details for the IDs
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        
        fetch_resp = requests.get(fetch_url, params=fetch_params)
        fetch_resp.raise_for_status()
        
        root = ET.fromstring(fetch_resp.text)
        papers = []
        for article in root.findall(".//PubmedArticle"):
            try:
                pmid = article.find(".//PMID").text
                title = article.find(".//ArticleTitle").text
                
                abstract_elem = article.find(".//AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else ""
                if not abstract:
                    continue # Skip papers without abstracts
                    
                journal = article.find(".//Title").text
                
                # Try to get DOI
                doi = ""
                for elid in article.findall(".//ArticleId"):
                    if elid.get("IdType") == "doi":
                        doi = elid.text
                        break
                        
                link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                if doi:
                    link = f"https://doi.org/{doi}"
                    
                papers.append({
                    "source": "PubMed",
                    "title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "url": link,
                    "date": self.end_date.isoformat() # Approx publication date
                })
            except Exception as e:
                logger.warning(f"Error parsing a PubMed article: {e}")
                continue
                
        return papers

    def fetch_biorxiv(self):
        logger.info("Fetching from bioRxiv...")
        start_str = self.start_date.strftime("%Y-%m-%d")
        end_str = self.end_date.strftime("%Y-%m-%d")
        url = f"https://api.biorxiv.org/details/biorxiv/{start_str}/{end_str}/0/100"
        
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            papers = []
            collection = data.get("collection", [])
            for item in collection:
                title = item.get("title", "").lower()
                abstract = item.get("abstract", "").lower()
                
                # Basic text filtering for keywords
                if any(kw in title or kw in abstract for kw in self.keywords):
                    papers.append({
                        "source": "bioRxiv",
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", ""),
                        "journal": "bioRxiv",
                        "url": f"https://doi.org/{item.get('doi')}",
                        "date": item.get("date")
                    })
            return papers
        except Exception as e:
            logger.warning(f"Error fetching from bioRxiv: {e}")
            return []

    def fetch_medrxiv(self):
        logger.info("Fetching from medRxiv...")
        start_str = self.start_date.strftime("%Y-%m-%d")
        end_str = self.end_date.strftime("%Y-%m-%d")
        url = f"https://api.biorxiv.org/details/medrxiv/{start_str}/{end_str}/0/100"
        
        try:
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json()
            
            papers = []
            collection = data.get("collection", [])
            for item in collection:
                title = item.get("title", "").lower()
                abstract = item.get("abstract", "").lower()
                
                if any(kw in title or kw in abstract for kw in self.keywords):
                    papers.append({
                        "source": "medRxiv",
                        "title": item.get("title", ""),
                        "abstract": item.get("abstract", ""),
                        "journal": "medRxiv",
                        "url": f"https://doi.org/{item.get('doi')}",
                        "date": item.get("date")
                    })
            return papers
        except Exception as e:
            logger.warning(f"Error fetching from medRxiv: {e}")
            return []

    def fetch_plos(self):
        logger.info("Fetching from PLOS...")
        keyword_query = " OR ".join(self.keywords)
        start_str = self.start_date.strftime("%Y-%m-%dT00:00:00Z")
        end_str = self.end_date.strftime("%Y-%m-%dT23:59:59Z")
        
        q = f"everything:({keyword_query}) AND publication_date:[{start_str} TO {end_str}]"
        
        url = "http://api.plos.org/search"
        params = {
            "q": q,
            "fl": "id,title_display,abstract,journal,publication_date",
            "wt": "json",
            "rows": 50
        }
        
        try:
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            docs = resp.json().get("response", {}).get("docs", [])
            
            papers = []
            for doc in docs:
                abstract_list = doc.get("abstract", [])
                abstract = abstract_list[0] if abstract_list else ""
                
                if not abstract:
                    continue
                    
                papers.append({
                    "source": "PLOS",
                    "title": doc.get("title_display", ""),
                    "abstract": abstract,
                    "journal": doc.get("journal", "PLOS"),
                    "url": f"https://doi.org/{doc.get('id')}",
                    "date": doc.get("publication_date")
                })
            return papers
        except Exception as e:
            logger.warning(f"Error fetching from PLOS: {e}")
            return []

    def fetch_manual_links(self):
        import os
        from bs4 import BeautifulSoup
        
        manual_file = "manual_links.txt"
        if not os.path.exists(manual_file):
            return []
            
        logger.info("Fetching manually provided links and PMIDs...")
        with open(manual_file, "r") as f:
            lines = f.readlines()
            
        papers = []
        pmids = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            if line.isdigit():
                pmids.append(line)
            elif line.startswith("http"):
                # Handle generic URL
                try:
                    logger.info(f"Scraping manual URL: {line}")
                    # Use a standard user-agent to bypass basic blocks
                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                    resp = requests.get(line, headers=headers, timeout=10)
                    resp.raise_for_status()
                    
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    scraped_title = soup.title.string if soup.title else "Manually Curated Article"
                    
                    # Extract text from paragraphs
                    paragraphs = soup.find_all('p')
                    scraped_text = " ".join([p.get_text() for p in paragraphs])
                    scraped_text = scraped_text[:4000] + ("..." if len(scraped_text) > 4000 else "")
                    
                    final_title = scraped_title.strip()
                    final_abstract = scraped_text.strip()
                    journal = "Web Source"
                    url = line
                    
                    # AI Research to find the primary paper
                    import os
                    try:
                        from google import genai
                    except ImportError:
                        genai = None
                        
                    api_key = os.environ.get("GEMINI_API_KEY")
                    if genai and api_key:
                        client = genai.Client(api_key=api_key)
                        prompt = f"""
                        Read this scraped text from a web article. 
                        Identify the primary scientific research publication being discussed.
                        Return ONLY a valid JSON object with this structure:
                        {{
                          "is_news_article": boolean,
                          "pubmed_search_query": "AuthorLastName AND Keywords",
                          "summary": "Summary of findings"
                        }}
                        Text: {scraped_title}
                        {scraped_text}
                        """
                        try:
                            ai_resp = client.models.generate_content(model="gemini-3.5-flash", contents=prompt)
                            cleaned_text = ai_resp.text.strip()
                            if cleaned_text.startswith("```json"): cleaned_text = cleaned_text[7:]
                            if cleaned_text.endswith("```"): cleaned_text = cleaned_text[:-3]
                            
                            ai_data = json.loads(cleaned_text)
                            
                            if ai_data.get("is_news_article") and ai_data.get("pubmed_search_query"):
                                logger.info(f"AI identified it as news. Searching PubMed for: {ai_data['pubmed_search_query']}")
                                # Hit PubMed eSearch
                                search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                                search_params = {"db": "pubmed", "term": ai_data['pubmed_search_query'], "retmode": "json", "retmax": 1}
                                search_resp = requests.get(search_url, params=search_params).json()
                                id_list = search_resp.get("esearchresult", {}).get("idlist", [])
                                
                                if id_list:
                                    logger.info(f"Found matching primary paper on PubMed: {id_list[0]}")
                                    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                                    fetch_params = {"db": "pubmed", "id": id_list[0], "retmode": "xml"}
                                    fetch_resp = requests.get(fetch_url, params=fetch_params)
                                    root = ET.fromstring(fetch_resp.text)
                                    for article in root.findall(".//PubmedArticle"):
                                        pmid = article.find(".//PMID").text
                                        title = article.find(".//ArticleTitle").text
                                        abstract_elem = article.find(".//AbstractText")
                                        pubmed_abstract = abstract_elem.text if abstract_elem is not None else ""
                                        
                                        # Combine the original news context with the primary paper context
                                        final_title = title
                                        final_abstract = f"[Primary Paper Abstract]: {pubmed_abstract}\n\n[Original News Context]: {ai_data.get('summary', '')}"
                                        journal = article.find(".//Title").text
                                        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                                        break
                        except Exception as ai_e:
                            logger.warning(f"AI research failed for URL {line}: {ai_e}")
                            
                    papers.append({
                        "source": "Manual Link (Researched)",
                        "title": final_title,
                        "abstract": final_abstract,
                        "journal": journal,
                        "url": url,
                        "date": self.end_date.isoformat(),
                        "manual_override": True,
                        "original_news_url": line if url != line else None
                    })
                except Exception as e:
                    logger.warning(f"Failed to scrape URL {line}: {e}")
                    
        # Handle PMIDs if any were provided
        if pmids:
            fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml"
            }
            try:
                fetch_resp = requests.get(fetch_url, params=fetch_params)
                fetch_resp.raise_for_status()
                
                root = ET.fromstring(fetch_resp.text)
                for article in root.findall(".//PubmedArticle"):
                    pmid = article.find(".//PMID").text
                    title = article.find(".//ArticleTitle").text
                    
                    abstract_elem = article.find(".//AbstractText")
                    abstract = abstract_elem.text if abstract_elem is not None else "No abstract provided."
                    journal = article.find(".//Title").text
                    
                    papers.append({
                        "source": "Manual PMID",
                        "title": title,
                        "abstract": abstract,
                        "journal": journal,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        "date": self.end_date.isoformat(),
                        "manual_override": True
                    })
            except Exception as e:
                logger.warning(f"Error fetching manual PMIDs: {e}")
                
        # Clear the file
        with open(manual_file, "w") as f:
            f.write("# Paste URLs or PubMed IDs here, one per line.\n")
            
        return papers

    def run(self):
        papers = []
        papers.extend(self.fetch_manual_links())
        papers.extend(self.fetch_pubmed())
        papers.extend(self.fetch_biorxiv())
        papers.extend(self.fetch_medrxiv())
        papers.extend(self.fetch_plos())
        logger.info(f"Total relevant papers found: {len(papers)}")
        return papers

if __name__ == "__main__":
    fetcher = ResearchFetcher()
    results = fetcher.run()
    print(f"Sample: {json.dumps(results[:2], indent=2)}")
