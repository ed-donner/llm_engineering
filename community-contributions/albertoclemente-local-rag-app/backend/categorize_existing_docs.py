#!/usr/bin/env python3
"""
Script to categorize all existing documents that were indexed before
the categorization feature was implemented.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.storage import get_document_storage
from app.categorization import categorize_document
from app.diagnostics import get_logger

logger = get_logger(__name__)


async def categorize_existing_documents():
    """
    Find all documents without categories and categorize them.
    """
    try:
        # Get storage instance
        storage = get_document_storage()
        
        # List all documents
        print("Loading all documents...")
        logger.info("Loading all documents...")
        documents = await storage.list_documents()
        
        if not documents:
            print("No documents found in the system")
            logger.info("No documents found in the system")
            return
        
        print(f"Found {len(documents)} total documents")
        print(f"Found {len(documents)} total documents")
        logger.info(f"Found {len(documents)} total documents")
        
        # Filter documents that need categorization
        uncategorized = []
        already_categorized = []
        
        for doc in documents:
            if not doc.categories or len(doc.categories) == 0:
                uncategorized.append(doc)
            else:
                already_categorized.append(doc)
        
        print(f"Documents already categorized: {len(already_categorized)}")
        print(f"Documents needing categorization: {len(uncategorized)}")
        logger.info(f"Documents already categorized: {len(already_categorized)}")
        print(f"Documents needing categorization: {len(uncategorized)}")
        logger.info(f"Documents needing categorization: {len(uncategorized)}")
        
        if not uncategorized:
            print("All documents are already categorized!")
            logger.info("All documents are already categorized!")
            return
        
        # Categorize each uncategorized document
        success_count = 0
        fail_count = 0
        
        for i, doc in enumerate(uncategorized, 1):
            try:
                print(f"\n[{i}/{len(uncategorized)}] Categorizing: {doc.name} (ID: {doc.id})")
                logger.info(f"\n[{i}/{len(uncategorized)}] Categorizing: {doc.name} (ID: {doc.id})")
                
                # Load parsed content
                parsed_data = await storage.load_parsed_content(doc.id)
                
                if not parsed_data:
                    logger.warning(f"  ⚠️  No parsed content found for {doc.name} - skipping")
                    fail_count += 1
                    continue
                
                # Categorize
                categorization_result = await categorize_document(
                    parsed_content=parsed_data,
                    doc_name=doc.name,
                    force_recategorize=True  # Force categorization
                )
                
                # Update document metadata
                await storage.update_document_metadata(
                    doc.id,
                    {
                        "categories": categorization_result.get("categories", []),
                        "category_confidence": categorization_result.get("confidence"),
                        "category_generated_at": categorization_result.get("generated_at"),
                        "category_method": categorization_result.get("method", "auto"),
                        "category_language": categorization_result.get("language"),
                        "category_subcategories": categorization_result.get("subcategories", {})
                    }
                )
                
                categories = categorization_result.get("categories", [])
                confidence = categorization_result.get("confidence", 0)
                subcategories = categorization_result.get("subcategories", {})
                
                logger.info(f"  ✅ Categories: {categories}")
                logger.info(f"  📊 Confidence: {confidence:.2%}")
                if subcategories:
                    logger.info(f"  🔍 Subcategories: {subcategories}")
                
                success_count += 1
                
                # Small delay to avoid overwhelming the LLM API
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"  ❌ Failed to categorize {doc.name}: {e}")
                fail_count += 1
                continue
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("CATEGORIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Total documents processed: {len(uncategorized)}")
        logger.info(f"✅ Successfully categorized: {success_count}")
        logger.info(f"❌ Failed: {fail_count}")
        logger.info(f"📚 Already categorized: {len(already_categorized)}")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in categorization script: {e}")
        raise


def main():
    """Main entry point"""
    print("\n🏷️  Document Categorization Script")
    print("=" * 60)
    print("This script will categorize all documents that were indexed")
    print("before the categorization feature was implemented.\n")
    
    # Run async function
    asyncio.run(categorize_existing_documents())


if __name__ == "__main__":
    main()
