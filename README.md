# Plone security.txt

A Plone addon to generate and provide a security.txt for the Plone website.

## Features

- One site-wide, structured Security Policy with draft and published lifecycle states
- Deterministic RFC 9116 output at `/.well-known/security.txt`
- Anonymous GET/HEAD, strong ETags, Canonical enforcement, and expiry-bounded caching
- Dedicated management permission, Classic UI control panel, REST API, and expiry warning
- Optional fail-closed OpenPGP clear-signing via the `signing` extra
- Compatible with Plone 6.0+

See the [administrator guide](docs/security-policy.md), [REST API](docs/rest-api.md),
[deployment guide](docs/deployment.md), and [signing guide](docs/signing.md).

## Installation

Add `plone.securitytxt` to your project's dependencies:

```python
# In your pyproject.toml
dependencies = [
    "plone.securitytxt",
    # ...
]
```

Then activate the addon in your Plone site's control panel or via GenericSetup.

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/collective/plone.securitytxt.git
cd plone.securitytxt

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
uv sync --extra test
```

### Running Tests

```bash
uv run pytest
```

### Running Tests with Coverage

```bash
uv run pytest --cov=plone.securitytxt --cov-report=html
```

## License

GPL-2.0-or-later

## Author

Maik Derstappen <md@derico.de>
