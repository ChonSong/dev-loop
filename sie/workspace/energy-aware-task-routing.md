# Energy-Aware Task Routing

## Source
`ChonSong/energy-aware-task-router` (archived)

## Core Idea
Deferrable compute tasks are routed based on real-time electricity grid carbon intensity. Low-carbon windows = run deferred tasks. High-carbon windows = hold them. All without breaking user-facing SLAs.

## Key Patterns

### CarbonIntensityClient
```python
class GridConditions:
    carbon_intensity_gco2kwh: float | None  # grams CO2 per kWh
    level: GridCarbonLevel  # LOW / MEDIUM / HIGH / UNKNOWN
    region: str

class CarbonApiClient:
    async def fetch_carbon_intensity(self, region: str = "AU-NSW") -> GridConditions
```

### Task model
```python
@dataclass
class Task:
    deferrable: bool = True
    defer_until: GridCarbonLevel | None = None   # wait for LOW carbon
    deadline: datetime.datetime | None = None    # don't defer past this
```

### Decision logic
```
if not task.can_defer: → route_now
elif carbon_level >= target: → route_now
else: → defer
```

## Data Sources
- electricitymap.org API (real, requires API key)
- Region: AU-NSW (Australia NSW)

## Potential Applications
- Cron job scheduling that respects green energy windows
- Agent task queue with carbon awareness
- Cloud cost + carbon co-optimization
