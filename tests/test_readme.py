import os
import pytest

README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

def test_readme_exists():
    assert os.path.exists(README_PATH), "README.md should exist in the root directory"

def test_readme_content():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check for critical sections
    assert "# Conductor" in content
    assert "## 📋 Inhaltsverzeichnis" in content
    assert "## Architektur" in content
    assert "## Benchmarks" in content
    assert "## Schnellstart" in content
    
    # Check for Mermaid diagram
    assert "```mermaid" in content
    
    # Check for Benchmarks
    assert "| **OCR (Surya)** |" in content
    assert "| **97.7%** |" in content

def test_readme_links():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check simple relative links existence (naive check)
    if "LICENSE" in content:
        assert os.path.exists(os.path.join(os.path.dirname(README_PATH), "LICENSE"))
