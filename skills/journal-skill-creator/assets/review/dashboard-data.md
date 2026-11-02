# Assessment data for the fixed review layout

Read the local critical-review and paragraph-readiness references before assigning ratings. The HTML asset is the approved presentation shell; the assessment JSON contains manuscript-specific content only. Use plain text in every field. Do not insert HTML into the data or copy example paper findings into a new review.

Generate the standalone HTML file and its annotated PDF with the bundled script (replace paths with the actual skill, JSON and authorized output paths):

```sh
python3 <skill-directory>/scripts/render_review_dashboard.py <assessment.json> <review-dashboard.html>
```

The script reads `assets/review/dashboard-template.html`, validates required fields and safely embeds the data. It also writes `<name>-annotated.pdf` beside the HTML file and embeds the same PDF for the dashboard's **Export annotated PDF** button. It prints both paths and warns about any character the PDF fonts cannot draw; such characters appear as "?" in the PDF text, while comments keep the original. Same input gives byte-identical output. It does not assign ratings, verify sources, infer limits or rewrite the manuscript. The output bundles its CSS and tab controls and opens directly in a browser without network access or a host runtime. In Claude, present it as an HTML artifact when supported, or provide the HTML file for download. When publishing the dashboard as a Claude artifact, declare the downloads capability on the first publish (Artifact tool: `capabilities: {downloads: true}`). Without it, Claude blocks the Export annotated PDF button with "file downloads aren't available for this artifact". On later republishes of the same artifact, omit `capabilities` so the stored declaration carries over; if an earlier version was published without it, republish once with `capabilities: {downloads: true}`. Declare nothing else. The button saves through that capability inside Claude and uses a normal browser download when the HTML file is opened directly. In Codex, open it in the available browser preview; adapt it to an inline surface only when that surface requires a fragment. Optional OpenAI state APIs are not required for interaction. Keep the template and renderer together when installing or sharing this skill.

## Root object

| Field | Value |
|---|---|
| `reviewId` | Unique review/version identifier, used to restore compatible selection state. |
| `title`, `journal`, `articleType`, `scope`, `version`, `reviewDate` | Explicit identity and reviewed scope; date in YYYY-MM-DD. |
| `requirementsAccess` | Where the journal rules came from and when, shown in the header, e.g. `Requirements accessed 2026-10-07 (bundled)` or `Requirements accessed 2026-11-02 (refreshed this session)`. Use the oldest access date among the captures relied on. |
| `editorial` | `{score, reason, status}`. Score is a separate qualitative 0–10 assessment or `null` with a reason. Status keeps scientific blockers and incomplete review visible. |
| `length` | `{count, limit, limitStatus, scope, exclusions, source, method}`. Count is a measured nonnegative integer or `null`. Limit is a verified positive integer or `null`. `limitStatus` is `verified`, `unverified` or `none`. State the applicable source/section, counting method and exclusions. No known count means no progress indicator. |
| `focus` | `{ids, action, status, workType}`. Ordered array of priority paragraph IDs from `paragraphs`; first ID is initially selected. Use an empty array only when no material revision is identified, and explain the scope. |
| `paragraphs` | Array of paragraph objects below, in manuscript order. Preserve IDs and boundaries on updates. |
| `actions` | Prioritized array of `{title, location, workType, action, completeWhen, evidenceBoundary}`. The fixed labels in the Actions tab are Action, Complete when, Evidence boundary. |
| `coverage` | Array of `[label, text]` pairs covering assessed material, evidence scope, unavailable material, interpretation and preserved boundaries as applicable. |
| `checks` | Array of `{check, observed, status}` for section limits and cross-section consistency. Use explicit unchecked status when necessary. |
| `sources` | Array of `{id, basis, title, url, location, access, limitations}`. URL is an inspected http(s) link or `null`; location identifies the local capture file and sections; access identifies date and checked/unavailable status. Preserve requirement/recommendation/observed-style/editorial-judgement/study-evidence distinctions. Every cited short source ID must resolve here. |

## Paragraph object

- `id`, `section`, `sectionCode`, `location`, `opening`, `purpose`: stable label, actual section name, its fixed section code, manuscript pointer, short opening phrase and paragraph role. Take the code from the section-code table in the local paragraph-readiness reference; the ID is that code, a space, then P and the paragraph's number in its section (`R P2`, `SRS P3`). Each section has one code, and no two sections share one. The section selector shows `R · Results` and `SRS · Segmentation Reference Standard`. `All paragraphs` is reserved for the combined view.
- `r`: exactly five ratings in C/E/J/F/L order; each is an integer 0–4, `"U"` or `"N/A"`. The renderer computes totals and coverage; do not supply a manual score.
- `reasons`: object with `C`, `E`, `J`, `F`, `L` strings. Explain each rating, every unknown/exclusion, and why a higher anchor is not met. Include the basis and source IDs/location. Full credit requires positive assessment against the scientific checks; it is not an automatic default.
- `action`, `workType`, `evidenceNeeded`, `improveWhen`: smallest useful action, type of work, material needed and conditions for reassessment. Identify prose, source, record or analysis work. Do not promise score gains.
- `segments`: the paragraph's full text as ordered highlighted spans, following **Sentence highlights** in the local paragraph-readiness reference. Each span is `{text, rating, dims, comment, suggestion}`: verbatim text; rating as an integer 0–4 or `"U"`; dims as an array of C/E/J/F/L letters, empty only for rating 4; a comment for every span; an optional suggested replacement. Concatenated span texts must reproduce the paragraph and start with `opening`. The renderer rejects spans rated below the cited paragraph dimensions, sub-4 or U dimensions with no citing span, and spans that cite an N/A dimension.
- `blocker`: optional string describing a demonstrated blocker, otherwise empty/omitted. Missing access alone is not a blocker.
- `provisional`: optional string explaining incomplete contextual verification, or a relevant rule genuinely missing from the bundled captures, even when all numeric ratings are available; otherwise empty/omitted. Bundled dated rules count as verified and do not make a paragraph provisional.

All required text fields must explain their state. Use explicit “None within this scope”, “Not checked” or “Unavailable” with the relevant explanation instead of a blank. Unknown and unavailable material must not be filled with invented facts. An entirely unassessed paragraph displays Not assessed and 0% coverage; N/A weights are excluded, U weights retained. Empty action/check lists display explicit scope statements, so only leave them empty after assessment supports that state.

## Delivery check

Check exactly three overview cards and the Paragraphs / Actions / Sources tabs, selection and disclosures, source pointers, and the numeric outputs against the local rubric. Confirm the section selector shows codes, a click anywhere on a row selects it, the Sentence highlights panel matches the paragraph, and the Export button downloads the PDF. Open the PDF and confirm one highlight per span (a span that crosses a page break gets one per page), one margin note per paragraph, and readable comments. Test 736px and 320px widths and light/dark appearance. The initial detail should match the focus; tab changes retain the overview cards. When maintaining the template, test complete scores, U intervals, N/A normalization, all-U/no-assessable cases, a demonstrated blocker, numeric-but-provisional ratings and an unverified word limit. Do not deliver synthetic calibration data as a manuscript review.
