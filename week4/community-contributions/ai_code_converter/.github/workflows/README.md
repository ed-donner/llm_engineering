# CodeXchange AI CI/CD Workflows

This directory contains GitHub Actions workflows for continuous integration and deployment of the CodeXchange AI application.

## Workflow Overview

1. **python-test.yml**: Runs Python tests, linting, and code coverage
2. **docker-build.yml**: Builds and validates Docker images with security scanning
3. **deploy-staging.yml**: Deploys to staging environment when changes are pushed to develop branch
4. **deploy-production.yml**: Deploys to production environment when a new release is published

## Required GitHub Secrets

To use these workflows, you need to set up the following secrets in your GitHub repository:

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and Variables → Actions
3. Add the following secrets:

| Secret Name | Description |
|-------------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | A personal access token from Docker Hub (not your password) |

## Getting a Docker Hub Access Token

1. Log in to [Docker Hub](https://hub.docker.com)
2. Go to Account Settings → Security
3. Create a new access token with appropriate permissions
4. Copy the token immediately (it's only shown once)
5. Add it as a GitHub secret

## Customizing Deployment

The deployment workflows currently include placeholder comments where you would add your specific deployment commands. Update these sections based on your hosting environment:

- For VPS hosting: Add SSH-based deployment steps
- For cloud providers: Add their specific deployment APIs
- For Kubernetes: Add kubectl commands or Helm chart updates

## Testing GitHub Actions Locally

You can test GitHub Actions locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act

# Run a specific workflow
act -j test -W .github/workflows/python-test.yml
```
