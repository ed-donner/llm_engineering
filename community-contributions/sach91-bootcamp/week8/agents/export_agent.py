"""
Export Agent - Generates formatted reports and exports
"""
import logging
from typing import List, Dict
from datetime import datetime
from agents.base_agent import BaseAgent
from models.document import Summary

logger = logging.getLogger(__name__)

class ExportAgent(BaseAgent):
    """Agent that exports summaries and reports in various formats"""
    
    def __init__(self, llm_client=None, model: str = "llama3.2"):
        """
        Initialize export agent
        
        Args:
            llm_client: Optional shared LLM client
            model: Ollama model name
        """
        super().__init__(name="ExportAgent", llm_client=llm_client, model=model)
        
        logger.info(f"{self.name} initialized")
    
    def process(self, content: Dict, format: str = "markdown") -> str:
        """
        Export content in specified format
        
        Args:
            content: Content dictionary to export
            format: Export format ('markdown', 'text', 'html')
            
        Returns:
            Formatted content string
        """
        logger.info(f"{self.name} exporting as {format}")
        
        if format == "markdown":
            return self._export_markdown(content)
        elif format == "text":
            return self._export_text(content)
        elif format == "html":
            return self._export_html(content)
        else:
            return str(content)
    
    def _export_markdown(self, content: Dict) -> str:
        """Export as Markdown"""
        md = []
        md.append(f"# Knowledge Report")
        md.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        if 'title' in content:
            md.append(f"## {content['title']}\n")
        
        if 'summary' in content:
            md.append(f"### Summary\n")
            md.append(f"{content['summary']}\n")
        
        if 'key_points' in content and content['key_points']:
            md.append(f"### Key Points\n")
            for point in content['key_points']:
                md.append(f"- {point}")
            md.append("")
        
        if 'sections' in content:
            for section in content['sections']:
                md.append(f"### {section['title']}\n")
                md.append(f"{section['content']}\n")
        
        if 'sources' in content and content['sources']:
            md.append(f"### Sources\n")
            for i, source in enumerate(content['sources'], 1):
                md.append(f"{i}. {source}")
            md.append("")
        
        return "\n".join(md)
    
    def _export_text(self, content: Dict) -> str:
        """Export as plain text"""
        lines = []
        lines.append("=" * 60)
        lines.append("KNOWLEDGE REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("=" * 60)
        lines.append("")
        
        if 'title' in content:
            lines.append(content['title'])
            lines.append("-" * len(content['title']))
            lines.append("")
        
        if 'summary' in content:
            lines.append("SUMMARY:")
            lines.append(content['summary'])
            lines.append("")
        
        if 'key_points' in content and content['key_points']:
            lines.append("KEY POINTS:")
            for i, point in enumerate(content['key_points'], 1):
                lines.append(f"  {i}. {point}")
            lines.append("")
        
        if 'sections' in content:
            for section in content['sections']:
                lines.append(section['title'].upper())
                lines.append("-" * 40)
                lines.append(section['content'])
                lines.append("")
        
        if 'sources' in content and content['sources']:
            lines.append("SOURCES:")
            for i, source in enumerate(content['sources'], 1):
                lines.append(f"  {i}. {source}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _export_html(self, content: Dict) -> str:
        """Export as HTML"""
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append("  <meta charset='utf-8'>")
        html.append("  <title>Knowledge Report</title>")
        html.append("  <style>")
        html.append("    body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }")
        html.append("    h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }")
        html.append("    h2 { color: #555; margin-top: 30px; }")
        html.append("    .meta { color: #888; font-style: italic; }")
        html.append("    .key-points { background: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; }")
        html.append("    .source { color: #666; font-size: 0.9em; }")
        html.append("  </style>")
        html.append("</head>")
        html.append("<body>")
        
        html.append("  <h1>Knowledge Report</h1>")
        html.append(f"  <p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>")
        
        if 'title' in content:
            html.append(f"  <h2>{content['title']}</h2>")
        
        if 'summary' in content:
            html.append(f"  <h3>Summary</h3>")
            html.append(f"  <p>{content['summary']}</p>")
        
        if 'key_points' in content and content['key_points']:
            html.append("  <h3>Key Points</h3>")
            html.append("  <div class='key-points'>")
            html.append("    <ul>")
            for point in content['key_points']:
                html.append(f"      <li>{point}</li>")
            html.append("    </ul>")
            html.append("  </div>")
        
        if 'sections' in content:
            for section in content['sections']:
                html.append(f"  <h3>{section['title']}</h3>")
                html.append(f"  <p>{section['content']}</p>")
        
        if 'sources' in content and content['sources']:
            html.append("  <h3>Sources</h3>")
            html.append("  <ol class='source'>")
            for source in content['sources']:
                html.append(f"    <li>{source}</li>")
            html.append("  </ol>")
        
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)
    
    def create_study_guide(self, summaries: List[Summary]) -> str:
        """
        Create a study guide from multiple summaries
        
        Args:
            summaries: List of Summary objects
            
        Returns:
            Formatted study guide
        """
        logger.info(f"{self.name} creating study guide from {len(summaries)} summaries")
        
        # Compile all content
        all_summaries = "\n\n".join([
            f"{s.document_name}:\n{s.summary_text}" 
            for s in summaries
        ])
        
        all_key_points = []
        for s in summaries:
            all_key_points.extend(s.key_points)
        
        # Use LLM to create cohesive study guide
        system_prompt = """You create excellent study guides that synthesize information from multiple sources.
Create a well-organized study guide with clear sections, key concepts, and important points."""
        
        user_prompt = f"""Create a comprehensive study guide based on these document summaries:

{all_summaries}

Create a well-structured study guide with:
1. An overview
2. Key concepts
3. Important details
4. Study tips

Study Guide:"""
        
        study_guide = self.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.5,
            max_tokens=2048
        )
        
        # Format as markdown
        content = {
            'title': 'Study Guide',
            'sections': [
                {'title': 'Overview', 'content': study_guide},
                {'title': 'Key Points from All Documents', 'content': '\n'.join([f"• {p}" for p in all_key_points[:15]])}
            ],
            'sources': [s.document_name for s in summaries]
        }
        
        return self._export_markdown(content)
