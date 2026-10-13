# AMB FX preparation and validation handoff

## Roles

- **Claude — Preparer:** research, source verification, calculations, editorial review, rendering, and staging only.
- **Codex — Validator/Publisher:** independent source checks, arithmetic and visual QA, corrections where needed, production publication, live verification, and social publication.
- Claude must not merge to `main`, deploy the website, or publish to social media.

## Timetable (WAT / Africa-Lagos)

| Edition | Claude staged by | Codex pickup |
|---|---:|---:|
| Early Look | 06:30, Monday-Friday | 07:00 |
| Flagship Board | 12:00, Monday-Friday | 12:30 |

## Staging location

Repository: `amanaFTX/africa-money-brief`  
Branch: `staging/claude-fx`

Before each preparation, synchronize the staging branch with current `main`. Commit only the day's prepared package and handoff note.

Required files:

- Early Look source: `data/fx/early-YYYY-MM-DD.json`
- Early Look image: `assets/social/AMB_FX_Early_Look_YYYY-MM-DD.png`
- Early Look text: `assets/social/AMB_FX_Early_Look_YYYY-MM-DD.txt`
- Flagship source: `data/fx/YYYY-MM-DD.json`
- Flagship image: `assets/social/AMB_FX_Flagship_YYYY-MM-DD.png`
- Flagship text: `assets/social/AMB_FX_Flagship_YYYY-MM-DD.txt`
- Handoff note: `handoff/fx/YYYY-MM-DD-early.md` or `handoff/fx/YYYY-MM-DD-flagship.md`

Commit subject:

- `PREPARED Early Look YYYY-MM-DD`
- `PREPARED Flagship YYYY-MM-DD`

The handoff note must record the commit SHA, verification timestamp in WAT, official-source URLs/effective dates, calculations, carried-forward values and reasons, unresolved issues, render/test results, and a clear `PREPARED — NOT PUBLISHED` status. Because this repository is public, record Nigeria parallel observations as anonymized Source A/Source B quotes and timestamps; do not place parallel-provider names or URLs anywhere in the repository.

## Data and editorial controls

- Cover Nigeria, Ghana, Kenya, South Africa, and Egypt.
- Use official/primary sources for benchmark rates where available.
- Corroborate Nigeria parallel buy/sell observations with multiple reasonably current independent sources.
- Recompute and document the parallel midpoint and official-versus-parallel USD premium.
- When a parallel range exceeds the renderer threshold, include at least two corroborating observations plus a written `range_flag_reason`; never use the acknowledgement flag as an unexplained bypass.
- Public attribution for aggregated Nigeria parallel observations remains: “Aggregated from multiple independent market sources.”
- Label effective dates and whether a value is early trade, current observation, prior close, or latest available benchmark.
- Never fabricate, silently carry forward, or describe a prior-session figure as live.
- Use one final dataset for the website, image, and social text.
- Preserve the approved 13 October Flagship image format and the substantive country-by-country social text structure.

## Validator release rule

Codex independently checks the staged package. If it passes, Codex approves and publishes. If it fails, Codex corrects the data and all affected outputs, reruns QA, and then publishes. Website publication and live-page verification come before social publication. A release is not reported as **Published** until the live website and social post are both verified.
