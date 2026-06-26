# Indefinite Autonomous Development Pattern

Use this pattern when a project needs ongoing development beyond a single session's max_turns. Each cron run is one unit of work; the checkpoint file bridges state between runs.

## Components

- **Checkpoint file** (`.checkpoint.json`): Stores phase, completed tasks, next task, last commit SHA, health status
- **Cron job**: Runs on schedule (every 2h), loads skill + prompt, does one unit of work
- **Skill** (`project-name-dev`): Full architecture, phases, rules, conventions
- **`max_turns: 0`**: No session cap

## Checkpoint Format

```json
{
  "project": "project-name",
  "repo": "/path/to/repo",
  "phase": 1,
  "phase_name": "Project Foundation",
  "completed": [".gitignore"],
  "current": null,
  "next": "Dockerfile",
  "health": "tests_pass",
  "last_sha": "abc1234"
}
```

## Cron Job Design

```
schedule: every 120m
deliver: origin
skills: [project-dev]
toolsets: [terminal, file, web]
```

Each run: read checkpoint → do ONE task → test → commit → update checkpoint → report.

## When to Use

- New backend-heavy projects (FastAPI, Go, data processing, CLI tools)
- Projects with full architecture understood before starting
- NOT for frontend-heavy projects (no visual verification)
- NOT for urgent work (cron is deferred ~2h)
