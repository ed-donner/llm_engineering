from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Chunk(BaseModel):
    page_content: str
    metadata: Dict[str, Any]

class PharmaChunker:
    """
    Splits OpenFDA drug label JSON into semantically meaningful chunks.
    Preserves context (Drug Name, Section Name) in each chunk.
    """
    
    # Critical sections that pharmacists care about
    TARGET_SECTIONS = [
        "indications_and_usage",
        "dosage_and_administration",
        "warnings",
        "boxed_warning",
        "adverse_reactions",
        "contraindications",
        "precautions",
        "drug_interactions",
        "use_in_specific_populations"
    ]

    def chunk_drug_label(self, json_data: Dict[str, Any]) -> List[Chunk]:
        """
        Takes a single OpenFDA drug label JSON object.
        Returns a list of semantic chunks.
        """
        chunks = []
        
        # 1. Extract Drug Metadata (The Context)
        openfda = json_data.get("openfda", {})
        # Brand name is often a list, take first or fallback
        brand_name = openfda.get("brand_name", ["Unknown"])[0] 
        generic_name = openfda.get("generic_name", ["Unknown"])[0]
        
        # Robust name display
        drug_display_name = brand_name if brand_name != "Unknown" else generic_name
        
        # 2. Iterate through specific medical sections
        for section_key in self.TARGET_SECTIONS:
            if section_key not in json_data:
                continue
                
            # OpenFDA content is often a list of strings ["Text val..."]
            raw_content = json_data[section_key]
            text_content = ""
            
            if isinstance(raw_content, list):
                text_content = "\n".join(raw_content)
            elif isinstance(raw_content, str):
                text_content = raw_content
                
            if not text_content.strip():
                continue
                
            # 3. Clean the text (basic cleanup)
            text_content = self._clean_text(text_content)
            
            # 4. Create Semantic Chunks
            # If the section is huge, we might split it further (Todo: recursive splitter)
            # For now, we take the whole section as one "Semantic Unit" if it's reasonable size,
            # or simple paragraph split if massive.
            
            # Formatted Context Header
            # This is the "Engineering Twist" - forcing the model to see context
            section_title = section_key.replace("_", " ").upper()
            
            context_header = (
                f"DRUG: {drug_display_name} ({generic_name})\n"
                f"SECTION: {section_title}\n"
            )
            
            # Combine
            full_chunk_text = f"{context_header}\n{text_content}"
            
            # Create object
            chunk = Chunk(
                page_content=full_chunk_text,
                metadata={
                    "source": "openfda",
                    "drug_name": drug_display_name,
                    "generic_name": generic_name,
                    "section": section_key,
                    "original_length": len(text_content)
                }
            )
            chunks.append(chunk)

        return chunks

    def _clean_text(self, text: str) -> str:
        """Basic text cleanup."""
        # Remove common XML/HTML tags if found in OpenFDA data
        # (OpenFDA sometimes has <br>, <table>, etc.)
        # For a raw regex approach:
        import re
        text = re.sub(r'<[^>]+>', '', text) # Strip HTML tags
        return text.strip()