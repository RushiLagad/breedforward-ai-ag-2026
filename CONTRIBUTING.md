# Contributing

## Public contribution workflow

Fork the repository, create a focused branch, push the branch to your fork, and open a pull request. Public visibility allows access and forking but does not grant direct push permission to the main repository.


## Branches

Use short, descriptive names such as `eda`, `feature-weather`, `baseline-rf`, or `pitch-figures`.

## Commits

Keep commits focused and write messages in the imperative, for example: `Add baseline model` or `Document missing-value rules`.

## Pull requests

Summarize the decision supported by the change, not only the files changed. Include evidence, limitations, and reproduction steps. One teammate should review code or claims before merge when time permits.

## Reproducibility

- Set random seeds.
- Record data versions and preprocessing decisions.
- Move repeated notebook logic into `src/`.
- Save generated figures in `assets/` only when permitted.
- Add a lightweight test for critical transformations or metrics.

## Data safety

Never commit raw sponsor data, credentials, or personally identifiable information. If redistribution permission is unclear, treat the data as private.
