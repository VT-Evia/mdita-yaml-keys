# mdita-yaml-keys

Preprocessing plugin for DITA-OT that reads `keys` blocks from MDITA map YAML front matter and injects XDITA `<keydef>` elements into the preprocessed map before key resolution.

Plugin ID: `com.vt-evia.mdita-yaml-keys`

## Tech stack

- Python 3.8+ (`pyyaml`, `xml.etree.ElementTree`, `pathlib`, `argparse`)
- Apache ANT (DITA-OT build pipeline integration)
- DITA-OT 4.x

## Key files

| File | Purpose |
|---|---|
| `plugin.xml` | Plugin manifest — declares ID, dependency on `org.dita.base`, and registers the ANT extension point `depend.preprocess.pre` |
| `build.xml` | ANT target `mdita-yaml-keys.preprocess` — calls Python script with `--input` and `--tempdir` arguments |
| `python/mdita_yaml_keys.py` | Core logic: parse YAML front matter, generate `<keydef>` elements, inject into temp map XML |
| `samples/` | Three sample files demonstrating the authoring workflow (MDITA map, MDITA topic, DITA concept) |
| `.github/workflows/test-build.yml` | CI workflow: installs DITA-OT 4.x, installs plugin, runs test build against `samples/garden-guide.md` |

## Local installation

```bash
dita install /path/to/mdita-yaml-keys
```

Verify the plugin is registered:

```bash
dita plugins
```

## Running a test build

```bash
dita --input=samples/garden-guide.md --format=html5 --output=out/
```

Output lands in `out/`. Inspect `out/garden-guide.html` to confirm key values resolve (e.g., "Acme Greenhouse" instead of fallback text).

## Constraints to observe

- This plugin handles **variable text keys only** — plain string values in the `keys` YAML block. It does not generate `href`-based keydefs for indirect addressing.
- All key names must match `^[a-zA-Z_][a-zA-Z0-9\-_.]*$` (the DITA key name rule). Invalid names are warned and skipped; the build does not fail.
- Never build XML by string concatenation in `mdita_yaml_keys.py`. Use `xml.etree.ElementTree` throughout.
- All log output from the Python script is prefixed with `[mdita-yaml-keys]` for easy filtering in OT build logs.
- The plugin injects into the DITA-OT **temp** copy of the map, never the source file.

## Non-normative note

This is a practical extension outside the OASIS LwDITA specification. Maps processed without this plugin work correctly — the `keys` front matter field is ignored and fallback text renders.
