# Plone security.txt

A Plone addon to generate and provide a security.txt for the Plone website.

## Features

- Compatible with Plone 6.0+

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
pip install -e ".[test]"
```

### Running Tests

```bash
pytest
```

### Running Tests with Coverage

```bash
pytest --cov=plone.securitytxt --cov-report=html
```

## License

GPL-2.0-or-later

## Author

Maik Derstappen <md@derico.de>
