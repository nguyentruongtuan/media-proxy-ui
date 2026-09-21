# API Coding Instruction

> `.claude/skills/`; deep reference lives in `docs/` (see end of file).

## Project Overview

This is a Python API for Movie Proxy UI, a website to crawl data from another website and show a compact UI for Android TV. The project uses a modular feature-based architecture with Python, Typescript for ReactJS, MongoDB/Mongoose, 

## Git commit

- First line is with format CHORE|FEAT|FIX: GRAP-123: <ticket title>
- Don't add this line at the end of commit message `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`
- Summary commit message after first line to 2 compact message

## Jira implementation

- Read the jira description
- If jira ticket is story, create worktree with branch `feature/<ticket>`
- Get subtasks from prompt input for implementing
- Each subtask create a worktree with branch `feature/<ticket>`, after finishing merge subtask branch to story branch
- If task was implemented, read the comments
- Before implementing read the worktrees first, ask for continue with existing worktree or create new one