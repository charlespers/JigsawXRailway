"""
KiCad design parsing + mapping helpers.
"""

from __future__ import annotations

import io
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

from components.component_registry import ComponentRegistry

_COMPONENT_CACHE: Dict[str, Any] | None = None


def load_component_library() -> Dict[str, Any]:
    """Load component definitions from local JSON."""
    global _COMPONENT_CACHE
    if _COMPONENT_CACHE is None:
        data_path = Path(__file__).resolve().parent.parent / "data" / "component_library.json"
        with data_path.open("r", encoding="utf-8") as f:
            _COMPONENT_CACHE = json.load(f)
    return _COMPONENT_CACHE


def parse_uploaded_design(uploaded_file) -> Dict[str, Any]:
    """Parse uploaded KiCad/JSON design file."""
    filename = uploaded_file.name.lower()
    raw_bytes = uploaded_file.read()
    if filename.endswith(".json"):
        design = json.loads(raw_bytes.decode("utf-8"))
    elif filename.endswith(".kicad_pcb"):
        design = _parse_kicad_pcb(raw_bytes.decode("utf-8", errors="ignore"))
    else:
        raise ValueError("Unsupported file type. Upload .kicad_pcb or .json")

    fingerprint = _fingerprint_design(design)
    design.setdefault("metadata", {})
    design["metadata"].update({
        "filename": uploaded_file.name,
        "fingerprint": fingerprint,
        "component_count": len(design.get("components", [])),
        "net_count": len(design.get("nets", []))
    })
    return design


def get_design_summary(design: Dict[str, Any]) -> Dict[str, Any]:
    comps = design.get("components", [])
    nets = design.get("nets", [])
    type_counts: Dict[str, int] = {}
    for comp in comps:
        key = comp.get("type") or comp.get("value") or "Unknown"
        type_counts[key] = type_counts.get(key, 0) + 1
    return {
        "components": len(comps),
        "nets": len(nets),
        "types": type_counts,
        "filename": design.get("metadata", {}).get("filename")
    }


def import_design_into_registry(design: Dict[str, Any], registry: ComponentRegistry) -> None:
    """Populate registry with parsed design."""
    registry.clear()
    library = load_component_library()
    profiles = {c["name"]: _match_profile(c, library) for c in design.get("components", [])}

    for comp in design.get("components", []):
        profile = profiles.get(comp["name"], {})
        comp_payload = {
            "name": comp["name"],
            "type": profile.get("type", comp.get("type", "generic")),
            "description": comp.get("value") or profile.get("description", "KiCad component"),
            "inputs": profile.get("inputs", comp.get("inputs", [])) or ["IN"],
            "outputs": profile.get("outputs", comp.get("outputs", [])),
            "position": comp.get("position"),
            "metadata": {
                "value": comp.get("value"),
                "footprint": comp.get("footprint"),
                "pins": comp.get("pins", [])
            }
        }
        registry.add_component(comp_payload["name"], comp_payload)

    # Build connections based on nets
    for net in design.get("nets", []):
        connections = net.get("connections", [])
        if len(connections) < 2:
            continue
        driver, receivers = _select_driver(connections, profiles)
        if not driver:
            continue
        for dest in receivers:
            registry.add_connection(
                driver["component"],
                driver.get("pin", driver.get("output", "OUT")),
                dest["component"],
                dest.get("pin", dest.get("input", "IN"))
            )


def _select_driver(connections: List[Dict[str, Any]], profiles: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Any] | None, List[Dict[str, Any]]]:
    driver = None
    receivers: List[Dict[str, Any]] = []
    for conn in connections:
        profile = profiles.get(conn.get("component"), {})
        outputs = profile.get("outputs", [])
        inputs = profile.get("inputs", [])
        pin_name = conn.get("pin")
        if pin_name in outputs and driver is None:
            driver = conn
        else:
            if pin_name not in inputs and driver is None:
                driver = conn
            else:
                receivers.append(conn)
    if driver is None and receivers:
        driver = receivers.pop(0)
    return driver, receivers


def _match_profile(component: Dict[str, Any], library: Dict[str, Any]) -> Dict[str, Any]:
    value = (component.get("value") or "").lower()
    footprint = (component.get("footprint") or "").lower()
    for profile in library.get("components", []):
        fp_matches = any(f.lower() in footprint for f in profile.get("footprints", []))
        val_matches = profile["type"] in value or profile["name"].lower() in value
        if fp_matches or val_matches:
            return profile
    # heuristics
    if value.startswith("r") or "res" in value:
        return next((p for p in library["components"] if p["type"] == "resistor"), {})
    if value.startswith("led"):
        return next((p for p in library["components"] if p["type"] == "led"), {})
    if "mcu" in value or "esp" in value:
        return next((p for p in library["components"] if p["type"] == "mcu"), {})
    return {}


def _parse_kicad_pcb(content: str) -> Dict[str, Any]:
    nets = _parse_nets(content)
    modules = _parse_modules(content)
    components = []
    net_connections: Dict[str, List[Dict[str, Any]]] = {name: [] for name in nets.values()}

    for module in modules:
        comp = _parse_module(module, nets)
        components.append(comp)
        for pin in comp.get("pins", []):
            if pin.get("net") in net_connections:
                net_connections[pin["net"]].append({
                    "component": comp["name"],
                    "pin": pin.get("pin"),
                    "net": pin.get("net")
                })

    nets_payload = [
        {
            "name": name,
            "connections": net_connections[name]
        }
        for name in net_connections if net_connections[name]
    ]
    return {"components": components, "nets": nets_payload}


def _parse_nets(content: str) -> Dict[str, str]:
    pattern = re.compile(r"\(net\s+(\d+)\s+\"([^\"]+)\"\)")
    return {match.group(1): match.group(2) for match in pattern.finditer(content)}


def _parse_modules(content: str) -> List[str]:
    return _extract_sections(content, ["module", "footprint"])


def _extract_sections(content: str, keywords: List[str]) -> List[str]:
    sections = []
    i = 0
    length = len(content)
    while i < length:
        if content[i] == '(':
            for keyword in keywords:
                if content.startswith(keyword, i + 1):
                    start = i
                    depth = 0
                    while i < length:
                        if content[i] == '(':
                            depth += 1
                        elif content[i] == ')':
                            depth -= 1
                            if depth == 0:
                                i += 1
                                sections.append(content[start:i])
                                break
                        i += 1
                    break
            else:
                i += 1
        else:
            i += 1
    return sections


def _parse_module(section: str, nets: Dict[str, str]) -> Dict[str, Any]:
    ref = _match_regex(section, r"\(fp_text\s+reference\s+([^\s\)]+)") or "U?"
    value = _match_regex(section, r"\(fp_text\s+value\s+([^\s\)]+)") or "COMPONENT"
    footprint = _match_regex(section, r"\((?:module|footprint)\s+([^\s\)]+)") or ""
    pos_match = re.search(r"\(at\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)", section)
    position = None
    if pos_match:
        position = {"x": float(pos_match.group(1)), "y": float(pos_match.group(2))}
    pins = []
    pad_pattern = re.compile(r"\(pad\s+([^\s\)]+).*?\(net\s+(\d+)\s+\"([^\"]+)\"\)", re.DOTALL)
    for pad_name, net_id, net_name in pad_pattern.findall(section):
        pins.append({"pin": pad_name, "net": nets.get(net_id, net_name)})
    return {
        "name": ref,
        "value": value,
        "footprint": footprint,
        "position": position,
        "pins": pins
    }


def _match_regex(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _fingerprint_design(design: Dict[str, Any]) -> str:
    payload = json.dumps({
        "components": sorted([c.get("name", "") for c in design.get("components", [])]),
        "nets": sorted([n.get("name", "") for n in design.get("nets", [])])
    }, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
