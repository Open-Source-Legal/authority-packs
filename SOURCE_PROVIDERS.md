# Source providers in a pack

A pack may ship the code that fetches its own authority text, under
`<pack>/providers/`. The platform discovers it from the pack directory — no
registration call, no core edit — so copying the pack to another install brings
its scraper with it.

No pack ships one yet. This contract exists so that the first one is reviewable
against something.

## Why a pack would ship one

A pack already records **where its text came from**: `source_hosts` in
`pack.yaml`, and a `source_url` on every section. Neither says how to obtain a
section *by key*, so nothing in an install can re-fetch `itar:120.4`. The
harvesters that built the pack live in a separate workspace and are not shipped.

A source provider closes that: given a canonical key, produce a fetch plan
(`locate`) and then the bytes (`fetch`).

## The delegation rule — read this before writing a scraper

**Most packs must not write one.** The platform already ships providers for the
Code of Federal Regulations, the U.S. Code and the Federal Register. They fail
to fire for a pack only because of key SHAPE: the CFR provider accepts
`cfr-{digits}:` and a pack's sections are keyed `itar:`, `ear:`, `aeca:`.

A pack already declares that translation, in its own mappings:

```yaml
- from_key: cfr-22:120
  to_key: itar:120
```

So the provider is a key translator plus a delegation, not a scraper:

    itar:120.4 ─(invert the pack's own equivalence rows)→ cfr-22:120.4 ─(delegate)→ core CFR provider

Write a real scraper only for a publisher core does not cover.

**Inversion is many-to-one and MUST be disambiguated.** `itar:120` is the target
of `cfr-22:120`, `act:22-cfr-120`, `act:part-120-of-the-itar` and others. Invert
only rows whose `from_key` prefix matches `^(cfr|usc)-\d+$`, and FAIL when more
than one survives. Choosing silently fetches the wrong title and looks fine.

## The contract

**P1 — A provider claims only prefixes its own pack owns.** `supported_prefixes`
MUST be a subset of the pack's `authority_prefixes`. Two providers claiming one
prefix resolve by priority then discovery order — the platform warns, this
contract forbids.

**P2 — Every host a provider reaches is in `source_hosts`.** The SSRF allowlist
is built from `source_hosts`. A provider fetching elsewhere either fails at
runtime or becomes the reason someone widens the allowlist.

**P3 — `locate()` is pure.** No I/O. The locate/fetch split exists so a fetch
plan can be inspected and tested without a network.

**P4 — No network, no database, no settings access at import time.** The
registry imports every provider module when it builds. A module that acts on
import stalls startup and cannot be audited by reading it.

**P5 — The provider is OPTIONAL to the pack's value.** The pack MUST install and
serve its text with `providers/` deleted. A pack whose sections only resolve
through its scraper is not a pack.

**P6 — The declaration matches the implementation.** The `providers:` block in
`pack.yaml` MUST agree with the class's `supported_prefixes` and `priority`.

## File shape

```
<pack>/
  pack.yaml
  providers/
    <name>_provider.py          # BaseAuthoritySourceProvider subclass
  discovery_providers/
    <name>.py                   # BaseAuthorityDiscoveryProvider, for listing crawls
```

Declared in `pack.yaml`:

```yaml
providers:
  - module: providers/cfr_delegating_provider.py
    class: ITARCFRSourceProvider
    kind: source                  # source | discovery
    supported_prefixes: [itar]
    delegates_to: CFRAuthoritySourceProvider   # omit for a real scraper
    fetches_hosts: [www.ecfr.gov]              # subset of source_hosts (P2)
```

The block is **descriptive, not load-bearing**: discovery is by directory, so a
pack declaring it still installs on a platform that ignores it. Its job is to
let the validator check the code against the declaration, and to let a reviewer
see what a pack will execute without reading Python.

## What this means for whoever installs the pack

**Installing a pack that ships `providers/` runs its Python in the web and
worker processes.** That is a larger blast radius than `source_hosts`, where
"installing the pack is the trust decision" holds because the consequence is
only which hosts may be fetched.

Consequences for this repository:

- A pull request adding or changing `providers/**` requires a human read of the
  Python. Green CI is not sufficient.
- P4 is the line that makes that read tractable: a module that only defines a
  class is auditable; one that acts on import is not.
- An operator who will not execute pack code can disable provider loading and
  lose only refresh, because of P5.

## Validation

`scripts/validate_pack.py` checks the contract **statically**, by parsing the
source. It MUST NOT import a pack's provider to validate it — CI does not
execute pack code.

Checked: declared modules exist; declared classes are defined there and subclass
the right base; `supported_prefixes` ⊆ `authority_prefixes` (P1, P6);
`fetches_hosts` ⊆ `source_hosts` (P2); no module-level network or environment
access (P4).

Not checkable statically, and therefore a reviewer's job: P3 and P5.

`--self-test` MUST carry a fixture that fails each check, per this repo's rule
that a validator is only trusted once it has been shown able to fail.
