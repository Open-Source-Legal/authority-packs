# Domain packs

A **domain pack** composes atomic base packs and supplies the wiring that
belongs to none of them.

    base pack   = one body of law. One publisher, one update cadence, one
                  provenance story, one approval status. Reusable.
    domain pack = a named set of base packs, plus the corpus group, the
                  orchestrator persona, and cross-pack equivalences.

A domain pack carries little or no text of its own. Everything in it is *about*
the relationship between bodies of law.

## Why the split

**Review cadence differs by kind of artifact.** Verbatim law is expensive to
review and changes when the publisher says so. The orchestration story — which
body governs when two overlap — is opinionated and revised often. Fused into one
artifact, every revision to the reasoning re-releases megabytes of unchanged
law, and every routine currency refresh reopens the reasoning for review.

**The same base pack wants different orchestration in different domains.** One
body of law can be central in one domain and a peripheral cross-check in
another, with different precedence against its neighbours. A monolithic pack can
encode only one reading.

**Composition is safe by construction.** A namespace prefix binds to exactly one
corpus, permanently, and the installer refuses to move it. Two base packs
therefore cannot collide.

## The install contract

These are the assertions a conforming installer must satisfy. They are stated
about POST-INSTALL STATE, not about implementation, so the same contract can be
checked from either side.

**C1 — Completeness.** Every base pack named in `requires` is installed. An
installer that cannot obtain one FAILS; it does not install the remainder and
report success.

**C2 — Reachability.** Every corpus contributed by a required base pack is a
member of the declared corpus group. If the platform caps group size, exceeding
the cap is an ERROR, not a silent truncation.

**C3 — Addressability.** The orchestrator is created, is bound to the group, and
carries every tool the domain pack declares. If the platform cannot grant a
declared tool, the install FAILS.

**C4 — Resolution.** Every `equivalences` row resolves: `to_key` names a section
that exists in one of the required base packs. A row whose target is absent is
an ERROR at validation time, before install.

**C5 — Honesty.** An installer reports what it created AND what it could not.
"Installed successfully" must not be printable while any assertion above is
unmet.

**C6 — Idempotence.** Re-running an install converges. It does not duplicate a
group, an orchestrator, or an equivalence row.

**C7 — No orphan authority.** A domain pack MUST NOT introduce namespace
prefixes or section text of its own. Its `equivalences` may only map between
keys owned by its required base packs. Authority text belongs to a base pack,
where its provenance and approval status live.

## File shape

A directory containing `domain.yaml` is a domain pack. A directory containing
`pack.yaml` is a base pack. A directory MUST NOT contain both.

```yaml
schema_version: 1
name: <slug>                      # [a-z0-9][a-z0-9_-]*
title: <human readable>
description: >
  What this domain is, and what question it exists to answer correctly.

requires:
  - pack: <base-pack-name>        # a directory in this registry
    reason: >                     # why this body of law is in this domain
      ...

corpus_group:
  slug: <slug>
  title: <human readable>
  # Optional. Corpora that are already reachable another way (heavily cited by
  # the consuming documents) may be excluded to stay under a platform cap.
  # Excluding a corpus is a claim that it is reachable WITHOUT the group.
  exclude_corpora: [<corpus-slug>, ...]

orchestrator:
  # The system instructions for the agent bound to the group. This is the
  # substance of a domain pack: how these bodies of law interact.
  instructions_file: orchestrator.txt
  tools:
    - search_across_corpora
  preferred_llm: <optional model id>

# Rows that span two base packs and belong to neither. Same shape as a base
# pack's mappings equivalences.
equivalences:
  - {from_key: "a:800.215", to_key: "b:800.215", note: "..."}
```

### `requires[].reason` is not decoration

A domain pack is an editorial artifact. The reason a body of law is present is
the thing a reviewer needs in order to disagree, and it is what tells a future
maintainer whether a pack can be dropped.

### Why `equivalences` live here

Two bodies of law can share a CFR title. A namespace alias maps a whole title to
one prefix, so a citation to the part owned by the *other* corpus extracts under
the wrong prefix and resolves to nothing. The folding rows that fix it belong to
neither base pack alone — they exist only because both are installed together.

## What a domain pack must not do

- Declare `prefixes` or ship `specs/`. That is a base pack's job (**C7**).
- Silently drop a required pack or corpus (**C1**, **C2**).
- Depend on a consuming corpus's persona to make its tools reachable. If the
  orchestrator needs the group slug in order to call a tool, the orchestrator's
  own instructions carry it.

## Validation

    python scripts/validate_pack.py --all          # base packs
    python scripts/validate_domain.py --all        # domain packs
    python scripts/validate_domain.py --self-test  # prove the checks can fail

`validate_domain.py` checks C4 and C7 statically — it can see whether a
`to_key` exists in a required base pack, and whether a domain pack is smuggling
authority text. C1, C2, C3, C5 and C6 are install-time and belong to the
platform; they are stated here so both sides implement the same contract.
