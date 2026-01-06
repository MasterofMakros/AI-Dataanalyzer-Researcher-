import subprocess
import json
import logging
import os

logger = logging.getLogger("worker.validator")

def validate_media_file(file_path: str) -> bool:
    """
    SOP-003: Pre-Flight Inspection.
    Validates that a media file is readable by ffmpeg and has valid streams.
    Returns True if valid, False (and logs error) if corrupt.
    """
    if not os.path.exists(file_path):
        logger.error(f"Validation failed: File not found {file_path}")
        return False
        
    if os.path.getsize(file_path) == 0:
        logger.error(f"Validation failed: Empty file {file_path}")
        return False

    try:
        # Run ffprobe to extract metadata
        # -v error : Silence output unless error
        # -show_entries : Get duration and format
        # -of json : Parseable output
        cmd = [
            "ffprobe", 
            "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "json", 
            file_path
        ]
        
        # Timeout after 10s to prevent hangs on partially downloaded files
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, text=True)
        
        if result.returncode != 0:
            logger.error(f"Validation failed (ffprobe error): {result.stderr}")
            return False
            
        metadata = json.loads(result.stdout)
        duration = float(metadata.get('format', {}).get('duration', 0))
        
        if duration < 0.1:
            logger.error(f"Validation failed: Duration too short ({duration}s)")
            return False
            
        logger.info(f"Validation passed: {os.path.basename(file_path)} ({duration}s)")
        return True
        
    except subprocess.TimeoutExpired:
        logger.error(f"Validation failed: Timeout (Disk I/O or Corrupt Header)")
        return False
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Test run
    import sys
    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) > 1:
        validate_media_file(sys.argv[1])
    else:
        print("Usage: python validate_media.py <file>")
