# AI Safety Assessments

Evidence-graded assessment of AI safety developments.

This repository holds the published weekly issues and the tools that build
the site. The site is built from this repository and
published at <https://ai-safety-assessments.github.io>.

## What this is

An assessment product, not an aggregator. Other publications answer *what
happened*. This one answers *how much of it should you believe, and what would
change that*. Each issue carries:

- claim-level credibility ratings, with the reasoning shown (adapted Admiralty
  codes, categorical only, never scored arithmetically);
- origin maps, so a figure that is widely reported but traces back to a single
  source is visible as such;
- falsifiable judgments — a claim, a PHIA yardstick term, a deadline and a
  named audience;
- a public track record: every published judgment is registered with a deadline
  and scored when it resolves.

## What is deliberately not here

Analyst notes are kept in a separate, private repository. They hold the
bookkeeping that would clutter or prejudice the published text: per-judgment
worksheets, blinded second ratings and their reconciliation, resolution
procedures, verification records, collection gaps and drafting notes. The
per-area and per-story working notes live there too.

The split is deliberate and stated here so it is not mistaken for selective
publication. Each evidence row publishes the source with a link, what the
source says, and the rating with its basis, so each claim can be checked against
its source without the notes.

## Layout

```
reports/    weekly issues
tools/      builders and checks
assets/     stylesheets
```

## Licence

Content (`reports/`, `about.md`):
CC BY 4.0 — see `LICENSE`.
Code (`tools/`, `.github/`): MIT — see `LICENSE-tools`.

## Citing

See `CITATION.cff`, or cite an issue by its number and date.
