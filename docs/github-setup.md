# GitHub collaboration

This repository is public so teammates can view it, fork it, and submit pull requests. Public visibility does not grant direct push access to the main repository.

## Fork and contribute

```bash
gh repo fork RushiLagad/breedforward-ai-ag-2026 --clone
cd breedforward-ai-ag-2026
git checkout -b <short-feature-name>
# Make and test changes
git add .
git commit -m "<describe the change>"
git push -u origin <short-feature-name>
gh pr create
```

A maintainer can review and merge the pull request. Team members who need direct branch access should send the owner their exact GitHub usernames for individual collaborator invitations.

## Recommended GitHub settings

- Protect `main` if the rapid workflow permits it.
- Enable Issues and use the included task template.
- Require secret scanning and block pushes containing secrets when those controls are available.
- Never commit organizer- or sponsor-provided data unless redistribution is explicitly permitted.
- Keep raw challenge data, credentials, and personal information out of Git.
