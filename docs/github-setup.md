# Publish to GitHub

Keep the repository private until the team confirms the event's data and intellectual-property rules.

## GitHub CLI

From the repository directory:

```bash
git init -b main
git add .
git commit -m "Set up BreedForward hackathon workspace"
gh repo create breedforward-ai-ag-2026 --private --source=. --remote=origin --push
```

## Recommended GitHub settings

- Invite only the six team members initially.
- Protect `main` if the rapid workflow permits it.
- Enable Issues and use the included task template.
- Require secret scanning and block pushes containing secrets when those controls are available.
- Do not enable GitHub Pages or make the repository public until redistribution rights are clear.
