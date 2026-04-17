# mdita-yaml-keys

A DITA-OT preprocessing plugin that enables key definitions for variable text in MDITA maps using YAML front matter.

## Overview

MDITA (the Markdown authoring format of Lightweight DITA) has no native syntax for declaring key definitions in a map. The LwDITA specification requires authors to embed raw HDITA snippets (`<div data-class="keydef">`) inside otherwise clean Markdown files — a significant friction point for non-technical authors.

This plugin addresses the most common real-world use case: **variable text keys** (product names, version numbers, brand terms). It lets authors declare keys in a map's YAML front matter using plain key-value pairs, and injects the equivalent XDITA `<keydef>` elements into the DITA-OT preprocessing pipeline before key resolution occurs.

This is a **non-normative extension** to the LwDITA specification. It does not modify or conflict with the OASIS LwDITA standard.

---

## Authoring syntax

### The MDITA map

Add a `keys` block to the YAML front matter of any MDITA map file (`.md`). Each entry is a key name paired with its variable text value as a plain string.

```markdown
---
id: garden-guide-map
keys:
  product-name: "Acme Greenhouse"
  product-version: "3.2"
  company-name: "Remote Lighting Inc."
---

# Planting a Winter Garden

- [About winter gardening](winter-gardening-concept.dita)
- [Selecting your plants](selecting-plants.md)
```

**Rules:**

- Key names must be valid DITA key names: start with a letter or underscore, contain only letters, digits, hyphens, underscores, and periods.
- Values must be plain strings. Nested YAML objects are not supported in this version.
- The `keys` block may contain any number of entries.
- All other YAML front matter fields (`id`, `author`, etc.) are unaffected.

### Using key references in MDITA topics

MDITA topic files consume variable text keys using the HDITA snippet syntax, which is the mechanism specified by the LwDITA standard for the MDITA extended profile.

```markdown
---
id: selecting-plants
---

# Selecting Your Plants

Welcome to <span data-keyref="product-name">product name</span> version
<span data-keyref="product-version">product version</span>.
```

**Fallback text:** The text content inside each `<span>` renders if the key cannot be resolved. Always provide meaningful fallback text.

### Using key references in full DITA topics

```xml
<p>Version <ph keyref="product-version"/> of
<ph keyref="product-name"/> introduces a new climate zone calculator.</p>
```

---

## How it works

The plugin operates as a DITA-OT **preprocessing plugin**, running before the OT's key resolution stage via the `depend.preprocess.pre` extension point.

### Processing pipeline

```
garden-guide.md (MDITA map with YAML keys block)
        │
        ▼
[mdita-yaml-keys preprocessor — python/mdita_yaml_keys.py]
        │  1. Parse YAML front matter
        │  2. Extract `keys` block
        │  3. Generate in-memory XDITA <keydef> elements
        │  4. Inject into temp map file before key resolution
        ▼
[DITA-OT key resolution]
        │  Keys now available to all topics in map scope
        ▼
[Standard DITA-OT output pipeline]
```

### Generated XDITA (injected into temp map, not written to source)

```xml
<keydef keys="product-name">
  <topicmeta>
    <keytext>Acme Greenhouse</keytext>
  </topicmeta>
</keydef>
<keydef keys="product-version">
  <topicmeta>
    <keytext>3.2</keytext>
  </topicmeta>
</keydef>
```

---

## Cross-format compliance

| Topic format | Keyref syntax | Resolved by |
|---|---|---|
| MDITA | `<span data-keyref="key-name">fallback</span>` | DITA-OT HDITA processing |
| HDITA | `<span data-keyref="key-name">fallback</span>` | DITA-OT HDITA processing |
| XDITA | `<ph keyref="key-name"/>` | DITA-OT XDITA processing |
| Full DITA | `<ph keyref="key-name"/>` | DITA-OT standard key resolution |

---

## Installation

```bash
dita install https://github.com/VT-Evia/mdita-yaml-keys/archive/main.zip
```

Or clone and install locally:

```bash
git clone https://github.com/VT-Evia/mdita-yaml-keys.git
dita install /path/to/mdita-yaml-keys
```

Requires DITA-OT 4.x or later and Python 3.8+.

---

## Usage

```bash
dita --input=samples/garden-guide.md --format=html5 --output=out/
```

No additional flags are needed. The plugin activates automatically when it detects a `keys` block in the YAML front matter of the input map.

---

## Limitations

This plugin handles **variable text keys only**. It does not support:

- `href`-based keydefs for indirect addressing (use HDITA snippets for these)
- Keys with `scope`, `format`, or `processing-role` overrides
- Cascading key precedence across map-of-maps
- Keyref in MDITA topic titles

---

## Relationship to the LwDITA specification

This plugin is a non-normative, practical extension. Maps with a `keys` block processed without this plugin ignore the front matter field silently — fallback text renders instead. This ensures graceful degradation.

---

## License

Apache 2.0. See `LICENSE` for details.
