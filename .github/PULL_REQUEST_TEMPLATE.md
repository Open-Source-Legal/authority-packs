<!-- PR template for authority packs. Delete sections that don't apply
     (e.g. for a fix to an existing pack, keep only what changed + provenance
     for any new text). -->

## Pack

**Name / jurisdiction:**
**New pack or update to an existing one?**

**What law does it cover, and why this selection?**
<!-- Which bodies of law, which chapters/sections, and what kind of filing
     corpus this pack is meant to enrich (what do those documents cite?). -->

## Provenance — where every byte of law text came from

<!-- One row per source. "Verbatim" means the section text is the enacted text,
     unmodified — OCR cleanup and citation-form notes go in the pack README. -->

| Source (URL) | What was taken | Captured | Verbatim? |
|---|---|---|---|
|  |  |  |  |

- [ ] All statutory/ordinance/charter text is **verbatim enacted law** (edicts of government), or clearly labeled as a curated overview in its heading (e.g. "(chapter overview)").
- [ ] No proprietary editorial apparatus was copied from commercial publishers beyond the enacted text itself (headnotes, annotations, summaries written by the publisher).
- [ ] Amendment/ordinance history notes, where included, are part of the enacted compilation.

## Licensing

- [ ] I license my authored contributions in this PR (taxonomy, aliases, equivalences, overviews, personas, charters, selection & arrangement) under **CC BY-SA 4.0**, per the repo LICENSE.
- [ ] I understand the verbatim law text itself is public domain and the license does not (and cannot) restrict it.

## Validation

- [ ] `python scripts/validate_pack.py <pack_name>` passes locally (CI runs it too).
- [ ] The canonical preflight passes against an OpenContracts checkout:
      `manage.py load_authority_pack --path <pack> --creator <u> --check`
      (or `manage.py install_authority_pack <pack> --tarball <archive> --creator <u> --check`).
- [ ] Ran (or attempted) a real install + enrichment against a representative filing corpus, and the pack README notes what resolves. <!-- optional but strongly encouraged; say what you did -->

## Design notes

<!-- Anything a reviewer needs to know about prefix naming (municipal packs:
     use the `muni-<city-slug>` the open-vocab grammar derives), chapter-level
     keys, equivalence choices, or deliberate omissions. Two standing rules:

     1. A corpus whose sections span MULTIPLE prefixes must NOT declare
        spec-level `aliases` (they stamp per-document and mis-map the alias
        registry) — namespace aliases belong in the mappings YAML. The
        validator enforces this.
     2. A prefix bound via `authority_prefixes` may bind to only ONE corpus
        in the pack. -->

## Checklist

- [ ] Pack `README.md` documents contents, provenance, and design notes
- [ ] Catalog table in the repo root `README.md` updated
- [ ] Section `source_url`s point at the public source used
