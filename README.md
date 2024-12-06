# Meraki Configuration Tools

A toolkit for parsing, validating, and managing Meraki configuration files. This project provides tools to work with Meraki config files and compile them to Karabiner-Elements configurations.

## Features (In Development)

- Parse Meraki config files into AST
- Validate configurations for errors and inconsistencies
- Lint configurations for style and best practices
- Format config files for consistent styling
- Compile to Karabiner-Elements TypeScript DSL

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd meraki
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Development

To run tests:

```bash
pytest tests/
```

## License

MIT 