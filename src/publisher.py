import os
import datetime
from jinja2 import Environment, FileSystemLoader
import logging

logger = logging.getLogger(__name__)

class Publisher:
    def __init__(self, template_dir="templates", output_dir="public"):
        self.template_dir = template_dir
        self.output_dir = output_dir
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        
    def publish(self, papers):
        logger.info("Publishing newsletter...")
        index_template = self.env.get_template("index_template.html")
        story_template = self.env.get_template("story_template.html")
        
        today_date = datetime.date.today()
        today_str_display = today_date.strftime("%B %d, %Y")
        today_str_folder = today_date.strftime("%Y-%m-%d")
        
        editions_dir = os.path.join(self.output_dir, "editions")
        if not os.path.exists(editions_dir):
            os.makedirs(editions_dir)
            
        editions = []
        if os.path.exists(editions_dir):
            editions = sorted([d for d in os.listdir(editions_dir) if os.path.isdir(os.path.join(editions_dir, d))], reverse=True)
            
        if today_str_folder not in editions:
            editions.insert(0, today_str_folder)
            
        for i, paper in enumerate(papers):
            if "story" in paper:
                paper["slug"] = f"story_{i}.html"
                
        # 1. Render for ROOT
        # For the root index, images are inside the latest edition's folder
        self._render_files(papers, index_template, story_template, today_str_display, today_str_folder, editions, self.output_dir, ".", f"editions/{today_str_folder}")
        
        # 2. Render for EDITION FOLDER
        # For the edition index, images are locally in the 'images' folder
        edition_output_dir = os.path.join(editions_dir, today_str_folder)
        os.makedirs(edition_output_dir, exist_ok=True)
        self._render_files(papers, index_template, story_template, today_str_display, today_str_folder, editions, edition_output_dir, "../..", ".")

        import shutil
        graph_template_path = os.path.join(self.template_dir, "graph_template.html")
        if os.path.exists(graph_template_path):
            shutil.copy(graph_template_path, os.path.join(self.output_dir, "graph.html"))
            
        self._update_all_dropdowns(editions)
            
        logger.info(f"Newsletter published to {self.output_dir}/index.html")
        return os.path.join(self.output_dir, "index.html")
        
    def _update_all_dropdowns(self, editions):
        import re
        editions_dir = os.path.join(self.output_dir, "editions")
        if not os.path.exists(editions_dir):
            return
            
        for ed in editions:
            ed_path = os.path.join(editions_dir, ed)
            if not os.path.isdir(ed_path):
                continue
                
            options = []
            for e in editions:
                if e != ed:
                    options.append(f'                            <option value="../../editions/{e}/index.html">{e}</option>')
            options_html = "\n".join(options)
            
            new_select = f"""<select onchange="if (this.value) window.location.href=this.value;" style="padding: 5px; font-family: 'Georgia', serif; border-radius: 4px; border: 1px solid #ccc;">
                    <option value="../../index.html">Current Edition</option>
                    <optgroup label="Previous Editions">
{options_html}
                    </optgroup>
                </select>"""
                
            for root, dirs, files in os.walk(ed_path):
                for file in files:
                    if file.endswith(".html"):
                        filepath = os.path.join(root, file)
                        with open(filepath, "r") as f:
                            content = f.read()
                        content = re.sub(r'<select onchange="if \(this\.value\) window\.location\.href=this\.value;".*?</select>', new_select, content, flags=re.DOTALL)
                        with open(filepath, "w") as f:
                            f.write(content)
        
    def _render_files(self, papers, index_template, story_template, date_display, folder_date, editions, out_dir, root_path, image_base_path):
        html_content = index_template.render(
            date=date_display,
            folder_date=folder_date,
            papers=papers,
            editions=editions,
            root_path=root_path,
            image_base_path=image_base_path
        )
        with open(os.path.join(out_dir, "index.html"), "w") as f:
            f.write(html_content)
            
        for paper in papers:
            if "story" in paper:
                story_html = story_template.render(
                    date=date_display,
                    folder_date=folder_date,
                    paper=paper,
                    editions=editions,
                    root_path=root_path,
                    image_base_path=image_base_path
                )
                with open(os.path.join(out_dir, paper["slug"]), "w") as f:
                    f.write(story_html)
