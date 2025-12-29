
import os
import time
import logging
from docling.document_converter import DocumentConverter

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DeepIngest")

class DeepIngestService:
    def __init__(self):
        logger.info("🧠 Initializing Deep Ingest Service (Docling)...")
        self.converter = DocumentConverter()
        logger.info("✅ Docling Model Loaded.")

    def process_file(self, file_path):
        """
        Deep extraction of a PDF file using Docling.
        Returns:
            - markdown_content (str): The full markdown with tables.
            - meta (dict): Metadata (images, tables found).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"🐢 Starting Deep Extract on: {file_path}")
        start_time = time.time()
        
        try:
            result = self.converter.convert(file_path)
            md_content = result.document.export_to_markdown()
            
            # Simple metadata extraction from the result object if available
            # For now we just return basic stats
            elapsed = time.time() - start_time
            logger.info(f"🏁 Finished in {elapsed:.2f}s. Extracted {len(md_content)} chars.")
            
            return md_content, {"elapsed": elapsed, "size": len(md_content)}
            
        except Exception as e:
            logger.error(f"❌ Deep Extract Failed: {str(e)}")
            raise e

if __name__ == "__main__":
    # Test Run
    import sys
    if len(sys.argv) > 1:
        service = DeepIngestService()
        md, _ = service.process_file(sys.argv[1])
        print(md[:500] + "\n...\n[Truncated]")
    else:
        print("Usage: python deep_ingest.py <path_to_pdf>")
