#!/usr/bin/env python3
"""
E2E format coverage harness.

Primary ingest: file-drop + smart_ingest.py --once
Fallback ingest: file_indexer.py --path --limit
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import requests
except ImportError:  # pragma: no cover
    print("ERROR: 'requests' is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key and key not in os.environ:
            os.environ[key] = val


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="E2E format coverage harness")
    parser.add_argument("--mode", choices=["base", "overlay"], default="base")
    parser.add_argument("--ingest", choices=["smart", "indexer"], default="smart")
    parser.add_argument("--samples", default="data/samples")
    parser.add_argument("--artifacts", default="artifacts/e2e")
    parser.add_argument("--timeout-min", type=int, default=20)
    parser.add_argument("--poll-sec", type=int, default=5)
    parser.add_argument("--max-samples", type=int, default=0, help="Limit number of samples (0 = all)")
    parser.add_argument("--inbox")
    parser.add_argument("--archive-root")
    parser.add_argument("--quarantine-root")
    parser.add_argument("--ledger")
    parser.add_argument("--qdrant-url", default="http://localhost:6335")
    parser.add_argument("--qdrant-collection", default="neural_vault")
    parser.add_argument("--qdrant-api-key")
    parser.add_argument("--search-url", default="http://localhost:8040/api/neural-search")
    parser.add_argument("--search-limit", type=int, default=8)
    parser.add_argument("--keep-inbox", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def resolve_path(value: Optional[str], env_key: str, fallback: Path) -> Path:
    if value:
        return Path(value).resolve()
    env_val = os.environ.get(env_key)
    if env_val:
        return Path(env_val).resolve()
    return fallback.resolve()


def derive_conductor_root(ledger_path: Path, default_root: Path) -> Path:
    if ledger_path.name == "shadow_ledger.db" and ledger_path.parent.name == "data":
        return ledger_path.parent.parent
    env_root = os.environ.get("CONDUCTOR_ROOT")
    if env_root:
        return Path(env_root)
    return default_root


def path_is_under(child: Path, root: Path) -> bool:
    try:
        child.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def http_get(url: str, timeout: int = 5, headers: Optional[Dict] = None) -> Tuple[bool, str]:
    try:
        resp = requests.get(url, headers=headers or {}, timeout=timeout)
        return resp.status_code == 200, f"status={resp.status_code}"
    except Exception as exc:
        return False, str(exc)


def http_post_json(url: str, payload: Dict, headers: Optional[Dict] = None, timeout: int = 10) -> Tuple[bool, str, Optional[Dict]]:
    try:
        resp = requests.post(url, json=payload, headers=headers or {}, timeout=timeout)
        if resp.status_code != 200:
            return False, f"status={resp.status_code}", None
        return True, "ok", resp.json()
    except Exception as exc:
        return False, str(exc), None


def get_qdrant_count(qdrant_url: str, collection: str, headers: Dict) -> Tuple[Optional[int], str]:
    try:
        resp = requests.get(f"{qdrant_url}/collections/{collection}", headers=headers, timeout=5)
        if resp.status_code != 200:
            return None, f"status={resp.status_code}"
        data = resp.json().get("result", {})
        if "points_count" in data:
            count = data.get("points_count")
        else:
            count = data.get("vectors_count")
        return int(count) if count is not None else None, "ok"
    except Exception as exc:
        return None, str(exc)


def qdrant_find_by_filename(qdrant_url: str, collection: str, headers: Dict, filename: str) -> Tuple[bool, str]:
    payload = {
        "limit": 1,
        "with_payload": True,
        "with_vector": False,
        "filter": {
            "must": [
                {"key": "original_filename", "match": {"value": filename}}
            ]
        }
    }
    ok, msg, data = http_post_json(
        f"{qdrant_url}/collections/{collection}/points/scroll",
        payload,
        headers=headers,
        timeout=10,
    )
    if not ok or not data:
        return False, msg
    points = data.get("result", {}).get("points", [])
    return (len(points) > 0), f"points={len(points)}"


def qdrant_find_by_field(
    qdrant_url: str,
    collection: str,
    headers: Dict,
    field: str,
    value: str,
) -> Tuple[bool, str]:
    payload = {
        "limit": 1,
        "with_payload": True,
        "with_vector": False,
        "filter": {
            "must": [
                {"key": field, "match": {"value": value}}
            ]
        }
    }
    ok, msg, data = http_post_json(
        f"{qdrant_url}/collections/{collection}/points/scroll",
        payload,
        headers=headers,
        timeout=10,
    )
    if not ok or not data:
        return False, msg
    points = data.get("result", {}).get("points", [])
    return (len(points) > 0), f"points={len(points)}"


def qdrant_scan_for_token(
    qdrant_url: str,
    collection: str,
    headers: Dict,
    token: str,
    limit: int = 100,
) -> Tuple[bool, str]:
    payload = {"limit": limit, "with_payload": True, "with_vector": False}
    ok, msg, data = http_post_json(
        f"{qdrant_url}/collections/{collection}/points/scroll",
        payload,
        headers=headers,
        timeout=10,
    )
    if not ok or not data:
        return False, msg
    points = data.get("result", {}).get("points", [])
    for point in points:
        payload_data = point.get("payload", {})
        for key in ["extracted_text", "content", "text", "meta_description"]:
            value = payload_data.get(key, "")
            if value and token in value:
                return True, f"token_found_in={key}"
    return False, f"token_not_found_in_scroll(limit={limit})"


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").lower().strip()


def path_matches(source_path: str, target_path: str) -> bool:
    if not source_path or not target_path:
        return False
    source_norm = normalize_path(source_path)
    target_norm = normalize_path(target_path)
    if source_norm == target_norm:
        return True
    target_name = normalize_path(Path(target_path).name)
    if target_name and source_norm.endswith(f"/{target_name}"):
        return True
    return False


def evaluate_search_api(
    search_url: str,
    token: str,
    limit: int,
    ledger_path: Optional[str],
    current_filename: Optional[str],
) -> Dict[str, str]:
    ok, msg, data = http_post_json(search_url, {"query": token, "limit": limit})
    if not ok or not data:
        return {
            "status": "fail",
            "level": "fail",
            "matched_on": "none",
            "details": f"request_failed: {msg}",
        }

    sources = data.get("sources", [])
    if not sources:
        return {
            "status": "fail",
            "level": "fail",
            "matched_on": "none",
            "details": "no_sources_returned",
        }

    for source in sources:
        excerpt = source.get("excerpt", "") or ""
        filename = source.get("filename", "") or ""
        path = source.get("path", "") or ""

        if ledger_path and path_matches(path, ledger_path):
            return {
                "status": "pass",
                "level": "strong",
                "matched_on": "path",
                "details": "search_source_path_matches_ledger",
            }

        if current_filename and filename and filename == current_filename:
            return {
                "status": "pass",
                "level": "strong",
                "matched_on": "filename",
                "details": "search_source_filename_matches_ledger",
            }

        if token in excerpt or token in filename or token in path:
            return {
                "status": "pass",
                "level": "medium",
                "matched_on": "token",
                "details": "token_found_in_source_fields",
            }

    return {
        "status": "fail",
        "level": "fail",
        "matched_on": "none",
        "details": "token_or_path_not_found_in_sources",
    }


def qdrant_retrieval_fallback(
    qdrant_url: str,
    collection: str,
    headers: Dict,
    ledger_path: Optional[str],
    file_hash: Optional[str],
    ingest_name: Optional[str],
    token: str,
) -> Dict[str, str]:
    if ledger_path:
        found, msg = qdrant_find_by_field(qdrant_url, collection, headers, "file_path", ledger_path)
        if found:
            return {"status": "pass", "matched_on": "path", "details": msg}

    if file_hash:
        found, msg = qdrant_find_by_field(qdrant_url, collection, headers, "id", file_hash)
        if found:
            return {"status": "pass", "matched_on": "hash", "details": msg}

    if ingest_name:
        found, msg = qdrant_find_by_field(qdrant_url, collection, headers, "original_filename", ingest_name)
        if found:
            return {"status": "pass", "matched_on": "filename", "details": msg}

    found, msg = qdrant_scan_for_token(qdrant_url, collection, headers, token, limit=100)
    if found:
        return {"status": "pass", "matched_on": "token", "details": msg}

    return {"status": "fail", "matched_on": "none", "details": msg}


def prepare_subprocess_env(env: Dict) -> Dict:
    merged = env.copy()
    repo_root = str(REPO_ROOT)
    existing = merged.get("PYTHONPATH", "")
    if existing:
        merged["PYTHONPATH"] = repo_root + os.pathsep + existing
    else:
        merged["PYTHONPATH"] = repo_root
    merged.setdefault("PYTHONUTF8", "1")
    merged.setdefault("PYTHONIOENCODING", "utf-8")
    return merged


def run_subprocess(cmd: List[str], env: Dict, timeout_sec: Optional[int] = None) -> Tuple[int, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            env=prepare_subprocess_env(env),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_sec,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or "")[-2000:]
        stderr = (exc.stderr or "")[-2000:]
        output = stdout + ("\n" + stderr if stderr else "")
        return 124, (output.strip() or "timeout")
    stdout = (result.stdout or "")[-2000:]
    stderr = (result.stderr or "")[-2000:]
    output = stdout + ("\n" + stderr if stderr else "")
    return result.returncode, output.strip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_pdf(path: Path, text: str) -> None:
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 72 Td ({text}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
        "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        f"4 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj\n",
        "5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    pdf = b"%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf += obj.encode("ascii")
    xref_pos = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    pdf += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf += f"{off:010d} 00000 n \n".encode("ascii")
    pdf += (
        f"trailer << /Root 1 0 R /Size {len(objects) + 1} >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode("ascii")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)


def write_docx(path: Path, text: str) -> None:
    import zipfile

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document)


def write_xlsx(path: Path, text: str) -> None:
    import zipfile

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>
"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>
"""
    sheet = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="s"><v>0</v></c>
    </row>
  </sheetData>
</worksheet>
"""
    shared_strings = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="1" uniqueCount="1">
  <si><t>{text}</t></si>
</sst>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
        zf.writestr("xl/sharedStrings.xml", shared_strings)


def ensure_sample_file(sample: Dict, samples_root: Path) -> Tuple[Optional[Path], Optional[str]]:
    rel_path = Path(sample["rel_path"])
    path = samples_root / rel_path
    if path.exists():
        return path, None

    token = sample["token"]
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            write_text(path, f"{token}\n")
        elif suffix == ".html":
            write_text(path, f"<html><body><p>{token}</p></body></html>\n")
        elif suffix == ".json":
            write_text(path, json.dumps({"token": token}, indent=2) + "\n")
        elif suffix == ".csv":
            write_text(path, f"id,token\n1,{token}\n")
        elif suffix == ".eml":
            content = (
                "From: e2e@example.com\n"
                "To: e2e@example.com\n"
                f"Subject: {token}\n"
                "Date: Tue, 01 Jan 2030 00:00:00 +0000\n"
                "Content-Type: text/plain; charset=utf-8\n"
                "\n"
                f"Hello {token}\n"
            )
            write_text(path, content)
        elif suffix == ".pdf":
            write_pdf(path, token)
        elif suffix == ".docx":
            write_docx(path, token)
        elif suffix == ".xlsx":
            write_xlsx(path, token)
        elif suffix == ".stl":
            write_text(path, f"solid {token}\nendsolid {token}\n")
        elif suffix == ".geojson":
            write_text(
                path,
                json.dumps(
                    {
                        "type": "FeatureCollection",
                        "features": [
                            {"type": "Feature", "properties": {"token": token}, "geometry": {"type": "Point", "coordinates": [0, 0]}}
                        ],
                    },
                    indent=2,
                )
                + "\n",
            )
        else:
            return None, f"no_generator_for_suffix={suffix}"
        return path, "generated"
    except Exception as exc:
        return None, f"generation_failed: {exc}"


def build_samples(mode: str) -> List[Dict]:
    base = [
        {"id": "txt", "rel_path": "text/hello.txt", "class": "text", "token": "E2E_TOKEN_TXT", "modes": ["base", "overlay"]},
        {"id": "md", "rel_path": "text/note.md", "class": "text", "token": "E2E_TOKEN_MD", "modes": ["base", "overlay"]},
        {"id": "html", "rel_path": "text/page.html", "class": "text", "token": "E2E_TOKEN_HTML", "modes": ["base", "overlay"]},
        {"id": "json", "rel_path": "text/sample.json", "class": "text", "token": "E2E_TOKEN_JSON", "modes": ["base", "overlay"]},
        {"id": "csv", "rel_path": "text/sample.csv", "class": "text", "token": "E2E_TOKEN_CSV", "modes": ["base", "overlay"]},
        {"id": "pdf", "rel_path": "pdf/text.pdf", "class": "pdf", "token": "E2E_TOKEN_PDF_TEXT", "modes": ["base", "overlay"]},
        {"id": "docx", "rel_path": "office/doc.docx", "class": "office", "token": "E2E_TOKEN_DOCX", "modes": ["base", "overlay"]},
        {"id": "xlsx", "rel_path": "office/sheet.xlsx", "class": "office", "token": "E2E_TOKEN_XLSX", "modes": ["base", "overlay"]},
        {"id": "eml", "rel_path": "email/mail.eml", "class": "email", "token": "E2E_TOKEN_EML", "modes": ["base", "overlay"]},
    ]
    overlay = [
        {"id": "stl", "rel_path": "overlay_only/cube.stl", "class": "3d", "token": "E2E_TOKEN_STL", "modes": ["overlay"]},
        {"id": "geojson", "rel_path": "overlay_only/point.geojson", "class": "gis", "token": "E2E_TOKEN_GEOJSON", "modes": ["overlay"]},
    ]
    samples = base + overlay
    return [s for s in samples if mode in s["modes"]]


def check_prereqs(
    search_url: str,
    qdrant_url: str,
    qdrant_headers: Dict,
    overlay: bool,
) -> Tuple[bool, List[str]]:
    messages = []
    ok = True

    search_ok, search_msg, _ = http_post_json(search_url, {"query": "health-check", "limit": 1}, timeout=5)
    if not search_ok:
        ok = False
        messages.append(f"search_endpoint_unreachable: {search_msg} ({search_url})")

    q_ok, q_msg = http_get(f"{qdrant_url}/collections", timeout=5, headers=qdrant_headers)
    if not q_ok:
        ok = False
        messages.append(f"qdrant_unreachable: {q_msg}")

    if overlay:
        special_ok, special_msg = http_get("http://localhost:8016/health", timeout=5)
        if not special_ok:
            ok = False
            messages.append(f"special_parser_unhealthy: {special_msg}")

    return ok, messages


def main() -> int:
    load_dotenv(REPO_ROOT / ".env")
    args = parse_args()

    run_id = dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
    samples_root = (REPO_ROOT / args.samples).resolve()
    artifacts_dir = (REPO_ROOT / args.artifacts).resolve()
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    inbox = resolve_path(args.inbox, "CONDUCTOR_INBOX", REPO_ROOT / "data" / "inbox")
    archive_root = resolve_path(args.archive_root, "CONDUCTOR_ARCHIVE", REPO_ROOT / "data" / "archive")
    quarantine_root = resolve_path(args.quarantine_root, "CONDUCTOR_QUARANTINE", REPO_ROOT / "data" / "quarantine")

    ledger_path = Path(args.ledger) if args.ledger else None
    if ledger_path is None:
        env_root = os.environ.get("CONDUCTOR_ROOT")
        if env_root:
            ledger_path = Path(env_root) / "data" / "shadow_ledger.db"
        else:
            ledger_path = REPO_ROOT / "data" / "shadow_ledger.db"

    conductor_root = derive_conductor_root(ledger_path, REPO_ROOT)

    qdrant_api_key = args.qdrant_api_key or os.environ.get("QDRANT_API_KEY", "")
    qdrant_headers = {"api-key": qdrant_api_key} if qdrant_api_key else {}

    prereq_ok, prereq_msgs = check_prereqs(
        args.search_url,
        args.qdrant_url,
        qdrant_headers,
        args.mode == "overlay",
    )
    if not prereq_ok:
        print("Prerequisites missing:")
        for msg in prereq_msgs:
            print(f"- {msg}")
        return 2

    if args.ingest == "smart" and not args.dry_run:
        inbox.mkdir(parents=True, exist_ok=True)
        archive_root.mkdir(parents=True, exist_ok=True)
        quarantine_root.mkdir(parents=True, exist_ok=True)
        (quarantine_root / "_review_needed").mkdir(parents=True, exist_ok=True)
        (quarantine_root / "_processing_error").mkdir(parents=True, exist_ok=True)
        (quarantine_root / "_low_confidence").mkdir(parents=True, exist_ok=True)
        (quarantine_root / "_duplicates").mkdir(parents=True, exist_ok=True)

        if not args.keep_inbox:
            existing_files = [p for p in inbox.iterdir() if p.is_file()]
            if existing_files:
                print("Inbox is not empty; refusing to run without --keep-inbox.")
                return 2

    samples = build_samples(args.mode)
    report = {
        "run_id": run_id,
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "mode": args.mode,
        "ingest_method": args.ingest,
        "env": {
            "samples_root": str(samples_root),
            "artifacts_dir": str(artifacts_dir),
            "inbox": str(inbox),
            "archive_root": str(archive_root),
            "quarantine_root": str(quarantine_root),
            "ledger": str(ledger_path),
            "qdrant_url": args.qdrant_url,
            "qdrant_collection": args.qdrant_collection,
            "search_url": args.search_url,
            "search_limit": args.search_limit,
        },
        "samples": [],
        "summary": {},
    }

    total = 0
    passed = 0
    failed = 0
    skipped = 0

    for sample in samples:
        total += 1
        if args.max_samples and total > args.max_samples:
            break
        sample_start = time.time()
        sample_result = {
            "id": sample["id"],
            "path": str(samples_root / sample["rel_path"]),
            "class": sample["class"],
            "token": sample["token"],
            "ingestion": {"started_at": dt.datetime.utcnow().isoformat() + "Z", "ended_at": None, "method": args.ingest},
            "checks": {},
            "status": "pending",
            "duration_sec": None,
            "error": None,
        }

        path, gen_note = ensure_sample_file(sample, samples_root)
        if path is None:
            sample_result["status"] = "skipped"
            sample_result["error"] = gen_note or "missing_sample"
            sample_result["ingestion"]["ended_at"] = dt.datetime.utcnow().isoformat() + "Z"
            sample_result["duration_sec"] = round(time.time() - sample_start, 2)
            report["samples"].append(sample_result)
            skipped += 1
            continue

        if gen_note:
            sample_result["checks"]["sample_generation"] = {"status": "pass", "details": gen_note}

        if args.dry_run:
            sample_result["status"] = "skipped"
            sample_result["error"] = "dry_run"
            sample_result["ingestion"]["ended_at"] = dt.datetime.utcnow().isoformat() + "Z"
            sample_result["duration_sec"] = round(time.time() - sample_start, 2)
            report["samples"].append(sample_result)
            skipped += 1
            continue

        token = sample["token"]
        ingest_name = f"{run_id}__{token}__{path.name}"
        if len(ingest_name) > 200:
            ingest_name = ingest_name[:200] + path.suffix

        inbox_path = inbox / ingest_name

        if args.ingest == "smart":
            try:
                shutil.copy2(path, inbox_path)
            except Exception as exc:
                sample_result["status"] = "fail"
                sample_result["error"] = f"copy_failed: {exc}"
                failed += 1
                report["samples"].append(sample_result)
                continue
            file_hash = sha256_file(inbox_path)
        else:
            file_hash = sha256_file(path)
        pre_count, pre_count_msg = get_qdrant_count(args.qdrant_url, args.qdrant_collection, qdrant_headers)

        ingest_output = ""
        ingest_failed = False
        ingest_timeout = max(60, args.timeout_min * 60)
        if args.ingest == "smart":
            env = os.environ.copy()
            env["CONDUCTOR_INBOX"] = str(inbox)
            env["CONDUCTOR_ARCHIVE"] = str(archive_root)
            env["CONDUCTOR_QUARANTINE"] = str(quarantine_root)
            env["CONDUCTOR_ROOT"] = str(conductor_root)
            cmd = [sys.executable, str(REPO_ROOT / "scripts" / "smart_ingest.py"), "--once"]
            code, ingest_output = run_subprocess(cmd, env, timeout_sec=ingest_timeout)
            if code != 0:
                sample_result["error"] = f"smart_ingest_failed: exit={code}"
                ingest_failed = True
        else:
            temp_dir = artifacts_dir / "indexer_input" / run_id
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = temp_dir / ingest_name
            shutil.copy2(path, temp_file)
            env = os.environ.copy()
            cmd = [sys.executable, str(REPO_ROOT / "scripts" / "file_indexer.py"), "--path", str(temp_dir), "--limit", "1"]
            code, ingest_output = run_subprocess(cmd, env, timeout_sec=ingest_timeout)
            if code != 0:
                sample_result["error"] = f"file_indexer_failed: exit={code}"
                ingest_failed = True

        if ingest_failed:
            sample_result["status"] = "fail"
            sample_result["ingestion"]["ended_at"] = dt.datetime.utcnow().isoformat() + "Z"
            if ingest_output:
                sample_result["ingestion"]["output_tail"] = ingest_output
            sample_result["duration_sec"] = round(time.time() - sample_start, 2)
            report["samples"].append(sample_result)
            failed += 1
            continue

        # Poll for completion
        deadline = time.time() + args.timeout_min * 60
        move_ok = False
        ledger_ok = False
        qdrant_ok = False
        search_ok = False
        search_eval = {"status": "fail", "level": "fail", "matched_on": "none", "details": "not_checked"}
        ledger_details = "not_checked"
        move_details = "not_checked"
        qdrant_details = f"pre_count={pre_count} ({pre_count_msg})"

        ledger_row = None

        while time.time() < deadline:
            # Ledger check
            if args.ingest == "smart":
                if ledger_path.exists():
                    try:
                        conn = sqlite3.connect(ledger_path)
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT sha256, original_filename, current_filename, current_path, status "
                            "FROM files WHERE sha256 = ? OR original_filename = ? "
                            "ORDER BY updated_at DESC LIMIT 1",
                            (file_hash, ingest_name),
                        )
                        row = cur.fetchone()
                        conn.close()
                        if row:
                            ledger_row = {
                                "sha256": row[0],
                                "original_filename": row[1],
                                "current_filename": row[2],
                                "current_path": row[3],
                                "status": row[4],
                            }
                            ledger_ok = row[4] in {"indexed", "quarantined"}
                            ledger_details = f"status={row[4]} current_path={row[3]}"
                        else:
                            ledger_details = "no_entry"
                    except Exception as exc:
                        ledger_details = f"ledger_error: {exc}"
                else:
                    ledger_details = "ledger_missing"

                # Move/Quarantine check
                if not inbox_path.exists() and ledger_row and ledger_row.get("current_path"):
                    current_path = Path(ledger_row["current_path"])
                    if current_path.exists() and (
                        path_is_under(current_path, archive_root) or path_is_under(current_path, quarantine_root)
                    ):
                        move_ok = True
                        move_details = f"moved_to={current_path}"
                    else:
                        move_details = "current_path_missing_or_outside_roots"
                else:
                    move_details = "inbox_still_present_or_ledger_missing"
            else:
                ledger_details = "skipped:indexer"
                move_details = "skipped:indexer"

            # Qdrant evidence
            found, found_msg = qdrant_find_by_filename(
                args.qdrant_url, args.qdrant_collection, qdrant_headers, ingest_name
            )
            if found:
                qdrant_ok = True
                qdrant_details = f"found_by_filename: {found_msg}"
            else:
                post_count, post_msg = get_qdrant_count(args.qdrant_url, args.qdrant_collection, qdrant_headers)
                if pre_count is not None and post_count is not None and post_count >= pre_count + 1:
                    qdrant_ok = True
                    qdrant_details = f"count_increase pre={pre_count} post={post_count}"
                else:
                    qdrant_details = f"not_found pre={pre_count} post={post_count} ({post_msg})"

            completion_ok = False
            if args.ingest == "smart":
                completion_ok = sum([move_ok, ledger_ok, qdrant_ok]) >= 2
            else:
                completion_ok = qdrant_ok

            ledger_current_path = ledger_row.get("current_path") if ledger_row else None
            current_filename = ledger_row.get("current_filename") if ledger_row else None

            search_eval = evaluate_search_api(
                args.search_url,
                token,
                args.search_limit,
                ledger_current_path,
                current_filename,
            )
            search_ok = search_eval["status"] == "pass"

            if not search_ok and completion_ok:
                fallback = qdrant_retrieval_fallback(
                    args.qdrant_url,
                    args.qdrant_collection,
                    qdrant_headers,
                    ledger_current_path,
                    file_hash,
                    ingest_name,
                    token,
                )
                if fallback["status"] == "pass":
                    search_ok = True
                    search_eval = {
                        "status": "pass",
                        "level": "weak",
                        "matched_on": f"qdrant_fallback:{fallback['matched_on']}",
                        "details": fallback["details"],
                    }

            if args.ingest == "smart":
                if completion_ok and search_ok:
                    break
            else:
                if completion_ok and search_ok:
                    break

            time.sleep(args.poll_sec)

        sample_result["checks"]["moved_or_quarantined"] = {"status": "pass" if move_ok else "fail", "details": move_details}
        sample_result["checks"]["ledger_entry"] = {"status": "pass" if ledger_ok else "fail", "details": ledger_details}
        sample_result["checks"]["qdrant_evidence"] = {"status": "pass" if qdrant_ok else "fail", "details": qdrant_details}
        sample_result["checks"]["search_retrieval"] = {
            "status": "pass" if search_ok else "fail",
            "level": search_eval.get("level", "fail"),
            "matched_on": search_eval.get("matched_on", "none"),
            "details": search_eval.get("details", "unknown"),
        }

        if args.ingest == "smart":
            completion_ok = sum([move_ok, ledger_ok, qdrant_ok]) >= 2
        else:
            completion_ok = qdrant_ok

        if completion_ok and search_ok:
            sample_result["status"] = "pass"
            passed += 1
        else:
            sample_result["status"] = "fail"
            failed += 1

        sample_result["ingestion"]["ended_at"] = dt.datetime.utcnow().isoformat() + "Z"
        sample_result["duration_sec"] = round(time.time() - sample_start, 2)
        if ingest_output:
            sample_result["ingestion"]["output_tail"] = ingest_output
        report["samples"].append(sample_result)

        if args.ingest == "smart" and not args.keep_inbox and inbox_path.exists():
            try:
                inbox_path.unlink()
            except Exception:
                pass

    report["summary"] = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
    }

    json_path = artifacts_dir / "e2e_formats_report.json"
    md_path = artifacts_dir / "e2e_formats_report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md_lines = [
        "# E2E Format Harness Report",
        "",
        f"- Run ID: {report['run_id']}",
        f"- Timestamp: {report['timestamp']}",
        f"- Mode: {report['mode']}",
        f"- Ingest: {report['ingest_method']}",
        f"- Samples: {total} total, {passed} passed, {failed} failed, {skipped} skipped",
        "",
        "## Failures",
    ]
    failures = [s for s in report["samples"] if s["status"] == "fail"]
    if failures:
        for s in failures:
            md_lines.append(f"- {s['id']}: {s.get('error') or 'checks_failed'}")
    else:
        md_lines.append("- None")

    md_lines.append("")
    md_lines.append("## Skipped")
    skips = [s for s in report["samples"] if s["status"] == "skipped"]
    if skips:
        for s in skips:
            md_lines.append(f"- {s['id']}: {s.get('error') or 'skipped'}")
    else:
        md_lines.append("- None")

    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
