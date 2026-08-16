#!/usr/bin/env python3
"""Structural validation for authority packs — the CI gate for pack PRs.

Standalone (stdlib + PyYAML): mirrors the *structural* rules of the canonical
OpenContracts preflight (`manage.py load_authority_pack --check` /
`AuthorityPackService.preflight_path`) without needing the Django stack, so a
pack PR gets fast, dependency-light feedback. The canonical preflight remains
authoritative — run it (or `manage.py install_authority_pack <pack> --check`)
before shipping a pack to a deployment. Rules here should track
`opencontractserver/enrichment/services/authority_pack_service.py`; when the
two disagree, the OpenContracts validator wins and this script has a bug.

Usage:
    python scripts/validate_pack.py --all          # validate every pack dir
    python scripts/validate_pack.py fort_worth     # validate one pack
    python scripts/validate_pack.py --self-test    # prove the checks can fail

Exit code 0 = all packs valid; 1 = findings (printed per pack).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Mirrors opencontractserver/enrichment/constants.py::ALL_AUTHORITY_TYPES.
ALL_AUTHORITY_TYPES = {
    "statute",
    "regulation",
    "admin-rule",
    "municipal-ordinance",
    "case",
    "constitution",
    "court-rule",
    "guidance",
    "treaty",
}

# Mirrors opencontractserver/enrichment/data/mappings.py key grammar.
PREFIX_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CANONICAL_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:.+$")
PACK_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class PackFindings:
    def __init__(self, pack_dir: Path):
        self.pack_dir = pack_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _pack_file(f: PackFindings, rel: str, label: str) -> Path | None:
    """Resolve a manifest-referenced path, refusing escapes from the pack dir."""
    candidate = (f.pack_dir / rel).resolve()
    if not str(candidate).startswith(str(f.pack_dir.resolve()) + "/"):
        f.error(f"{label} path escapes the pack directory: {rel}")
        return None
    if not candidate.is_file():
        f.error(f"{label} file missing: {rel}")
        return None
    return candidate


def _load_yaml(f: PackFindings, path: Path, label: str):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        f.error(f"{label} is not valid YAML: {e}")
        return None


def _validate_mappings(f: PackFindings, path: Path) -> set[str]:
    """Validate the mappings YAML; return the declared prefixes."""
    data = _load_yaml(f, path, "mappings")
    if data is None:
        return set()
    if not isinstance(data, dict):
        f.error("mappings YAML must be a mapping at top level")
        return set()

    declared: set[str] = set()
    prefixes = data.get("prefixes") or {}
    if not isinstance(prefixes, dict):
        f.error("mappings `prefixes` must be a map of prefix -> config")
        prefixes = {}
    for prefix, cfg in prefixes.items():
        if not isinstance(prefix, str) or not PREFIX_RE.match(prefix):
            f.error(f"prefix {prefix!r} does not match {PREFIX_RE.pattern}")
            continue
        declared.add(prefix)
        if not isinstance(cfg, dict):
            f.error(f"prefix {prefix}: config must be a map")
            continue
        for field in ("display_name", "jurisdiction", "authority_type"):
            if not isinstance(cfg.get(field), str) or not cfg.get(field).strip():
                f.error(f"prefix {prefix}: `{field}` must be a non-empty string")
        atype = cfg.get("authority_type")
        if isinstance(atype, str) and atype not in ALL_AUTHORITY_TYPES:
            f.error(
                f"prefix {prefix}: authority_type {atype!r} not in "
                f"{sorted(ALL_AUTHORITY_TYPES)}"
            )
        aliases = cfg.get("aliases", [])
        if aliases is not None and (
            not isinstance(aliases, list)
            or any(not isinstance(a, str) or not a.strip() for a in aliases)
        ):
            f.error(f"prefix {prefix}: `aliases` must be a list of non-empty strings")

    for i, eq in enumerate(data.get("equivalences") or []):
        if not isinstance(eq, dict):
            f.error(f"equivalences[{i}] must be a map")
            continue
        for field in ("from_key", "to_key"):
            val = eq.get(field)
            if not isinstance(val, str) or not CANONICAL_KEY_RE.match(val):
                f.error(
                    f"equivalences[{i}].{field} {val!r} is not a canonical "
                    "`prefix:locator` key"
                )

    for i, rule in enumerate(data.get("rewrite_rules") or []):
        if not isinstance(rule, dict):
            f.error(f"rewrite_rules[{i}] must be a map")
            continue
        pattern = rule.get("pattern")
        if not isinstance(pattern, str):
            f.error(f"rewrite_rules[{i}].pattern must be a string")
        else:
            try:
                re.compile(pattern)
            except re.error as e:
                f.error(f"rewrite_rules[{i}].pattern does not compile: {e}")
        if not isinstance(rule.get("replacement"), str):
            f.error(f"rewrite_rules[{i}].replacement must be a string")

    for i, rule in enumerate(data.get("shape_rules") or []):
        if not isinstance(rule, dict):
            f.error(f"shape_rules[{i}] must be a map")
            continue
        pattern = rule.get("pattern")
        if isinstance(pattern, str):
            try:
                re.compile(pattern)
            except re.error as e:
                f.error(f"shape_rules[{i}].pattern does not compile: {e}")
        else:
            f.error(f"shape_rules[{i}].pattern must be a string")
        atype = rule.get("authority_type")
        if atype is not None and atype not in ALL_AUTHORITY_TYPES:
            f.error(f"shape_rules[{i}].authority_type {atype!r} invalid")

    abbrevs = data.get("abbreviations") or {}
    if not isinstance(abbrevs, dict):
        f.error("`abbreviations` must be a map with `state`/`municipal` tables")
        abbrevs = {}
    for table_name, table in abbrevs.items():
        if table_name not in ("state", "municipal"):
            f.error(f"abbreviations table {table_name!r} (expected state|municipal)")
            continue
        if not isinstance(table, dict):
            f.error(f"abbreviations.{table_name} must be a map")
            continue
        for surface, cfg in table.items():
            if not isinstance(cfg, dict):
                f.error(f"abbreviations.{table_name}[{surface!r}] must be a map")
                continue
            if not isinstance(cfg.get("prefix"), str) or not PREFIX_RE.match(
                cfg.get("prefix", "")
            ):
                f.error(
                    f"abbreviations.{table_name}[{surface!r}].prefix must be a "
                    "valid prefix"
                )
            atype = cfg.get("authority_type")
            if atype is not None and atype not in ALL_AUTHORITY_TYPES:
                f.error(
                    f"abbreviations.{table_name}[{surface!r}].authority_type "
                    f"{atype!r} invalid"
                )

    return declared


def _validate_spec(
    f: PackFindings, path: Path, declared_prefixes: set[str], corpus_label: str
) -> None:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        f.error(f"{corpus_label}: spec is not valid JSON: {e}")
        return
    if not isinstance(spec, dict):
        f.error(f"{corpus_label}: spec must be a JSON object")
        return

    aliases = spec.get("aliases")
    if aliases is not None and (
        not isinstance(aliases, list)
        or any(not isinstance(a, str) or not a.strip() for a in aliases)
    ):
        # A bare string would be iterated character-by-character downstream.
        f.error(f"{corpus_label}: spec `aliases` must be a list of strings")

    sections = spec.get("sections")
    if not isinstance(sections, list) or not sections:
        f.error(f"{corpus_label}: spec `sections` must be a non-empty list")
        return

    seen_keys: set[str] = set()
    section_prefixes: set[str] = set()
    for i, sec in enumerate(sections):
        label = f"{corpus_label}: sections[{i}]"
        if not isinstance(sec, dict):
            f.error(f"{label} must be an object")
            continue
        for field in ("key", "heading", "text"):
            val = sec.get(field)
            if not isinstance(val, str) or not val.strip():
                f.error(f"{label}.{field} must be a non-empty string")
        key = sec.get("key")
        if isinstance(key, str):
            if not CANONICAL_KEY_RE.match(key):
                f.error(f"{label}.key {key!r} is not `prefix:locator`")
            elif key in seen_keys:
                f.error(f"{label}.key {key!r} duplicated within the spec")
            else:
                seen_keys.add(key)
                section_prefixes.add(key.split(":", 1)[0])
        url = sec.get("source_url")
        if url is not None and not str(url).startswith(("http://", "https://")):
            f.error(f"{label}.source_url must be http(s), got {url!r}")

    # Prefix declaration: enforced only when the pack declares prefixes at all
    # (a taxonomy-free v1 pack is valid with any well-formed keys).
    if declared_prefixes:
        undeclared = section_prefixes - declared_prefixes
        if undeclared:
            f.error(
                f"{corpus_label}: section key prefix(es) {sorted(undeclared)} not "
                "declared in the pack's `prefixes` block"
            )

    # The trap we shipped once: spec-level aliases attach to EVERY document and
    # map each alias to that document's own prefix, overriding namespace rows —
    # in a corpus whose sections span multiple prefixes this silently mis-maps
    # aliases in the registry. Namespace aliases belong in the mappings YAML.
    if aliases and len(section_prefixes) > 1:
        f.error(
            f"{corpus_label}: spec declares `aliases` but its sections span "
            f"multiple prefixes {sorted(section_prefixes)} — per-document alias "
            "stamping would mis-map aliases onto the wrong prefix. Move aliases "
            "to the mappings YAML `prefixes` block."
        )


def validate_pack(pack_dir: Path) -> PackFindings:
    f = PackFindings(pack_dir)
    manifest_path = pack_dir / "pack.yaml"
    if not manifest_path.is_file():
        f.error("pack.yaml missing")
        return f
    manifest = _load_yaml(f, manifest_path, "pack.yaml")
    if manifest is None:
        return f
    if not isinstance(manifest, dict):
        f.error("pack.yaml must be a mapping")
        return f

    name = manifest.get("name")
    if not isinstance(name, str) or not PACK_NAME_RE.match(name) or len(name) > 64:
        f.error(f"pack `name` {name!r} must be a slug of ≤64 chars")
    elif name == "core":
        f.error("pack `name` 'core' is reserved")

    schema_version = manifest.get("schema_version", 1)
    if schema_version not in (1, 2):
        f.error(f"schema_version {schema_version!r} must be 1 or 2")

    if not manifest.get("mappings") and not manifest.get("corpora"):
        f.error("pack must declare at least one of `mappings` / `corpora`")

    declared_prefixes: set[str] = set()
    if manifest.get("mappings"):
        mp = _pack_file(f, str(manifest["mappings"]), "mappings")
        if mp is not None:
            declared_prefixes = _validate_mappings(f, mp)

    if not (pack_dir / "README.md").is_file():
        f.warn("no README.md — packs in this registry document contents + provenance")

    seen_slugs: set[str] = set()
    prefix_bindings: dict[str, str] = {}
    corpora = manifest.get("corpora") or []
    if not isinstance(corpora, list):
        f.error("`corpora` must be a list")
        corpora = []
    for i, entry in enumerate(corpora):
        label = f"corpora[{i}]"
        if not isinstance(entry, dict):
            f.error(f"{label} must be a map")
            continue
        title = entry.get("title")
        if not isinstance(title, str) or not title.strip():
            f.error(f"{label}.title must be a non-empty string")
        slug = entry.get("slug")
        if schema_version == 2:
            if not isinstance(slug, str) or not SLUG_RE.match(slug):
                f.error(f"{label}.slug is required (a slug) in schema v2")
            elif slug in seen_slugs:
                f.error(f"{label}.slug {slug!r} duplicated within the pack")
            else:
                seen_slugs.add(slug)
        for prefix in entry.get("authority_prefixes") or []:
            if prefix not in declared_prefixes:
                f.error(
                    f"{label}: authority_prefixes entry {prefix!r} not declared "
                    "in the pack's `prefixes` block"
                )
            elif prefix in prefix_bindings:
                f.error(
                    f"{label}: prefix {prefix!r} already bound by corpus "
                    f"{prefix_bindings[prefix]!r} — a prefix shared by more than "
                    "one corpus must be left unbound"
                )
            else:
                prefix_bindings[prefix] = slug or str(i)

        spec_rel = entry.get("spec")
        if not spec_rel:
            f.error(f"{label}.spec is required")
        else:
            sp = _pack_file(f, str(spec_rel), f"{label}.spec")
            if sp is not None:
                _validate_spec(f, sp, declared_prefixes, label)

        if schema_version == 2:
            charter_rel = entry.get("charter")
            if not charter_rel:
                f.error(f"{label}.charter is required in schema v2")
            else:
                cp = _pack_file(f, str(charter_rel), f"{label}.charter")
                if cp is not None:
                    charter = _load_yaml(f, cp, f"{label}.charter")
                    if isinstance(charter, dict):
                        purpose = charter.get("purpose")
                        if not isinstance(purpose, str) or not purpose.strip():
                            f.error(
                                f"{label}.charter must carry a non-empty `purpose`"
                            )
                    elif charter is not None:
                        f.error(f"{label}.charter must be a YAML mapping")

        persona_rel = entry.get("persona")
        if persona_rel:
            pp = _pack_file(f, str(persona_rel), f"{label}.persona")
            if pp is not None and not pp.read_text(encoding="utf-8").strip():
                f.error(f"{label}.persona file is empty")

    return f


def discover_packs(root: Path) -> list[Path]:
    return sorted(
        p.parent for p in root.glob("*/pack.yaml") if p.parent.name != "scripts"
    )


def self_test() -> int:
    """Prove the validator can fail: a deliberately broken pack must produce
    errors, and a minimal valid pack must produce none."""
    with tempfile.TemporaryDirectory() as tmp:
        ok_dir = Path(tmp) / "ok_pack"
        ok_dir.mkdir()
        (ok_dir / "pack.yaml").write_text(
            yaml.safe_dump({"name": "p", "corpora": [{"title": "A", "spec": "a.json"}]})
        )
        (ok_dir / "a.json").write_text(
            json.dumps({"sections": [{"key": "x:1", "heading": "H", "text": "T"}]})
        )
        (ok_dir / "README.md").write_text("readme")
        ok = validate_pack(ok_dir)

        bad_dir = Path(tmp) / "bad_pack"
        bad_dir.mkdir()
        (bad_dir / "pack.yaml").write_text(
            yaml.safe_dump(
                {
                    "name": "Bad Name!",
                    "schema_version": 2,
                    "mappings": "m.yaml",
                    "corpora": [{"title": "", "spec": "missing.json"}],
                }
            )
        )
        (bad_dir / "m.yaml").write_text(
            yaml.safe_dump(
                {
                    "prefixes": {
                        "ok-prefix": {
                            "display_name": "X",
                            "jurisdiction": "zz",
                            "authority_type": "not-a-type",
                        }
                    }
                }
            )
        )
        bad = validate_pack(bad_dir)

        mixed_dir = Path(tmp) / "mixed_alias_pack"
        mixed_dir.mkdir()
        (mixed_dir / "pack.yaml").write_text(
            yaml.safe_dump(
                {
                    "name": "mixed",
                    "mappings": "m.yaml",
                    "corpora": [{"title": "M", "spec": "s.json"}],
                }
            )
        )
        (mixed_dir / "m.yaml").write_text(
            yaml.safe_dump(
                {
                    "prefixes": {
                        "aa": {
                            "display_name": "A",
                            "jurisdiction": "zz",
                            "authority_type": "statute",
                        },
                        "bb": {
                            "display_name": "B",
                            "jurisdiction": "zz",
                            "authority_type": "statute",
                        },
                    }
                }
            )
        )
        (mixed_dir / "s.json").write_text(
            json.dumps(
                {
                    "aliases": ["some alias"],
                    "sections": [
                        {"key": "aa:1", "heading": "H", "text": "T"},
                        {"key": "bb:1", "heading": "H", "text": "T"},
                    ],
                }
            )
        )
        mixed = validate_pack(mixed_dir)

        # Two packs, each valid alone, colliding on a prefix and a slug. The
        # per-pack validation must stay silent and the registry check must not.
        twins = []
        for name in ("twin_a", "twin_b"):
            twin_dir = Path(tmp) / name
            twin_dir.mkdir()
            (twin_dir / "pack.yaml").write_text(
                yaml.safe_dump(
                    {
                        "name": name,
                        "schema_version": 2,
                        "mappings": "m.yaml",
                        "corpora": [
                            {
                                "slug": "shared-corpus",
                                "title": "T",
                                "authority_prefixes": ["dup"],
                                "spec": "s.json",
                                "charter": "c.yaml",
                            }
                        ],
                    }
                )
            )
            (twin_dir / "m.yaml").write_text(
                yaml.safe_dump(
                    {
                        "prefixes": {
                            "dup": {
                                "display_name": "D",
                                "jurisdiction": "zz",
                                "authority_type": "statute",
                            }
                        }
                    }
                )
            )
            (twin_dir / "s.json").write_text(
                json.dumps({"sections": [{"key": "dup:1", "heading": "H", "text": "T"}]})
            )
            (twin_dir / "c.yaml").write_text(yaml.safe_dump({"purpose": "p"}))
            (twin_dir / "README.md").write_text("readme")
            twins.append(twin_dir)
        twin_findings = [validate_pack(d) for d in twins]
        collisions = cross_pack_collisions(twins)

    failures = []
    if ok.errors:
        failures.append(f"valid pack produced errors: {ok.errors}")
    if not bad.errors:
        failures.append("broken pack produced no errors")
    if not any("span multiple prefixes" in e for e in mixed.errors):
        failures.append("mixed-prefix spec aliases not caught")
    if any(f.errors for f in twin_findings):
        failures.append(
            "colliding packs must each be valid ALONE — otherwise the registry "
            "check is not what caught the collision"
        )
    if not any("prefix 'dup'" in c for c in collisions):
        failures.append("cross-pack prefix collision not caught")
    if not any("corpus slug 'shared-corpus'" in c for c in collisions):
        failures.append("cross-pack corpus slug collision not caught")
    if cross_pack_collisions(twins[:1]):
        failures.append("a single pack collided with itself")
    if failures:
        for msg in failures:
            print(f"SELF-TEST FAIL: {msg}")
        return 1
    print(f"self-test ok (broken pack raised {len(bad.errors)} errors as expected)")
    return 0


def cross_pack_collisions(pack_dirs: list[Path]) -> list[str]:
    """Two packs must never declare the same prefix or the same corpus slug.

    Every other check here is per-pack, and this one cannot be: each pack is
    individually valid while declaring `ofac`, and the conflict only exists in
    the registry as a whole. It matters more than its size suggests, because a
    prefix binds to exactly one corpus PERMANENTLY — the installer refuses to
    move a bound prefix, so whichever pack installs second is not merely
    rejected, it is unshippable against every deployment that installed the
    first. There is no remedy short of a new prefix.

    Atomic base packs make this reachable in a way a registry of monoliths did
    not: splitting one body of law across packs, or copying a pack as the
    starting point for a neighbouring one, both produce it silently.
    """
    problems: list[str] = []
    prefix_owner: dict[str, str] = {}
    slug_owner: dict[str, str] = {}

    for pack_dir in pack_dirs:
        try:
            manifest = yaml.safe_load((pack_dir / "pack.yaml").read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue  # already reported by the per-pack validation
        if not isinstance(manifest, dict):
            continue

        declared: set[str] = set()
        mappings_rel = manifest.get("mappings")
        if mappings_rel:
            mappings_path = pack_dir / str(mappings_rel)
            try:
                mappings = yaml.safe_load(mappings_path.read_text(encoding="utf-8"))
                declared = set((mappings or {}).get("prefixes") or {})
            except (OSError, yaml.YAMLError):
                declared = set()

        for prefix in sorted(declared):
            if prefix in prefix_owner:
                problems.append(
                    f"prefix {prefix!r} is declared by both {prefix_owner[prefix]!r} "
                    f"and {pack_dir.name!r} — a prefix binds to one corpus "
                    "permanently, so the second pack to install is unshippable"
                )
            else:
                prefix_owner[prefix] = pack_dir.name

        for entry in manifest.get("corpora") or []:
            if not isinstance(entry, dict):
                continue
            slug = entry.get("slug")
            if not slug:
                continue
            if slug in slug_owner:
                problems.append(
                    f"corpus slug {slug!r} is declared by both "
                    f"{slug_owner[slug]!r} and {pack_dir.name!r}"
                )
            else:
                slug_owner[slug] = pack_dir.name

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packs", nargs="*", help="Pack directory names to validate")
    parser.add_argument("--all", action="store_true", help="Validate every pack")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    if args.all:
        targets = discover_packs(REPO_ROOT)
    elif args.packs:
        targets = [REPO_ROOT / p for p in args.packs]
    else:
        parser.error("give pack names, --all, or --self-test")

    exit_code = 0
    for pack_dir in targets:
        findings = validate_pack(pack_dir)
        status = "OK" if not findings.errors else "INVALID"
        print(f"{pack_dir.name}: {status}")
        for msg in findings.errors:
            exit_code = 1
            print(f"  ERROR: {msg}")
        for msg in findings.warnings:
            print(f"  warn:  {msg}")

    # Only meaningful over the whole registry; validating a subset by name
    # cannot see a collision with a pack that was not named.
    if args.all:
        for msg in cross_pack_collisions(targets):
            exit_code = 1
            print(f"REGISTRY ERROR: {msg}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
