---
name: journal-skill-creator
license: MIT
description: Create or refresh a dedicated academic writing and manuscript review skill for a named journal, grounded in its official author instructions and observed language conventions, with paragraph scoring and actionable visual review dashboards. Use when the user wants a reusable journal skill; ordinary manuscript editing belongs to the resulting journal skill.
---

# Journal skill creator

Create a self-contained `<journal-slug>-writing` skill that helps outline, draft, revise, check, and respond to reviewers for the specified journal. Use an existing journal skill as a structural reference when supplied; derive the new journal's rules and disciplinary voice from its own sources.

## Resolve the target

Infer the exact journal, publisher, intended article type, and output location from the request. Ask for the journal if absent; disambiguate sister journals or ambiguous abbreviations before researching. Default to original research when the journal publishes it, otherwise select a supported type and state the choice. Scope additional article types to the request and available instructions.

Use the available skill-creator workflow for file structure, UI metadata, installation, and validation. Default to the configured personal skills directory. Inspect an existing destination before editing it; preserve author customizations and unrelated files. Work in a temporary staging directory when installation needs filesystem permission, then request that permission for the concrete reviewed files.

## Research requirements and language

Browse the journal's current official author instructions, complete relevant article-type sections, submission-file guidance, templates, and applicable linked publisher policies. Search snippets and third-party summaries are discovery aids. Record source URL, title/section, access date, article type, submission stage, and whether each instruction is mandatory, recommended, or illustrative. Preserve conditions, exceptions, counting rules, and conflicting statements. Specific article-type guidance usually governs that type; report unresolved conflicts rather than inventing a reconciliation.

Build a compact source index covering relevant structure and limits, language/style, references, tables/figures/supplements, declarations, reporting guidelines, and submission/revision requirements. Check applicable policies such as ethics, authorship, data/code availability, registration, and AI assistance. Mark inaccessible, unspecified, or unchecked items explicitly; they are different from verified absence of a requirement. Link substantial official guidance instead of copying entire manuals. Keep permitted focused extracts or dated snapshots when needed for reliable offline use, identifying their coverage and omissions; retain official templates when relevant and accessible.

Inspect a small sample of accessible recent articles of the relevant type and, where possible, field. Record which articles and which portions were inspected. Derive useful conventions for argument structure, audience, terminology, English variant, sentence style, and treatment of uncertainty. Label these as observed tendencies, separate from explicit editorial rules and general writing advice. Published examples can reflect exceptions or older policies. Do not infer full-manuscript style from abstracts alone, copy distinctive wording, or turn limited observations into mandatory rules. If examples are unavailable, record the limitation and use neutral disciplinary prose.

## Build the journal skill

For a targeted review-standard update, inspect the existing skill and preserve its dated journal sources; do not imply those sources were refreshed. Apply the changes to the creator templates and requested installed journal skills, retaining each journal's customizations.

Read [the generated-skill contract](references/generated-skill-contract.md) while authoring. Produce a concise `SKILL.md`, `references/journal-requirements.md`, `references/writing-style.md`, `references/paragraph-readiness.md`, and `references/review-dashboard.md`. Read and install a self-contained adaptation of [critical-review.md](assets/review/critical-review.md) in the generated skill's references, and require it before substantive review and scoring. It defines the scientific argument checks, full-credit standard and handling of earlier generous assessments. Read and adapt the bundled [scoring template](assets/review/paragraph-readiness.md) and [dashboard template](assets/review/review-dashboard.md) into the generated skill's references. Their sibling links resolve in that destination, alongside its journal requirements and writing style. Also install `assets/review/dashboard-template.html`, `assets/review/dashboard-data.md` and `scripts/render_review_dashboard.py` as complete local copies. Require their use in the generated entrypoint and dashboard reference; fix relative links for the destination. Keep other resources limited to concrete workflows. Embed the selected journal identity, supported article types, and relevant reading routes. The resulting skill must work without this creator, the example skill, or private workspace paths.

Default substantive author-side reviews to paragraph scores out of 10 and an interactive dashboard with explanations, evidence status, and prioritised actions. Specify three overview boxes—editorial assessment, length, and revision focus—above the selectable C/E/J/F/L paragraph scorecard, following the bundled dashboard template. Honour text-only requests; drafting and narrow checks do not trigger scoring. Preserve the scoring rubric's uncertainty and blocker rules. Derive paragraph requirements and style judgements from the target journal and article type; never transfer another journal's limits, section names, or conventions. When inline visualization is unavailable, deliver the standalone HTML file; use a complete text scorecard when HTML delivery is unavailable.

Keep cross-journal scientific safeguards while adapting the audience: evidence provenance, no invented results or references, planned versus performed methods, consistent denominators, and conclusions bounded by the design and findings. Radiology terminology and clinical-outcome cautions belong only where relevant. Respect the manuscript's scope, terminology, citation system, format, and applicable workspace instructions.


## Preserve the approved review layout

Every substantive scored review uses the fixed design in the local dashboard guidance: three top boxes (**Editorial assessment / Length / Revision focus**), then **Paragraphs / Actions / Sources** tabs with per-paragraph C/E/J/F/L scores, selectable details, prioritized actions and traceable sources. Populate [the bundled HTML template](assets/review/dashboard-template.html) using [the data contract](assets/review/dashboard-data.md) and [renderer](scripts/render_review_dashboard.py); preserve its shell rather than redesigning each review. This applies to new reviews and updates unless the user explicitly requests a different layout or format. Keep unverified states in the same boxes and tables. Text-only requests, unavailable interactive surfaces, narrow edits and applicable assigned-review conditions retain their documented exceptions.

## Verify and deliver

Run the skill-creator validator if available. Inspect every local reference link, frontmatter, source attribution, unresolved scaffold value, and description for accidental targeting of another journal. Check that the source index preserves qualifications and that the generated skill requires relevant full-source reading rather than treating the index as exhaustive.

Test scientific calibration with fluent but incomplete rationale, unsupported component attribution, a defensible hypothesis, and pressure to award 10/10. Check that full marks remain attainable and uncertainty is not mistaken for a flaw. Exercise realistic scenarios: a narrow prose edit, an unsupported results claim, an alternative article type, and a submission audit with a missing or conflicting source. Also exercise a scored section review with an unverified source, a text-only review, and an unavailable visualization surface. Verify scope preservation, score/interval calculations, actionable paragraph details, and honest compliance status. Use an independent behavioral pass when useful and authorized; report the extent of testing without calling a structural validator proof of behavior.

If essential sources remain inaccessible, a usable skill may be delivered provisionally with those gaps prominently recorded; do not label its coverage complete. If the journal identity itself is unresolved, obtain clarification before installing a journal-specific skill.

Install the completed skill and report its name, path, example invocation, source verification date, and material coverage gaps. Creating a skill does not itself establish manuscript compliance or authorize submission.

## Portable dashboard delivery

The bundled renderer produces a complete standalone HTML document with local CSS and tab controls. Use an HTML artifact in Claude when supported, or deliver the downloadable HTML file. Open the file in a browser for preview. A Codex visualization plugin is optional; adapt to a fragment only if an inline surface requires it. Preserve the three overview boxes and Paragraphs / Actions / Sources tabs. Use the complete text fallback when requested or when HTML delivery is unavailable.
