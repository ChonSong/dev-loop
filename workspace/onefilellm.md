# OneFileLLM

## Source
`ChonSong/onefilellm` (archived)

## Core Idea
Command-line tool that aggregates content from local files, GitHub repos, web pages, PDFs, YouTube transcripts into a single structured XML file for LLM context.

## Key Patterns
- GitHub repo → scrape all files
- GitHub PR → scrape diff
- arXiv paper → fetch PDF
- YouTube → transcript
- Web URL → scrape
- Output: structured XML (clipboard + file)

## Potential Applications
- `repo-transmute` already does semantic search over code
- Could be used as a "fetch all context" pre-task before agent runs
- YouTube transcript fetching for learning materials
- PDF ingestion for research agents
