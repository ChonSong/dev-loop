# Subagent Delegation Patterns for Research & Spec Work

## When to Delegate

Delegate to a subagent when the task needs **3+ skills loaded simultaneously**. The subagent gets its own context window — skills loaded there don't cost your main context.

## Research Subagent Pattern

Use for competitive analysis, user research synthesis, or multi-source investigation:

```
delegate_task(
    goal="Research [topic] and produce [output format]",
    context="""
    Skills loaded: phuryn/competitor-analysis, deanpeters/customer-journey-map
    Research questions:
    1. [RQ1]
    2. [RQ2]
    3. [RQ3]
    
    Output: Save to docs/research/YYYY-MM-DD_<slug>.md
    Format: [specific format needed]
    """,
    toolsets=['web', 'terminal', 'file'],
)
```

## PRD Drafting Subagent Pattern

Use when producing a full PRD with multiple sections:

```
delegate_task(
    goal="Write a PRD for [feature] based on research findings",
    context="""
    Skills loaded: phuryn/create-prd, deanpeters/problem-statement, 
                   deanpeters/proto-persona, deanpeters/user-story
    
    Research input: [path to research file or summary]
    
    Sections needed: [list specific sections]
    Output: Save to docs/specs/YYYY-MM-DD_<slug>-prd.md
    """,
    toolsets=['file', 'terminal'],
)
```

## Interview / Synthesis Subagent Pattern

Use for processing large amounts of raw research (transcripts, survey results):

```
delegate_task(
    goal="Synthesize research findings from [sources]",
    context="""
    Skills loaded: deanpeters/summarize-interview, coreyhaines31/customer-research
    
    Sources: [list of file paths or URLs]
    
    Output format:
    - Key findings (5-7 bullets)
    - Supporting evidence per finding
    - Conflicting evidence flagged
    - Open questions
    
    Save to docs/research/YYYY-MM-DD_<slug>-synthesis.md
    """,
    toolsets=['file', 'terminal'],
)
```

## Parallel Research Pattern

For broad research, spawn 3 subagents in parallel:

```python
# Competitive landscape
delegate_task(
    goal="Analyze 5 competitors for [product domain]",
    context="Skills: phuryn/competitor-analysis, coreyhaines31/competitor-profiling",
    toolsets=['web', 'file'],
)

# User pain points via YouTube
delegate_task(
    goal="Find and extract UX pain points from YouTube videos about [product type]",
    context="Skills: media/youtube-content. Search: '[product type] review problems frustrations'",
    toolsets=['web', 'terminal', 'file'],
)

# Academic / HCI research
delegate_task(
    target="Search arXiv for HCI research on [interaction pattern]",
    context="Skills: arxiv, research-paper-writing (literature review phase only)",
    toolsets=['web', 'terminal', 'file'],
)
```

## Skill Loading Template for Subagents

When you need a subagent to use specific skills, include the skill content inline in the context. This is more reliable than hoping the subagent finds the skill:

```
delegate_task(
    goal="Write user stories for [feature]",
    context="""
    Use this user story format:
    As a [persona], I want to [action] so that [outcome].
    Acceptance Criteria:
    - [ ] [measurable criterion]
    
    INVEST criteria: Independent, Negotiable, Valuable, Estimable, Small, Testable
    
    Stories needed:
    1. [brief description]
    2. [brief description]
    
    Output: Save to docs/specs/YYYY-MM-DD_<slug>-stories.md
    """,
    toolsets=['file'],
)
```

## Rules

1. **Max 10 skills per subagent.** More than that and the subagent's context is too fragmented.
2. **Always specify the output path.** Subagents forget where to save if you don't tell them.
3. **Verify subagent output.** Read the file they produce before trusting it.
4. **Don't nest delegation.** Leaf subagents can't delegate further.
5. **For tasks > 5 minutes, use background=True** with notify_on_complete=True instead of delegate_task.
