# Dev Loop — Autonomous Coach/Player Development System

A structured autonomous development loop where **Player** agents implement tasks from a backlog and **Coach** agents adversarially review each commit. Inspired by g3's dialectical autocoding (Block AI Research, Dec 2025).

## Core Concept

```
AGENTS.md (tasks + criteria)  ──→  Player (implements, tests, commits)
         ↑                              │
         │                              ▼
    Coach (reviews, approves,       Checkpoint.json
    generates next tasks)         (state tracking)
```

Each repo describes itself via `AGENTS.md` + `.checkpoint.json`. The loop discovers repos by scanning for these files.

## Quick Start

### 1. Add AGENTS.md to a repo

Copy `templates/AGENTS.md` to the repo root. Fill in:

- **About**: one-line description + status (active/maintenance/legacy)
- **Architecture**: stack, key directories, service relations
- **Conventions**: test commands, lint, commit format, safety rules
- **Skills**: Hermes skills to load for this project
- **Tasks**: ordered by priority, each with success criteria and coach checks

### 2. Add .checkpoint.json

Copy `templates/checkpoint.json` to the repo root. Set `current_task` to the first task ID from AGENTS.md.

### 3. Register in master checkpoint

Copy `templates/master-checkpoint.json` to `~/.hermes/master-checkpoint.json`. Add your project entry.

### 4. Cron jobs handle the rest

The Player cron runs hourly and picks up any repo with both AGENTS.md + checkpoint. The Coach runs 5 minutes later and reviews.

## Repository Structure

```
dev-loop/
├── README.md                     # This file
├── docs/
│   ├── architecture.md           # Full loop design
│   ├── agent-roles.md            # Coach and Player responsibilities
│   ├── project-onboarding.md     # Step-by-step project setup
│   ├── scoring-model.md          # Backlog prioritisation formula
│   └── cron-setup.md             # Cron job configuration reference
├── templates/
│   ├── AGENTS.md                 # Blank AGENTS.md
│   ├── checkpoint.json           # Blank checkpoint
│   └── master-checkpoint.json    # Blank master checkpoint
└── skills/
    ├── coach-agent.md            # Coach role reference
    ├── player-agent.md           # Player role reference
    └── writing-tasks.md          # Task writing guidelines
```
