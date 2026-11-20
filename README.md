# RL-A2A

[![CI](https://img.shields.io/github/actions/workflow/status/KunjShah01/RL-A2A/ci.yml?branch=main)](https://github.com/KunjShah01/RL-A2A/actions)
[![PyPI](https://img.shields.io/pypi/v/rl-a2a.svg)](https://pypi.org/project/rl-a2a/)
[![Docker Pulls](https://img.shields.io/docker/pulls/your-docker-repo/rl-a2a.svg)](https://hub.docker.com/)

Reinforcement Learning Agent-to-Agent Communication Platform.

This repository contains the RL-A2A platform: API server, orchestration, learning components, and utilities.

Write-up: [Secure Multi-AI Agent Systems: The Next Generation (RL-A2A Enhanced)](https://kunjshah.in/writing/rl-a2a-enhanced-the-next-generation-of-secure-multi-ai-agent). Built by [Kunj Shah](https://kunjshah.in).

Quick links

- Docs: `./docs/`
- Run locally: `python -m main` or `rla2a start`

Releases: when a GitHub Release is published the project automatically builds and publishes a wheel to PyPI and pushes a Docker image (requires repository secrets: `PYPI_API_TOKEN`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `DOCKERHUB_REPO`).
