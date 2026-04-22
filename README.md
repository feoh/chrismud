# Plurludanta

Plurludanta, "multiplayer game" in Esperanto, is a Python project for building simple multiplayer games on top of FastAPI.

For implementation details, API structure, data model notes, and a technical design review, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Overview

The project currently provides:

- A FastAPI-based game server
- A text-based command line client
- A small seeded world for local development
- Automated tests for the current REST gameplay flows

## Usage

### Running the Server

```bash
uv sync
uv run fastapi dev plurludanta.py
uv run python plurludanta.py
```

The last command initializes the sample world database.

### Running the Client

```bash
uv run python client.py --register
uv run python client.py
```

### Client Commands

- `look` or `l`
- `go <exit>`
- `take <item>`
- `drop <item>`
- `inventory` or `i`
- `say <message>`
- `who`
- `quit`

## Tests

```bash
uv run pytest -v
```
