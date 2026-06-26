# AI System Monitor

## Source
`ChonSong/ai-system-monitor` (archived)

## Core Idea
Collects full process tree with psutil, groups processes by parent shell (bash/zsh/tmux/screen), outputs JSON for LLM context injection.

## Key Patterns

### Process collection
```python
psutil.process_iter(['pid', 'ppid', 'name', 'cmdline', 'create_time', 'cwd', 'status', 'username'])
```

### Shell-grouping heuristic
```python
shell_keywords = ['bash', 'zsh', 'sh', 'tmux', 'screen', 'zellij', 'fish']
# Group processes by parent shell session
# Output: { shell_name: 'tmux', pid: 12345, applications: [...] }
```

## Output format
```json
{
  "shell_process": { "pid": 12345, "name": "tmux", "cmdline": [...] },
  "applications": [{ pid, name, cmdline, ... }]
}
```

## Potential Applications
- LLM context injection: give agent full picture of running processes
- Shell session tracking for agent orchestration
- Anomaly detection: unexpected processes
- Resource monitoring correlated to agent activity
