# zion

> The Zion Boundary — a toolkit for testing the limits of human control over agentic AI. Adversarial benchmarks for instruction-following, deception detection, sandbox escape prevention.

![status](https://img.shields.io/badge/status-active_planning-blue)
![license](https://img.shields.io/badge/license-MIT-green)
![backlog](https://img.shields.io/badge/backlog-see_DESIGN.md-orange)

## What this is

As AI agents take more autonomous actions (spending money, deploying code, sending emails), safety research on 'does this agent actually do what I asked' needs production-grade benchmarks and red-team tooling — not just academic papers. Alignment evals are either proprietary (Anthropic, OAI) or fragmented across research GitHub repos.

**Read the full [DESIGN.md](./DESIGN.md)** for problem statement, user personas, architecture, and roadmap.

## Status

**Active planning / pre-alpha.** The design is scoped (see DESIGN.md). Code is minimal — this repo is the home for the first real implementation, not a placeholder.

## MVP (v0.1) — what ships first

- 5-10 well-designed instruction-injection tests
- `zion eval my_agent.py` runs suite, outputs HTML report
- Adapter pattern for agent wrappers (just needs a `run(prompt) -> response` function)
- Deterministic scoring — each test has clear pass/fail

## Stack

- Python 3.11+
- Anthropic + OpenAI + local model adapters
- Standard eval harness compatible with Inspect (UK AISI's framework)
- YAML-declared test suites
- HTML report output

See [DESIGN.md](./DESIGN.md#planned-stack) for complete stack rationale.

## Quick start

```bash
git clone https://github.com/MukundaKatta/zion.git
cd zion
# See DESIGN.md for full architecture
```


## Roadmap

| Version | Focus |
|---------|-------|
| v0.1 | MVP — see checklist in [DESIGN.md](./DESIGN.md) |
| v0.2 | Sandbox-escape test suite |
| v0.3 | Goal-hijack / deception tests (multi-turn) |

Full roadmap in [DESIGN.md](./DESIGN.md#roadmap).

## Contributing

Open an issue if:
- You'd use this tool and have a specific use case not covered
- You spot a design flaw in DESIGN.md
- You want to claim one of the v0.1 checklist items

## See also

- [My other projects](https://github.com/MukundaKatta)
- [mukunda.dev](https://mukunda-ai.vercel.app)
