"""
Special Parser Core
===================

Modulare Parser für Spezialformate:
- 3D: Trimesh / Assimp
- CAD: OpenCascade / ODA (Fallback: STEP/IGES Textanalyse)
- GIS: GDAL (Fallback: GeoJSON Parser)
- Fonts: fontTools (Fallback: Headeranalyse)
"""

import importlib
import importlib.util
import json
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SpecialParseResult:
    filepath: str
    filename: str
    extension: str
    category: str
    parser: str
    success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    preview: str = ""
    derived_text: str = ""
    confidence: float = 0.0
    error: str = ""
    processing_time_ms: int = 0


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _load_module(name: str):
    return importlib.import_module(name)


class BaseParser:
    name: str = "base"
    category: str = "unknown"
    extensions: List[str] = []

    def can_handle(self, extension: str, category: Optional[str]) -> bool:
        if category and category != self.category:
            return False
        return extension in self.extensions

    def parse(self, path: Path) -> SpecialParseResult:
        raise NotImplementedError


class ThreeDParser(BaseParser):
    name = "trimesh/assimp"
    category = "3d"
    extensions = [".obj", ".stl", ".ply", ".glb", ".gltf", ".fbx"]

    def parse(self, path: Path) -> SpecialParseResult:
        start = time.time()
        result = SpecialParseResult(
            filepath=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
            category=self.category,
            parser=self.name,
        )

        metadata = {}
        try:
            if _module_available("trimesh"):
                trimesh = _load_module("trimesh")
                mesh = trimesh.load(path, force="mesh")
                metadata["vertex_count"] = int(len(mesh.vertices))
                metadata["face_count"] = int(len(mesh.faces))
                metadata["bounds"] = [
                    mesh.bounds[0].tolist(),
                    mesh.bounds[1].tolist(),
                ]
                result.success = True
                result.confidence = 0.9
            elif _module_available("pyassimp"):
                pyassimp = _load_module("pyassimp")
                scene = pyassimp.load(str(path))
                mesh_count = len(scene.meshes)
                vertex_count = sum(len(mesh.vertices) for mesh in scene.meshes)
                face_count = sum(len(mesh.faces) for mesh in scene.meshes)
                metadata.update(
                    {
                        "mesh_count": mesh_count,
                        "vertex_count": vertex_count,
                        "face_count": face_count,
                    }
                )
                pyassimp.release(scene)
                result.success = True
                result.confidence = 0.8
            else:
                metadata.update(self._fallback_obj_parse(path))
                result.success = True
                result.confidence = 0.6
        except Exception as exc:
            metadata.update(self._fallback_obj_parse(path))
            result.success = True if metadata else False
            result.confidence = 0.4
            result.error = str(exc)

        result.metadata = metadata
        result.preview = (
            f"3D Preview: {metadata.get('vertex_count', 0)} vertices, "
            f"{metadata.get('face_count', 0)} faces"
        )
        result.derived_text = (
            f"3D Model {path.name} with {metadata.get('vertex_count', 0)} vertices and "
            f"{metadata.get('face_count', 0)} faces."
        )
        result.processing_time_ms = int((time.time() - start) * 1000)
        return result

    def _fallback_obj_parse(self, path: Path) -> Dict[str, Any]:
        if path.suffix.lower() not in {".obj", ".stl", ".ply"}:
            return {
                "vertex_count": 0,
                "face_count": 0,
                "format": path.suffix.lower().lstrip("."),
            }
        vertex_count = 0
        face_count = 0
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    if line.startswith("v "):
                        vertex_count += 1
                    elif line.startswith("f "):
                        face_count += 1
        except Exception:
            pass
        return {
            "vertex_count": vertex_count,
            "face_count": face_count,
            "format": path.suffix.lower().lstrip("."),
        }


class CadParser(BaseParser):
    name = "opencascade/oda"
    category = "cad"
    extensions = [".step", ".stp", ".iges", ".igs"]

    def parse(self, path: Path) -> SpecialParseResult:
        start = time.time()
        result = SpecialParseResult(
            filepath=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
            category=self.category,
            parser=self.name,
        )

        metadata = {}
        try:
            if _module_available("OCP") and _module_available("OCP.STEPControl"):
                step_module = _load_module("OCP.STEPControl")
                reader = step_module.STEPControl_Reader()
                status = reader.ReadFile(str(path))
                metadata["read_status"] = int(status)
                metadata["transfer_roots"] = int(reader.TransferRoots())
                result.success = status == 1
                result.confidence = 0.8 if result.success else 0.4
            else:
                metadata.update(self._fallback_step_parse(path))
                result.success = True
                result.confidence = 0.6
        except Exception as exc:
            metadata.update(self._fallback_step_parse(path))
            result.success = True if metadata else False
            result.confidence = 0.4
            result.error = str(exc)

        result.metadata = metadata
        schema = metadata.get("schema", "unknown")
        result.preview = f"CAD Preview: schema={schema}"
        result.derived_text = f"CAD asset {path.name} uses schema {schema}."
        result.processing_time_ms = int((time.time() - start) * 1000)
        return result

    def _fallback_step_parse(self, path: Path) -> Dict[str, Any]:
        schema = "unknown"
        product = ""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read(10000)
            if "FILE_SCHEMA" in content:
                start = content.find("FILE_SCHEMA")
                snippet = content[start:start + 200]
                schema = snippet.split("(")[-1].split(")")[0].replace("'", "").strip()
            if "PRODUCT" in content:
                product = "PRODUCT"
        except Exception:
            pass
        return {
            "schema": schema,
            "product_block": product,
            "format": path.suffix.lower().lstrip("."),
        }


class GisParser(BaseParser):
    name = "gdal"
    category = "gis"
    extensions = [".geojson", ".json", ".shp", ".kml", ".gpx"]

    def parse(self, path: Path) -> SpecialParseResult:
        start = time.time()
        result = SpecialParseResult(
            filepath=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
            category=self.category,
            parser=self.name,
        )

        metadata = {}
        try:
            if _module_available("osgeo.gdal"):
                gdal = _load_module("osgeo.gdal")
                dataset = gdal.OpenEx(str(path))
                if dataset:
                    metadata["layer_count"] = dataset.GetLayerCount()
                    result.success = True
                    result.confidence = 0.8
                else:
                    result.success = False
                    result.confidence = 0.2
            else:
                metadata.update(self._fallback_geojson_parse(path))
                result.success = True
                result.confidence = 0.6
        except Exception as exc:
            metadata.update(self._fallback_geojson_parse(path))
            result.success = True if metadata else False
            result.confidence = 0.4
            result.error = str(exc)

        result.metadata = metadata
        result.preview = f"GIS Preview: {metadata.get('feature_count', 0)} features"
        result.derived_text = (
            f"GIS dataset {path.name} with {metadata.get('feature_count', 0)} features."
        )
        result.processing_time_ms = int((time.time() - start) * 1000)
        return result

    def _fallback_geojson_parse(self, path: Path) -> Dict[str, Any]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "feature_count": 0,
                "geometry_types": [],
                "format": path.suffix.lower().lstrip("."),
            }

        features = data.get("features", []) if isinstance(data, dict) else []
        geometry_types = {
            feature.get("geometry", {}).get("type")
            for feature in features
            if isinstance(feature, dict)
        }
        geometry_types.discard(None)

        return {
            "feature_count": len(features),
            "geometry_types": sorted(geometry_types),
            "format": "geojson",
        }


class FontParser(BaseParser):
    name = "fonttools"
    category = "fonts"
    extensions = [".ttf", ".otf", ".woff", ".woff2"]

    def parse(self, path: Path) -> SpecialParseResult:
        start = time.time()
        result = SpecialParseResult(
            filepath=str(path),
            filename=path.name,
            extension=path.suffix.lower(),
            category=self.category,
            parser=self.name,
        )

        metadata = {}
        try:
            if _module_available("fontTools.ttLib"):
                ttlib = _load_module("fontTools.ttLib")
                font = ttlib.TTFont(str(path), lazy=True)
                name_table = font["name"]
                family = name_table.getDebugName(1) if name_table else None
                subfamily = name_table.getDebugName(2) if name_table else None
                metadata.update(
                    {
                        "family": family or "unknown",
                        "subfamily": subfamily or "unknown",
                        "glyph_count": len(font.getGlyphOrder()),
                        "format": path.suffix.lower().lstrip("."),
                    }
                )
                font.close()
                result.success = True
                result.confidence = 0.9
            else:
                metadata.update(self._fallback_font_header(path))
                result.success = True
                result.confidence = 0.6
        except Exception as exc:
            metadata.update(self._fallback_font_header(path))
            result.success = True if metadata else False
            result.confidence = 0.4
            result.error = str(exc)

        result.metadata = metadata
        result.preview = (
            f"Font Preview: {metadata.get('family', 'unknown')} "
            f"{metadata.get('subfamily', '')}"
        ).strip()
        result.derived_text = (
            f"Font file {path.name} ({metadata.get('format', 'unknown')}) with "
            f"{metadata.get('glyph_count', 0)} glyphs."
        )
        result.processing_time_ms = int((time.time() - start) * 1000)
        return result

    def _fallback_font_header(self, path: Path) -> Dict[str, Any]:
        header = path.read_bytes()[:4]
        format_map = {
            b"wOFF": "woff",
            b"wOF2": "woff2",
            b"\x00\x01\x00\x00": "ttf",
            b"OTTO": "otf",
        }
        return {
            "format": format_map.get(header, "unknown"),
            "glyph_count": 0,
            "family": "unknown",
            "subfamily": "unknown",
        }


PARSERS: List[BaseParser] = [ThreeDParser(), CadParser(), GisParser(), FontParser()]


def parse_file(path: Path, category: Optional[str] = None) -> SpecialParseResult:
    extension = path.suffix.lower()
    for parser in PARSERS:
        if parser.can_handle(extension, category):
            return parser.parse(path)
    raise ValueError(f"Unsupported extension: {extension}")


__all__ = [
    "SpecialParseResult",
    "PARSERS",
    "parse_file",
    "asdict",
]
