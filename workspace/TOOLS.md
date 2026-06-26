# General Tool Guidelines

- **file_read** – Always specify absolute path. Respect allowed paths.
- **file_write** – Never write outside designated directories.
- **exec** – Use a timeout; prefer built‑in commands over complex pipelines.
- **spawn_agent** – Provide clear, self‑contained tasks. Do not poll for completion; wait for auto‑announcement.
- **web_search** / **web_fetch** – Respect rate limits; cite sources.

See each agent's `TOOLS.md` for specific permissions.
