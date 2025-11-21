# GitHub Copilot – Repo Context

This repository uses:

- Conventional Commits (type(scope): subject)
- Critical domains: payment-gateway, future auth services
- Simple risk scoring based on semantic type and path criticality

When suggesting commit messages:

- Always follow Conventional Commits format
- Prefer scopes like `payment`, `auth`, `infra`, `docs`
- In commit bodies, briefly note business impact and tests

When editing policies or risk scoring:

- Preserve comments explaining "why", not just "what"
- Assume this repo is a teaching/demo asset for enterprise platform teams
