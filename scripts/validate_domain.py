#!/usr/bin/env python3
"""Validate domain packs — the composition layer over atomic base packs.

    python scripts/validate_domain.py --all
    python scripts/validate_domain.py us-export-control
    python scripts/validate_domain.py --self-test   # prove the checks can fail

A domain pack composes base packs and supplies the wiring that belongs to none
of them: the corpus group, the orchestrator persona, cross-pack equivalences,
and optionally a consumer_agent increment for whichever corpus ends up
consuming it. See DOMAIN_PACKS.md for the shape and the install contract.

This script checks the parts of that contract that are decidable WITHOUT a
platform — statically, from the files in this repository:

    C4  every `equivalences` to_key names a section that exists in a required
        base pack. A row pointing at nothing is an error before install, not a
        silent no-op afterwards.
    C7  a domain pack introduces no authority of its own: no `prefixes`, no
        `specs/`, and both sides of every equivalence row use a prefix owned by
        a required base pack.
    C8  a declared `consumer_agent` is EXTEND-mode, its instructions file is
        present, readable and non-empty, its tools are grantable, and — when it
        declares `search_across_corpora` — its instructions name the group slug.
        Only the file-decidable half: the BINDING (which corpus consumes the
        domain) is supplied at install time and cannot be checked here.

C1/C2/C3/C5/C6 and C8's binding half are install-time assertions and belong to
the platform. They are stated in DOMAIN_PACKS.md so both sides implement the
same contract.

Deliberately mirrors validate_pack.py's structure and exit conventions so CI can
run them side by side.
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
DOMAINS_DIR = "domains"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:.+$")

# Mirrors AuthorityKeyEquivalence.note = CharField(max_length=255).
MAX_NOTE = 255

# Tools a domain pack may request for its orchestrator or consumer_agent.
# Closed on purpose: a typo here is otherwise discovered as "the agent never
# calls the tool", which is indistinguishable from the model choosing not to.
KNOWN_TOOLS = {
    "search_across_corpora",
    "ask_document",
    "search_exact_text",
}


class Findings:
    def __init__(self, domain_dir: Path):
        self.domain_dir = domain_dir
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _base_pack_index(root: Path) -> dict[str, dict]:
    """{pack_name: {"prefixes": set, "keys": set, "corpora": set}} for every base pack."""
    index: dict[str, dict] = {}
    for manifest in sorted(root.glob("*/pack.yaml")):
        pack_dir = manifest.parent
        try:
            manifest_data = yaml.safe_load(manifest.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        prefixes: set[str] = set()
        keys: set[str] = set()
        corpora: set[str] = set()
        for corpus in manifest_data.get("corpora") or []:
            corpora.add(str(corpus.get("slug", "")))
            prefixes.update(str(p) for p in (corpus.get("authority_prefixes") or []))
            spec_rel = corpus.get("spec")
            if not spec_rel:
                continue
            spec_path = pack_dir / spec_rel
            if not spec_path.is_file():
                continue
            try:
                spec = json.loads(spec_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for section in spec.get("sections") or []:
                key = section.get("key")
                if key:
                    keys.add(str(key))
        index[pack_dir.name] = {
            "prefixes": prefixes,
            "keys": keys,
            "corpora": corpora,
        }
    return index


def _validate_instructions_block(f: Findings, domain_dir: Path, group,
                                  block: dict, *, label: str,
                                  warn_if_no_tools: bool,
                                  missing_file_hint: str = "") -> None:
    """Shared shape between `orchestrator` and `consumer_agent`: an
    instructions file that must live inside the domain dir and be readable
    and non-empty; tools drawn from KNOWN_TOOLS; and, if
    `search_across_corpora` is among them, instructions that name the corpus
    group's slug — the tool takes it as a required argument, so an agent
    never told the slug cannot call it (C3 for the orchestrator, C8 for a
    consumer_agent)."""
    rel = block.get("instructions_file")
    if not rel:
        hint = f" — {missing_file_hint}" if missing_file_hint else ""
        f.error(f"{label}.instructions_file is required{hint}")
    else:
        candidate = (domain_dir / str(rel)).resolve()
        if not str(candidate).startswith(str(domain_dir.resolve()) + "/"):
            f.error(f"{label}.instructions_file escapes the domain "
                    f"directory: {rel}")
        elif not candidate.is_file():
            f.error(f"{label}.instructions_file missing: {rel}")
        elif not candidate.read_text(encoding="utf-8").strip():
            f.error(f"{label}.instructions_file is empty: {rel}")

    tools = [str(t) for t in (block.get("tools") or [])]
    if warn_if_no_tools and not tools:
        f.warn(f"{label} declares no tools; without search_across_corpora "
               "the group is not actually reachable")
    for tool in tools:
        if tool not in KNOWN_TOOLS:
            f.error(f"{label}.tools: unknown tool {tool!r} (known: "
                    f"{', '.join(sorted(KNOWN_TOOLS))})")

    if "search_across_corpora" in tools and isinstance(group, dict) and rel:
        slug = str(group.get("slug") or "")
        if slug:
            path = domain_dir / str(rel)
            if path.is_file() and slug not in path.read_text(encoding="utf-8"):
                f.error(
                    f"{label} declares search_across_corpora but its "
                    f"instructions never name the group slug {slug!r}. The "
                    "tool takes corpus_group as a REQUIRED argument, so an "
                    "agent that is not told the slug cannot call it."
                )


def validate_domain(domain_dir: Path, root: Path) -> Findings:
    f = Findings(domain_dir)
    manifest_path = domain_dir / "domain.yaml"
    if not manifest_path.is_file():
        f.error("domain.yaml missing")
        return f
    if (domain_dir / "pack.yaml").is_file():
        f.error("directory has BOTH domain.yaml and pack.yaml; it must be one or "
                "the other")
    if (domain_dir / "specs").exists():
        f.error("C7: domain pack ships specs/ — authority text belongs to a base "
                "pack, where its provenance and approval status live")

    try:
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        f.error(f"domain.yaml is not valid YAML: {exc}")
        return f
    if not isinstance(data, dict):
        f.error("domain.yaml must be a mapping")
        return f

    if data.get("schema_version") != 1:
        f.error(f"schema_version must be 1, got {data.get('schema_version')!r}")
    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        f.error(f"name must match {NAME_RE.pattern}, got {name!r}")
    elif name != domain_dir.name:
        f.error(f"name {name!r} does not match directory {domain_dir.name!r}")
    if not data.get("title"):
        f.error("title is required")
    if "prefixes" in data:
        f.error("C7: domain pack declares `prefixes` — namespaces are owned by "
                "base packs")

    # --- requires -------------------------------------------------------- #
    base_index = _base_pack_index(root)
    requires = data.get("requires")
    required_names: list[str] = []
    if not isinstance(requires, list) or not requires:
        f.error("requires must be a non-empty list")
    else:
        for i, entry in enumerate(requires):
            if not isinstance(entry, dict) or not entry.get("pack"):
                f.error(f"requires[{i}] must be a mapping with a `pack` key")
                continue
            pack_name = str(entry["pack"])
            required_names.append(pack_name)
            if pack_name not in base_index:
                f.error(f"requires[{i}]: base pack {pack_name!r} is not in this "
                        "registry")
            if not entry.get("reason"):
                f.warn(f"requires[{i}] ({pack_name}): no `reason` — a domain pack "
                       "is an editorial artifact; say why this body of law is here")

    owned_prefixes: set[str] = set()
    owned_keys: set[str] = set()
    owned_corpora: set[str] = set()
    for pack_name in required_names:
        info = base_index.get(pack_name)
        if info:
            owned_prefixes |= info["prefixes"]
            owned_keys |= info["keys"]
            owned_corpora |= info["corpora"]

    # --- corpus group ---------------------------------------------------- #
    group = data.get("corpus_group")
    if not isinstance(group, dict):
        f.error("corpus_group is required (a domain pack exists to make its "
                "members reachable)")
    else:
        slug = group.get("slug")
        if not isinstance(slug, str) or not SLUG_RE.match(slug):
            f.error(f"corpus_group.slug must match {SLUG_RE.pattern}, got {slug!r}")
        if not group.get("title"):
            f.error("corpus_group.title is required")
        for corpus_slug in group.get("exclude_corpora") or []:
            if str(corpus_slug) not in owned_corpora:
                f.error(f"corpus_group.exclude_corpora names {corpus_slug!r}, "
                        "which no required base pack contributes")

    # --- orchestrator ---------------------------------------------------- #
    orch = data.get("orchestrator")
    if not isinstance(orch, dict):
        f.error("orchestrator is required")
    else:
        _validate_instructions_block(
            f, domain_dir, group, orch, label="orchestrator",
            warn_if_no_tools=True,
            missing_file_hint="the orchestration story is the substance of "
                               "a domain pack",
        )

    # --- consumer agent (C8) --------------------------------------------- #
    #
    # Optional. The orchestrator above is GLOBAL and knows the domain; this one
    # is scoped at install time to the corpus holding the documents a user asks
    # about, and needs BOTH that corpus's persona and reach into the group.
    #
    # The pack supplies only the text, because the group slug it must name is
    # the pack's own invention. The binding — which corpus — is supplied by the
    # operator via `install_domain_pack --consumer-corpus`, because a pack
    # cannot know which corpus will consume it. That split is what keeps this
    # inside the prohibition on coupling to a consuming corpus's persona rather
    # than outside it.
    consumer = data.get("consumer_agent")
    if consumer is not None:
        if not isinstance(consumer, dict):
            f.error("consumer_agent must be a mapping")
        else:
            # EXTEND is required, not merely recommended. REPLACE would
            # overwrite the consuming corpus's own persona with pack-supplied
            # text — the coupling this document forbids. EXTEND appends, so the
            # persona stays single-sourced on the corpus and the pack
            # contributes only its increment.
            mode = str(consumer.get("mode") or "")
            if mode != "EXTEND":
                f.error(
                    f"consumer_agent.mode must be 'EXTEND' (got {mode!r}). "
                    "REPLACE would overwrite the consuming corpus's persona "
                    "with text shipped by this pack."
                )
            _validate_instructions_block(
                f, domain_dir, group, consumer, label="consumer_agent",
                warn_if_no_tools=False,
            )

    # --- equivalences (C4, C7) ------------------------------------------- #
    for i, row in enumerate(data.get("equivalences") or []):
        if not isinstance(row, dict):
            f.error(f"equivalences[{i}] must be a mapping")
            continue
        frm, to = row.get("from_key"), row.get("to_key")
        for label, key in (("from_key", frm), ("to_key", to)):
            if not isinstance(key, str) or not KEY_RE.match(key):
                f.error(f"equivalences[{i}].{label} malformed: {key!r}")
        note = row.get("note")
        if isinstance(note, str) and len(note) > MAX_NOTE:
            # The platform stores this in a CharField(max_length=255); Postgres
            # rejects anything longer with a DataError raised part-way through
            # the install, after the base packs are already written. A static,
            # platform-independent fact about the schema, so a pack author
            # should learn it at PR time rather than at install time.
            f.error(
                f"equivalences[{i}].note is {len(note)} chars; the platform "
                f"column holds {MAX_NOTE}"
            )
        if not isinstance(frm, str) or not isinstance(to, str):
            continue
        if frm == to:
            f.error(f"equivalences[{i}] maps {frm!r} to itself")
        # C7 — both sides must belong to a required base pack.
        for label, key in (("from_key", frm), ("to_key", to)):
            prefix = key.split(":", 1)[0]
            if prefix not in owned_prefixes:
                f.error(f"C7: equivalences[{i}].{label} uses prefix {prefix!r}, "
                        "which no required base pack owns")
        # C4 — the target must actually exist.
        if to.split(":", 1)[0] in owned_prefixes and to not in owned_keys:
            f.error(f"C4: equivalences[{i}].to_key {to!r} does not name a section "
                    "in any required base pack")
    return f


def discover_domains(root: Path) -> list[Path]:
    base = root / DOMAINS_DIR
    if not base.is_dir():
        return []
    return sorted(p.parent for p in base.glob("*/domain.yaml"))


def self_test() -> int:
    """Prove the checks can fail. A validator nobody has seen fail is a rubber stamp."""
    cases = 0
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A minimal, valid base pack to compose.
        pack = root / "basepack"
        (pack / "specs").mkdir(parents=True)
        (pack / "specs/a.json").write_text(
            json.dumps({"sections": [{"key": "aa:1"}, {"key": "bb:2"}]}),
            encoding="utf-8")
        (pack / "pack.yaml").write_text(yaml.safe_dump({
            "corpora": [{"slug": "ca", "authority_prefixes": ["aa", "bb"],
                         "spec": "specs/a.json"}]}), encoding="utf-8")

        def build(mutate) -> Findings:
            dom = root / DOMAINS_DIR / "d"
            if dom.exists():
                for child in dom.iterdir():
                    child.unlink()
            dom.mkdir(parents=True, exist_ok=True)
            (dom / "orchestrator.txt").write_text("use group d-group", encoding="utf-8")
            manifest = {
                "schema_version": 1, "name": "d", "title": "D",
                "requires": [{"pack": "basepack", "reason": "because"}],
                "corpus_group": {"slug": "d-group", "title": "D group"},
                "orchestrator": {"instructions_file": "orchestrator.txt",
                                 "tools": ["search_across_corpora"]},
                "equivalences": [{"from_key": "bb:2", "to_key": "aa:1"}],
            }
            mutate(manifest, dom)
            (dom / "domain.yaml").write_text(yaml.safe_dump(manifest), encoding="utf-8")
            return validate_domain(dom, root)

        def check(label: str, mutate, want_error: bool) -> None:
            nonlocal cases, failures
            cases += 1
            findings = build(mutate)
            got_error = bool(findings.errors)
            if got_error != want_error:
                failures += 1
                print(f"  SELF-TEST FAIL: {label} — expected "
                      f"{'error' if want_error else 'clean'}, got "
                      f"{findings.errors or 'clean'}")
            else:
                print(f"  ok: {label}")

        check("a well-formed domain pack validates", lambda m, d: None, False)
        check("C4: to_key that names no section is rejected",
              lambda m, d: m["equivalences"].__setitem__(
                  0, {"from_key": "bb:2", "to_key": "aa:999"}), True)
        check("C7: prefix no base pack owns is rejected",
              lambda m, d: m["equivalences"].__setitem__(
                  0, {"from_key": "zz:1", "to_key": "aa:1"}), True)
        check("C7: declaring prefixes is rejected",
              lambda m, d: m.__setitem__("prefixes", {"zz": {}}), True)
        check("missing base pack is rejected",
              lambda m, d: m["requires"].__setitem__(
                  0, {"pack": "nope", "reason": "x"}), True)
        check("unknown orchestrator tool is rejected",
              lambda m, d: m["orchestrator"].__setitem__("tools", ["teleport"]), True)
        check("orchestrator that never names the group slug is rejected",
              lambda m, d: (d / "orchestrator.txt").write_text("no slug here",
                                                               encoding="utf-8"), True)
        check("excluding a corpus no base pack contributes is rejected",
              lambda m, d: m["corpus_group"].__setitem__(
                  "exclude_corpora", ["ghost"]), True)
        check("self-mapping equivalence is rejected",
              lambda m, d: m["equivalences"].__setitem__(
                  0, {"from_key": "aa:1", "to_key": "aa:1"}), True)
        # The platform stores `note` in a CharField(255) and does not truncate;
        # an over-long one is a DataError raised part-way through the install,
        # after the base packs are written. Cheap to catch here instead.
        check("an over-long equivalence note is rejected",
              lambda m, d: m["equivalences"][0].__setitem__(
                  "note", "x" * (MAX_NOTE + 1)), True)

        # --- C8: the consumer agent --------------------------------------- #
        def with_consumer(m, d, *, mode="EXTEND", tools=None, text=None,
                          rel="consumer.txt"):
            (d / "consumer.txt").write_text(
                text if text is not None else "reach via corpus_group=d-group",
                encoding="utf-8")
            m["consumer_agent"] = {
                "instructions_file": rel,
                "tools": ["search_across_corpora"] if tools is None else tools,
                "mode": mode,
            }

        check("consumer_agent is optional",
              lambda m, d: None, False)
        check("a well-formed consumer_agent validates",
              lambda m, d: with_consumer(m, d), False)
        check("C8: consumer_agent.mode REPLACE is rejected",
              lambda m, d: with_consumer(m, d, mode="REPLACE"), True)
        check("C8: consumer_agent with no mode is rejected",
              lambda m, d: (with_consumer(m, d),
                            m["consumer_agent"].pop("mode")), True)
        check("C8: consumer_agent whose instructions_file is missing is rejected",
              lambda m, d: with_consumer(m, d, rel="absent.txt"), True)
        check("C8: consumer_agent that never names the group slug is rejected",
              lambda m, d: with_consumer(m, d, text="answer from the corpus"), True)
        check("C8: unknown consumer_agent tool is rejected",
              lambda m, d: with_consumer(m, d, tools=["teleport"]), True)
        # A consumer that declares no reach is a legitimate (if odd) shape: it
        # contributes answering rules and nothing else, so the slug rule that
        # only exists to make search_across_corpora callable does not apply.
        check("a consumer_agent with no tools need not name the slug",
              lambda m, d: with_consumer(m, d, tools=[],
                                         text="answer from the corpus"), False)

    print(f"\nself-test: {cases - failures}/{cases} checks behaved as expected")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("domains", nargs="*")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", default=str(REPO_ROOT))
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    root = Path(args.root).resolve()
    if args.all:
        targets = discover_domains(root)
    elif args.domains:
        targets = [root / DOMAINS_DIR / name for name in args.domains]
    else:
        parser.error("give domain names, --all, or --self-test")

    if not targets:
        print("no domain packs found")
        return 0

    failed = 0
    for domain_dir in targets:
        findings = validate_domain(domain_dir, root)
        for warning in findings.warnings:
            print(f"  WARN  {domain_dir.name}: {warning}")
        if findings.errors:
            failed = 1
            for err in findings.errors:
                print(f"  ERROR {domain_dir.name}: {err}")
            print(f"{domain_dir.name}: INVALID")
        else:
            print(f"{domain_dir.name}: OK")
    return failed


if __name__ == "__main__":
    sys.exit(main())
