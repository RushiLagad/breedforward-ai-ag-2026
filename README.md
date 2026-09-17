<p align="center">
  <img src="assets/breedforward-logo-white.png" alt="BreedForward logo" width="520">
</p>

# BreedForward

**Grounded in data. Breeding for the future.**

A collaboration repository for the University of Arkansas AI in Ag Hackathon, held September 18–20, 2026. Top teams present at the AI in Agriculture Symposium on September 21.

## Identity

BreedForward represents the use of AI, statistics, and agricultural knowledge to make better breeding decisions for the next generation. The logo combines a DNA helix, data nodes, a growing plant, and a forward arrow.

See [docs/branding.md](docs/branding.md) for the current logo files and usage notes.

## Team

- Ajaydeep Bedi
- Renuka Khanal
- Sambhavi Patel
- Rushikesh Lagad
- Elias Zakaria Mohellebi
- Soni Pinjala

Skills, roles, and contact preferences can be added in [TEAM.md](TEAM.md).

## Event

- Hackathon: September 18–20, 2026
- Location: David W. Mullins Library, University of Arkansas
- Symposium: September 21, 2026, Don Tyson Center for Agricultural Sciences
- [Official event page](https://aaes.uada.edu/events/ai-in-agri-symposium-2026/)

## Quick start

```bash
git clone <repository-url>
cd breedforward-ai-ag-2026
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Suggested workflow

1. Record the challenge and judging criteria in [docs/challenge-brief.md](docs/challenge-brief.md).
2. Create one GitHub issue per task and assign one owner.
3. Work in short branches such as `eda`, `baseline-model`, or `pitch`.
4. Keep raw data out of Git; save only permitted, reproducible outputs.
5. Merge through small pull requests so changes are easy to review.
6. Update [docs/pitch-outline.md](docs/pitch-outline.md) as evidence develops.

## Repository map

| Path | Purpose |
| --- | --- |
| `data/` | Instructions for local data; raw files are ignored |
| `notebooks/` | Exploration and experiments |
| `src/` | Reusable analysis and modeling code |
| `tests/` | Checks for reusable code and data assumptions |
| `assets/` | Logo files, approved figures, diagrams, and presentation assets |
| `docs/` | Challenge brief, branding, decisions, and pitch plan |

See [docs/github-setup.md](docs/github-setup.md) for safe publication steps.

## Data and IP guardrails

- Keep organizer- or sponsor-provided data private unless the rules explicitly permit redistribution.
- Do not commit credentials, tokens, personal data, or large raw datasets.
- Record the source and license for every external dataset.
- Confirm event and sponsor IP terms before adding an open-source license or making the repository public.

No software license is included yet for that reason.
