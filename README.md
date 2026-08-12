# smailpro-api

Python wrapper for the [SmailPro](https://smailpro.com) temporary email service with multi-provider support and automated CAPTCHA bypassing.

[![PyPI](https://img.shields.io/pypi/v/smailpro-api)](https://pypi.org/project/smailpro-api/)
[![PyPI - License](https://img.shields.io/pypi/l/smailpro-api)](https://github.com/AsmSafone/smailpro-api/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/smailpro-api)](https://pypi.org/project/smailpro-api/)

## Installation

```bash
pip install smailpro-api
```

## Quick Start

```python
from smailpro_api import SmailProAPI, Provider

api = SmailProAPI(
    provider=Provider.GOOGLE,
    solver_url="http://localhost:9000"
)

email_info = api.create_email()
print(f"Created email: {email_info['address']}")
```

For the full usage guide, configuration options, and supported providers, see the [package README](smailpro_api/README.md).

## CAPTCHA Solver

This library requires a running CAPTCHA solver service to handle Cloudflare Turnstile challenges. The solver service can be run using Docker:

```bash
cd solver-docker
docker compose up -d
```

## Project Structure

```text
smailpro-api/
├── smailpro_api/        # Python package (published to PyPI)
│   ├── src/smailpro_api/
│   ├── pyproject.toml
│   └── README.md
├── solver-docker/       # Docker setup for the CAPTCHA solver
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── Boterdrop-Solver/
├── .github/workflows/   # CI/CD (auto-publish to PyPI on release)
└── test_package.py
```

## Automated PyPI Publishing

A GitHub Actions workflow (`.github/workflows/publish-pypi.yml`) automatically builds and publishes the package to PyPI whenever a new GitHub Release is created. To use it, add a repository secret named `PYPI_API_TOKEN` containing a PyPI API token with upload permissions.

```bash
git tag 1.0.0
git push origin 1.0.0
# Then create a release on GitHub from this tag to trigger publishing
```

## License

MIT License — see [LICENSE](LICENSE) for details.
