import os
import json
import logging
try:
    from google import genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, api_key=None, model_name="gemini-3.5-flash"):
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        self.graph_file = os.path.join("public", "knowledge_graph.json")

    def load_graph(self):
        if os.path.exists(self.graph_file):
            try:
                with open(self.graph_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                pass
        return {"nodes": [], "links": []}

    def save_graph(self, graph_data):
        os.makedirs(os.path.dirname(self.graph_file), exist_ok=True)
        with open(self.graph_file, "w") as f:
            json.dump(graph_data, f, indent=2)

    def extract_and_merge(self, story_text, paper_slug):
        """Extract entities/relationships from text and merge into the graph."""
        logger.info(f"Extracting knowledge graph for {paper_slug}...")
        
        prompt = f"""
        Analyze the following text from a scientific newsletter about longevity.
        Extract the key biological entities (Genes, Proteins, Drugs, Diseases, Aging Hallmarks).
        Extract the relationships between them.
        
        Return ONLY a JSON object with this exact schema:
        {{
            "nodes": [
                {{"id": "Exact Name", "type": "Drug | Gene | Protein | Disease | Hallmark | Organism"}}
            ],
            "links": [
                {{"source": "Exact Name 1", "target": "Exact Name 2", "label": "inhibits | increases | causes | treats | etc"}}
            ]
        }}
        
        Rules:
        - Keep node IDs very concise (e.g., "mTOR" not "the mTOR pathway").
        - Ensure every source and target in links exists in the nodes array.
        - Only include highly confident, explicit relationships.
        
        Text:
        {story_text}
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
                
            new_data = json.loads(cleaned_text)
            
            # Load current graph
            graph = self.load_graph()
            
            # Merge Nodes
            existing_node_ids = {node["id"].lower(): node["id"] for node in graph["nodes"]}
            for new_node in new_data.get("nodes", []):
                node_id = new_node.get("id", "").strip()
                node_type = new_node.get("type", "Unknown")
                if not node_id:
                    continue
                    
                if node_id.lower() not in existing_node_ids:
                    graph["nodes"].append({"id": node_id, "type": node_type})
                    existing_node_ids[node_id.lower()] = node_id
            
            # Merge Links
            existing_links = set(
                (link["source"].lower(), link["target"].lower(), link["label"].lower()) 
                for link in graph["links"]
            )
            
            for new_link in new_data.get("links", []):
                source = new_link.get("source", "").strip()
                target = new_link.get("target", "").strip()
                label = new_link.get("label", "related to").strip()
                
                if not source or not target:
                    continue
                    
                # Map to correct casing if it exists
                source_id = existing_node_ids.get(source.lower(), source)
                target_id = existing_node_ids.get(target.lower(), target)
                
                link_key = (source_id.lower(), target_id.lower(), label.lower())
                if link_key not in existing_links:
                    graph["links"].append({
                        "source": source_id,
                        "target": target_id,
                        "label": label,
                        "paper_slug": paper_slug
                    })
                    existing_links.add(link_key)
                    
            self.save_graph(graph)
            logger.info("Graph updated successfully.")
            
        except Exception as e:
            logger.error(f"Failed to extract and merge graph: {e}")
