# zion — Design

> The Zion Boundary — a toolkit for testing the limits of human control over agentic AI. Adversarial benchmarks for instruction-following, deception detection, sandbox escape prevention.

## Problem

As AI agents take more autonomous actions (spending money, deploying code, sending emails), safety research on 'does this agent actually do what I asked' needs production-grade benchmarks and red-team tooling — not just academic papers. Alignment evals are either proprietary (Anthropic, OAI) or fragmented across research GitHub repos.

zion is an open-source toolkit for adversarial evaluation of agentic systems: prompt-injection resistance, goal-hijack detection, sandbox-escape attempts, deception detection. Targeted at developers building agents who need to know where their system breaks before a user finds out.

## Primary users

- Agent-system developers wanting to ship safely
- Alignment researchers
- Red teams at AI labs and security firms

## Use cases

- Run the 'instruction-injection gauntlet' against your agent before shipping
- Measure how often your agent follows injected instructions in retrieved context
- Adversarial sandbox: can the agent try to break out of its constraints?
- Deception eval: does the agent under-report errors to the user?

## Planned stack

- Python 3.11+
- Anthropic + OpenAI + local model adapters
- Standard eval harness compatible with Inspect (UK AISI's framework)
- YAML-declared test suites
- HTML report output

## MVP scope (v0.1)

- [ ] 5-10 well-designed instruction-injection tests
- [ ] `zion eval my_agent.py` runs suite, outputs HTML report
- [ ] Adapter pattern for agent wrappers (just needs a `run(prompt) -> response` function)
- [ ] Deterministic scoring — each test has clear pass/fail

## Roadmap

- v0.2: Sandbox-escape test suite
- v0.3: Goal-hijack / deception tests (multi-turn)
- v0.4: Integration with CI/CD — gate PRs on safety evals
- v1.0: Shared leaderboard, standardized benchmark names

---

_This is a living design document. Status: **concept / active planning**. Follow progress at [github.com/MukundaKatta](https://github.com/MukundaKatta)._
