# Provenance and non-repudiation

This archive exists so that a skeptic who does not trust us can still verify the
benchmark. Two separate claims have to hold, and they need different evidence.

## Claim A: we predicted before the outcome (no backdating)

The whole point of a *prospective* benchmark is that the prediction existed before the
fire. Our defense is the public commit history of this repository.

- Each day's forecast is committed by an automated workflow the day it is served.
- The **forward forecast** (`forecast24h-*.json`) is the cleanest evidence: it predicts
  tomorrow and is committed today, so the commit provably predates the day it forecasts.
- The fire truth for a given day arrives several days later (FIRMS near-real-time and
  ICNF records need time to settle), so it is committed *after* the prediction it will be
  scored against. That ordering is visible to anyone reading the log.

**What git does and does not prove.** The trustworthy signal is the **push timestamp**,
which GitHub records server-side. The per-commit author/committer date is set by whoever
makes the commit and is worth nothing on its own. History rewrites (force-push) are
detectable and are blocked on `main` by branch protection.

**Honest limit.** A git-only design ultimately rests on trusting GitHub's recorded push
times. That is weaker than a cryptographic timestamp authority. It is public, cheap, and
defensible, and it can be strengthened later (RFC 3161 timestamp tokens, or an on-chain
timestamp of each daily commit hash) without changing anything else in this repository.

## Claim B: the official data really is theirs (no doctoring)

We archive IPMA RCM and EFFIS FWI to benchmark against them. How does anyone know we did
not quietly weaken their forecasts to flatter ours?

- We cannot cryptographically prove third-party authorship, because neither IPMA nor
  EFFIS signs their outputs. That door stays closed unless they start signing.
- What we can do is make forgery require **collusion across independent parties**:
  - The raw upstream response is preserved verbatim (the exact bytes IPMA/EWDS returned),
    not a re-typed summary.
  - The same public sources can be, and are encouraged to be, independently mirrored
    (for example via the Internet Archive), so a third party holds the same artifact for
    the same day.

This is the ordinary evidentiary standard of journalism and legal discovery: not
mathematical proof, but "to fake this you would have to corrupt several independent
records at once."

## Priority

Claim A (our own predictions are not backdated) is what the paper actually rests on, so
it gets the strongest treatment. Claim B is lower stakes: there is little to gain from
shaving an official forecast, and it is checkable against the live upstream sources.
