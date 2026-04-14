# zion — The Zion Boundary — Mapping the limits of human control over agentic AI. Adversarial robustness as humanity's last line of defense

The Zion Boundary — Mapping the limits of human control over agentic AI. Adversarial robustness as humanity's last line of defense. zion gives you a focused, inspectable implementation of that idea.

## Why zion

zion exists to make this workflow practical. The zion boundary — mapping the limits of human control over agentic ai. adversarial robustness as humanity's last line of defense. It favours a small, inspectable surface over sprawling configuration.

## Features

- CLI command `zion`
- Included test suite
- Worked examples included

## Tech Stack

- **Runtime:** Python
- **Frameworks:** Click
- **AI/ML:** NumPy, OpenAI SDK, Anthropic SDK
- **Tooling:** Rich, Pydantic

## How It Works

The codebase is organised into `examples/`, `src/`, `tests/`. The primary entry points are `src/zion/cli.py`, `src/zion/__init__.py`. `src/zion/cli.py` exposes functions like `cli`, `audit`.

## Getting Started

```bash
pip install -e .
zion --help
```

## Usage

```bash
zion --help
```

## Project Structure

```
zion/
├── .env.example
├── CONTRIBUTING.md
├── README.md
├── config.example.yaml
├── examples/
├── index.html
├── pyproject.toml
├── requirements.txt
├── src/
├── tests/
```
