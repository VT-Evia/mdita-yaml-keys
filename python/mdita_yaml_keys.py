"""
mdita_yaml_keys.py — DITA-OT preprocessing script for mdita-yaml-keys plugin.

Reads the `keys` block from the YAML front matter of an MDITA map file and
injects equivalent XDITA <keydef> elements into the preprocessed map XML in
the DITA-OT temp directory, before the OT's key resolution stage.

Dependency: pyyaml (pip install pyyaml)
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

import yaml

LOG_PREFIX = "[mdita-yaml-keys]"
KEY_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9\-_.]*$")


def log(message: str) -> None:
    print(f"{LOG_PREFIX} {message}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inject YAML front-matter keys into DITA-OT temp map."
    )
    parser.add_argument("--input", required=True, help="Path to the original MDITA map file")
    parser.add_argument("--tempdir", required=True, help="Path to the DITA-OT temp directory")
    return parser.parse_args()


def extract_front_matter(md_path: Path) -> Optional[dict]:
    """Return parsed YAML front matter from an MDITA file, or None if absent."""
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError as exc:
        log(f"Could not read input file {md_path}: {exc}")
        return None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    end_index = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = i
            break

    if end_index is None:
        return None

    front_matter_text = "\n".join(lines[1:end_index])
    try:
        return yaml.safe_load(front_matter_text) or {}
    except yaml.YAMLError as exc:
        log(f"Failed to parse YAML front matter: {exc}")
        return None


def build_keydef_element(key_name: str, key_value: str) -> ET.Element:
    """Return an XDITA <keydef> Element for a single key-value pair."""
    keydef = ET.Element("keydef", attrib={"keys": key_name})
    topicmeta = ET.SubElement(keydef, "topicmeta")
    keytext = ET.SubElement(topicmeta, "keytext")
    keytext.text = key_value
    return keydef


def find_temp_map(tempdir: Path, stem: str) -> Optional[Path]:
    """Locate the preprocessed XML copy of the map in the DITA-OT temp directory."""
    candidates = [p for p in tempdir.rglob("*.xml") if p.stem == stem]
    if not candidates:
        return None
    return candidates[0]


def inject_keydefs(temp_map_path: Path, keydefs: list[ET.Element]) -> bool:
    """Insert <keydef> elements as the first children of <map> in the temp map XML."""
    try:
        tree = ET.parse(temp_map_path)
    except ET.ParseError as exc:
        log(f"Failed to parse temp map XML {temp_map_path}: {exc}")
        return False

    root = tree.getroot()

    # Strip namespace for comparison so we match both bare and namespaced <map>
    local_tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    if local_tag != "map":
        log(f"Root element is <{local_tag}>, expected <map>. Skipping injection.")
        return False

    # Insert keydefs before any existing children (topicrefs, etc.)
    for index, keydef in enumerate(keydefs):
        root.insert(index, keydef)

    try:
        ET.indent(tree, space="  ")
        tree.write(
            temp_map_path,
            encoding="unicode",
            xml_declaration=True,
        )
    except OSError as exc:
        log(f"Failed to write modified temp map {temp_map_path}: {exc}")
        return False

    return True


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    tempdir = Path(args.tempdir)

    front_matter = extract_front_matter(input_path)
    if front_matter is None:
        log("No YAML front matter found in input file. Skipping.")
        sys.exit(0)

    raw_keys = front_matter.get("keys")
    if not raw_keys:
        log("No keys block found in front matter. Skipping.")
        sys.exit(0)

    if not isinstance(raw_keys, dict):
        log("keys block is not a YAML mapping. Skipping.")
        sys.exit(0)

    keydef_elements: list[ET.Element] = []
    for key_name, key_value in raw_keys.items():
        key_name_str = str(key_name)
        if not KEY_NAME_RE.match(key_name_str):
            log(f"WARNING: '{key_name_str}' is not a valid DITA key name. Skipping.")
            continue
        if not isinstance(key_value, str):
            log(f"WARNING: value for key '{key_name_str}' is not a plain string. Skipping.")
            continue
        keydef_elements.append(build_keydef_element(key_name_str, key_value))

    if not keydef_elements:
        log("No valid key definitions found. Skipping.")
        sys.exit(0)

    stem = input_path.stem
    temp_map_path = find_temp_map(tempdir, stem)
    if temp_map_path is None:
        log(
            f"WARNING: Could not find preprocessed map '{stem}.xml' in temp dir {tempdir}. "
            "Skipping — DITA-OT may not have copied the map yet."
        )
        sys.exit(0)

    success = inject_keydefs(temp_map_path, keydef_elements)
    if success:
        log(
            f"Injected {len(keydef_elements)} key definition(s) into {temp_map_path.name}"
        )


if __name__ == "__main__":
    main()
