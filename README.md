# OpenContracts Authority Packs

Curated bodies of law for [OpenContracts](https://github.com/Open-Source-Legal/OpenContracts)
citation enrichment: each top-level directory is a schema-v2 **authority pack** —
a citation taxonomy (namespaces, aliases, equivalences, grammar abbreviations)
plus seeded corpora of verbatim law, installable into any OpenContracts
deployment.

Packs live here, out of the platform repo, so deployments install only the
jurisdictions they want and the platform's MIT license stays untangled from
pack content licensing.

## Installing a pack

From an OpenContracts checkout (fetches from this repo, validates, installs):

```bash
python manage.py install_authority_pack fort_worth --creator <username> --public
```

Useful variants:

```bash
python manage.py install_authority_pack --list                 # what's available
python manage.py install_authority_pack fort_worth --check     # fetch + preflight only
python manage.py install_authority_pack fort_worth --ref main --creator <u> --public
```

Restart celery workers after install — the grammar-tier pack config is cached
per process.

Manual alternative (no management command): clone this repo wholesale and point
`AUTHORITY_PACK_ROOTS` at the clone; every directory containing a `pack.yaml`
is auto-discovered.

```bash
git clone https://github.com/Open-Source-Legal/authority-packs /srv/authority-packs
export AUTHORITY_PACK_ROOTS=/srv/authority-packs
python manage.py load_authority_pack --path /srv/authority-packs/fort_worth --creator <u> --public
```

## Catalog

A pack is **one body of law**: one publisher, one update cadence, one
provenance story, one approval status. That is deliberately small. A pack that
spans several bodies of law forces every revision to the reasoning to
re-release megabytes of unchanged text, and every routine currency refresh to
reopen the reasoning for review. Assemblies are built by composing packs — see
[Domains](#domains) below.

### United States, federal (`us`)

| Pack | Corpora | Sections |
|---|---|---|
| [`aeca`](aeca/) | Arms Export Control Act, by OLRC release point | 55 |
| [`itar`](itar/) | ITAR (22 C.F.R. 120-130) · U.S. Munitions List (Categories I-XXI) | 210 |
| [`ddtc`](ddtc/) | DDTC FAQs and guidance · enforcement and consent agreements · commodity-jurisdiction practice · advisory opinions | 76 |
| [`ear`](ear/) | Export Administration Regulations · Commerce Control List (638 ECCNs) | 1,270 |
| [`ofac`](ofac/) | OFAC sanctions regulations, 31 C.F.R. Chapter V (rules, not rosters) | 978 |
| [`cfius`](cfius/) | CFIUS / FIRRMA, 31 C.F.R. Parts 800 and 802 | 194 |
| [`ecra`](ecra/) | Export Control Reform Act · IEEPA · National Emergencies Act | 38 |
| [`export_fedreg`](export_fedreg/) | Federal Register rule preambles (State/BIS/OFAC) · executive orders | 901 |
| [`export_caselaw`](export_caselaw/) | Federal court decisions construing the AECA, ITAR and EAR | 5 |
| [`multilateral_regimes`](multilateral_regimes/) | Wassenaar · MTCR · Nuclear Suppliers Group · Australia Group control lists | 59 |
| [`doj_data_security`](doj_data_security/) | DOJ Data Security Program, 28 C.F.R. Part 202 | 104 |
| [`nuclear_exports`](nuclear_exports/) | NRC 10 C.F.R. Part 110 · DOE 10 C.F.R. Part 810 | 123 |
| [`nispom`](nispom/) | NISPOM, 32 C.F.R. Part 117 | 25 |
| [`dfars`](dfars/) | DFARS and FAR export-control clauses, 48 C.F.R. | 641 |

### City of Fort Worth, Texas (`us-tx-fort-worth`)

| Pack | Corpora | Sections |
|---|---|---|
| [`fort_worth`](fort_worth/) | City Code procurement **and construction** provisions · City Charter (selected chapters) · Texas procurement & contract-verification statutes · Building Administrative Code · local amendments to the 2021 IRC · Zoning Ordinance (residential) · Texas residential trade licensing & restrictive covenants | 881 |

Each pack's `README.md` documents its contents, provenance, and design notes.

## Domains

A **domain pack** composes atomic base packs and supplies the wiring that
belongs to none of them — the corpus group, the orchestrator persona describing
how those bodies of law interact, and cross-pack equivalences. It carries little
or no text of its own.

| Domain | Composes | Purpose |
|---|---|---|
| [`us-export-control`](domains/us-export-control/) | 14 packs: `aeca` `itar` `ddtc` `ear` `ofac` `cfius` `ecra` `export_fedreg` `export_caselaw` `multilateral_regimes` `doj_data_security` `nuclear_exports` `nispom` `dfars` | Which regime governs a transfer, and what else must clear before it proceeds |

See [DOMAIN_PACKS.md](DOMAIN_PACKS.md) for the shape and the install contract.

## Licensing

Pack content in this repository is licensed under
[**CC BY-SA 4.0**](LICENSE) (Creative Commons Attribution-ShareAlike).

Two important qualifications:

1. **The law itself is not ours to license.** Statutes, ordinances, charters,
   and other edicts of government are in the public domain (*Veeck v. SBCCI*,
   293 F.3d 791 (5th Cir. 2002) (en banc); *Georgia v. Public.Resource.Org*,
   590 U.S. 255 (2020)). The verbatim legal text inside a pack may be copied
   freely by anyone, from any source. CC BY-SA applies to what we authored:
   the selection and arrangement, citation taxonomies, alias and equivalence
   mappings, chapter overviews, personas, charters, and other editorial
   apparatus.
2. **Attribution** for the authored apparatus: "OpenContracts Authority Packs,
   Open-Source-Legal" with a link back to this repository satisfies the BY
   requirement.

The OpenContracts platform itself remains MIT-licensed; packs are data loaded
at runtime and impose no licensing obligation on the platform or on
deployments' own documents.

## Contributing a pack

Open a PR — the template walks through provenance, licensing, and validation.
CI runs `scripts/validate_pack.py` (a dependency-light structural mirror of the
OpenContracts preflight) against every pack on every PR; run it locally first:

```bash
pip install pyyaml
python scripts/validate_pack.py <pack_name>     # or --all
```

The canonical validator remains OpenContracts' own preflight
(`manage.py load_authority_pack --check`); run it before shipping a pack to a
real deployment.

## Authoring new packs

See the OpenContracts guide:
[`docs/guides/authoring-authority-packs.md`](https://github.com/Open-Source-Legal/OpenContracts/blob/main/docs/guides/authoring-authority-packs.md).
The in-tree `bolivia` pack and `example_utility` test fixture remain the
minimal worked examples; packs here are the real-jurisdiction catalog.
