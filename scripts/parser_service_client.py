"""
Neural Vault - Parser Service Client
=====================================

HTTP-Client für den Docker-basierten Parser Service.
Ersetzt lokale Python-Bibliotheken durch API-Aufrufe.

Verwendung:
    from parser_service_client import parse_file_docker, is_parser_available

    result = parse_file_docker(Path("file.torrent"))
    print(result.summary)
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

# Parser Service URL
PARSER_SERVICE_URL = os.getenv("PARSER_SERVICE_URL", "http://localhost:8002")

# Pfad-Mapping für Docker
from config.paths import BASE_DIR

# Default to BASE_DIR if HOST_DATA_PATH not set
HOST_DATA_PATH = Path(os.getenv("HOST_DATA_PATH", str(BASE_DIR)))
CONTAINER_DATA_PATH = os.getenv("CONTAINER_DATA_PATH", "/mnt/data")


@dataclass
class ParserResult:
    """Ergebnis vom Parser Service."""
    filepath: str
    filename: str
    extension: str
    file_type: str
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_text: str = ""
    summary: str = ""
    completeness: float = 0.0
    confidence: float = 0.0
    error: str = ""
    processing_time: float = 0.0


def host_to_container_path(host_path: Path) -> str:
    """Konvertiere Host-Pfad zu Container-Pfad."""
    try:
        rel_path = host_path.relative_to(HOST_DATA_PATH)
        return f"{CONTAINER_DATA_PATH}/{rel_path.as_posix()}"
    except ValueError:
        return str(host_path)


def is_parser_available() -> bool:
    """Prüfe ob Parser Service erreichbar ist."""
    try:
        r = requests.get(f"{PARSER_SERVICE_URL}/health", timeout=5)
        return r.ok and r.json().get("status") == "healthy"
    except:
        return False


def get_supported_extensions() -> list:
    """Hole Liste der unterstützten Erweiterungen vom Service."""
    try:
        r = requests.get(f"{PARSER_SERVICE_URL}/supported", timeout=5)
        if r.ok:
            return r.json().get("extensions", [])
    except:
        pass
    return []


def parse_file_docker(filepath: Path, use_upload: bool = False) -> ParserResult:
    """
    Parse eine Datei über den Docker Parser Service.
    
    Args:
        filepath: Pfad zur Datei
        use_upload: True = Datei hochladen, False = Pfad übergeben (schneller)
    
    Returns:
        ParserResult mit extrahierten Daten
    """
    if use_upload:
        # Datei hochladen (für Dateien außerhalb des gemounteten Volumes)
        try:
            with open(filepath, "rb") as f:
                files = {"file": (filepath.name, f)}
                r = requests.post(
                    f"{PARSER_SERVICE_URL}/parse",
                    files=files,
                    timeout=120
                )
            
            if r.ok:
                data = r.json()
                return ParserResult(**data)
            else:
                return ParserResult(
                    filepath=str(filepath),
                    filename=filepath.name,
                    extension=filepath.suffix,
                    file_type="unknown",
                    error=f"HTTP {r.status_code}: {r.text[:100]}"
                )
        except Exception as e:
            return ParserResult(
                filepath=str(filepath),
                filename=filepath.name,
                extension=filepath.suffix,
                file_type="unknown",
                error=str(e)
            )
    else:
        # Pfad übergeben (für Dateien im gemounteten Volume)
        container_path = host_to_container_path(filepath)
        try:
            r = requests.post(
                f"{PARSER_SERVICE_URL}/parse/path",
                params={"filepath": container_path},
                timeout=120
            )
            
            if r.ok:
                data = r.json()
                # Originalpfad wiederherstellen
                data["filepath"] = str(filepath)
                return ParserResult(**data)
            else:
                return ParserResult(
                    filepath=str(filepath),
                    filename=filepath.name,
                    extension=filepath.suffix,
                    file_type="unknown",
                    error=f"HTTP {r.status_code}: {r.text[:100]}"
                )
        except Exception as e:
            return ParserResult(
                filepath=str(filepath),
                filename=filepath.name,
                extension=filepath.suffix,
                file_type="unknown",
                error=str(e)
            )


def is_docker_processable(filepath: Path) -> bool:
    """Prüfe ob Datei vom Docker Service verarbeitet werden kann."""
    ext = filepath.suffix.lower()
    supported = get_supported_extensions()
    return ext in supported


# CLI Test
if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("PARSER SERVICE CLIENT")
    print("=" * 60)
    
    # Health Check
    available = is_parser_available()
    print(f"\nService verfügbar: {'✅' if available else '❌'}")
    
    if available:
        extensions = get_supported_extensions()
        print(f"Unterstützte Erweiterungen: {', '.join(extensions)}")
        
        # Test mit Argument
        if len(sys.argv) > 1:
            test_file = Path(sys.argv[1])
            if test_file.exists():
                print(f"\nTeste: {test_file}")
                result = parse_file_docker(test_file)
                print(f"Erfolg: {'✅' if result.success else '❌'}")
                print(f"Summary: {result.summary}")
                if result.error:
                    print(f"Fehler: {result.error}")
