# Deploy and Release

## Deploying the API

1. Ensure you are on the correct branch (e.g. `main` or `release/YYYY-MM-DD`).
2. Run the deploy script from the repo root: `./scripts/deploy.sh`.
3. The script builds the Docker image, pushes to the registry, and updates the staging deployment.
4. After deploy, run the smoke tests: `pytest tests/smoke/ -v`.
5. If smoke tests pass, the release is tagged and the same image is promoted to production.

## Rollback

If a deploy causes issues:

1. Open the CI/CD pipeline and select the previous successful deployment.
2. Click "Rollback" to revert to that image.
3. Notify the team in #releases and document the incident in the runbook.

## Release checklist

- [ ] Changelog updated
- [ ] Version bumped in `pyproject.toml`
- [ ] Staging deploy verified
- [ ] Smoke tests green
- [ ] Production deploy approved
