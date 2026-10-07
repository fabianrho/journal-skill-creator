![Journal Skill Creator — Journal guidelines. Reusable writing skills.](docs/assets/banner.gif)

Create a reusable writing and manuscript-review skill for any academic journal, grounded in its official author instructions and writing conventions.

The creator produces a separate journal skill with sources, article-type requirements, writing guidance, a scientific review rubric, paragraph scores and a review dashboard. It distinguishes explicit journal rules from conventions, records unavailable evidence and avoids invented study results or citations.

## Install

Download this repository using GitHub's **Code → Download ZIP**, then extract it. The skill folder is `skills/journal-skill-creator`; copy the entire folder, including its supporting files.

### Codex

Ask Codex:

```text
$skill-installer install the skill from https://github.com/fabianrho/journal-skill-creator/tree/main/skills/journal-skill-creator
```

For manual installation, copy `skills/journal-skill-creator` into `~/.agents/skills/`. Restart Codex if the skill does not appear.

Example:

```text
Use $journal-skill-creator to create a writing skill for European Radiology,
focusing on Original Research. Research the current official author instructions
and record inaccessible sources or unresolved requirements.
```

### Claude Code

Copy `skills/journal-skill-creator` into `~/.claude/skills/` for personal use, or into `.claude/skills/` inside a project to share it with that project. Start a new session and run:

```text
/journal-skill-creator Create a writing skill for European Radiology,
focusing on Original Research. Save the resulting skill in .claude/skills/.
Research the current official author instructions and record source limitations.
```

### Claude Desktop

Download `journal-skill-creator.zip` from the repository's Releases page once published. In Claude, open **Customize → Skills → + → Create skill → Upload a skill**, upload the ZIP and enable it. Code execution must be available and enabled.

Example:

```text
Use journal-skill-creator to create a writing skill for European Radiology,
focusing on Original Research. Package the resulting skill as a downloadable ZIP.
Provide dashboards as standalone HTML files or HTML artifacts when supported.
```

## Capabilities and dependencies

- Creating or refreshing a journal skill needs web access to the official sources. Unavailable sources must be recorded.
- Generated skills work offline. Each one bundles the official pages in `references/sources/`, verbatim where the publisher's terms allow, with URL, access date, capture method and completeness. The index quotes the original sentence of every limit and mandatory rule. Generated skills use these bundled rules by default and browse only when asked to refresh them. Every output that relies on journal rules states the access date, for example *Requirements accessed 2026-10-07 (bundled)*.
- The instructions and Markdown review fallback use the shared Agent Skills format. Other agents can read the skill if they support that format and the required research/file tools.
- A separate skill-creator helper is optional. The included generated-skill contract specifies the required output resources; the entrypoint makes helper validation conditional on availability.
- `agents/openai.yaml` provides optional Codex UI metadata.
- The dashboard renderer uses Python 3 and its standard library. It produces a complete HTML file with bundled CSS and tab controls, usable offline in a browser. Claude can deliver the file or display it as an HTML artifact where supported. Optional OpenAI selection-state integration is not required. Browser behavior is tested; execution inside Claude itself has not been tested.
- This package creates journal skills. Journal rules are researched when it runs; the creator itself does not bundle a rule set for every journal.

## Package contents

```text
skills/journal-skill-creator/
├── SKILL.md
├── LICENSE
├── agents/openai.yaml
├── references/generated-skill-contract.md
├── assets/review/
│   ├── critical-review.md
│   ├── paragraph-readiness.md
│   ├── review-dashboard.md
│   ├── dashboard-data.md
│   └── dashboard-template.html
└── scripts/render_review_dashboard.py
```

Some links in the review templates refer to `journal-requirements.md` and `writing-style.md`. Those files are authored for each target journal when generating a skill. The creator explicitly requires adapting template links to their generated destination.

## Publishing and updates

1. Create a GitHub repository named `journal-skill-creator` (or another name).
2. Upload the contents of this source package to its root: README, LICENSE, .gitignore, docs/ and skills/. Keep the skill folder intact.
3. Replace OWNER/REPO in the installation example with the actual repository details; adjust `main` if using a different branch.
4. Create a release, such as `v0.1.0`, and attach the separately supplied `journal-skill-creator.zip` for Claude chat users.
5. Share the repository URL. For updates, publish a new release ZIP; manually copied or uploaded skills need reinstalling/re-uploading.

Do not upload the source-package ZIP as the Claude skill: use the dedicated skill ZIP whose top-level folder is `journal-skill-creator/`.

## Documentation

- [Agent Skills specification](https://agentskills.io/specification)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Skills in Claude](https://support.claude.com/en/articles/12512180-use-skills-in-claude)

## License

MIT. See [LICENSE](LICENSE). Journal websites, articles and other external sources retain their own terms.
