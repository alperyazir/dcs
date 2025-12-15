# Git Workflow for Dream Central Storage

## Branch Strategy

**Main Branch:** `main`
- Contains only stable, completed work
- All stories merge back to main via Pull Requests
- Never commit directly to main during development

**Feature Branches:** `story/{epic}-{story}-{short-description}`
- One branch per story
- Created from main before starting dev-story
- Example: `story/1-1-initialize-template`

## Workflow Per Story

### Before Running `/bmad:bmm:workflows:dev-story`

**Step 1: Ensure Clean Working Directory**
```bash
# Check for uncommitted changes
git status

# If changes exist, commit them first
git add .
git commit -m "Your commit message"
```

**Step 2: Create Feature Branch from Main**
```bash
# Ensure you're on main
git checkout main

# Pull latest changes (if working with team)
git pull origin main

# Create and checkout feature branch for the story
git checkout -b story/1-1-initialize-template

# Verify you're on the new branch
git branch --show-current
```

**Step 3: Now Run dev-story**
```bash
/bmad:bmm:workflows:dev-story
```

### During Development

The DEV agent will:
- Make code changes
- Create commits as it completes tasks
- Document changes in the story file

### After Story Completion

**Step 1: Review Changes**
```bash
git status
git log --oneline
```

**Step 2: Push Feature Branch**
```bash
git push -u origin story/1-1-initialize-template
```

**Step 3: Create Pull Request** (if using GitHub/GitLab)
- Or merge directly if working solo:
```bash
git checkout main
git merge story/1-1-initialize-template
git push origin main
git branch -d story/1-1-initialize-template
```

## Branch Naming Convention

Format: `story/{epic}-{story}-{short-description}`

**Examples:**
- `story/1-1-initialize-template` - Story 1.1: Initialize FastAPI Template
- `story/1-2-docker-minio` - Story 1.2: Configure Docker with MinIO
- `story/2-1-jwt-auth` - Story 2.1: JWT Authentication
- `story/3-1-file-upload` - Story 3.1: Single File Upload

## Commit Message Convention

```
<type>: <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat:` New feature implementation
- `fix:` Bug fix
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `docs:` Documentation changes
- `chore:` Maintenance tasks

**Examples:**
```
feat: initialize project from FastAPI full-stack template

- Generated project structure with copier
- Configured Docker Compose with backend, frontend, db
- Set up pre-commit hooks with ruff and prettier
- Verified all services start successfully

Closes Story 1.1
```

## Important Notes

1. **Always create branch from main before starting a story**
2. **Commit frequently during development**
3. **Never commit .bmad/ or .claude/ directories** (already in .gitignore)
4. **Include story number in commits for traceability**
5. **DEV agent will create commits - review them before pushing**

## Quick Reference Card

```bash
# BEFORE dev-story:
git status                                          # Check for changes
git add . && git commit -m "..."                   # Commit if needed
git checkout main                                   # Switch to main
git checkout -b story/{epic}-{story}-{desc}        # Create feature branch

# RUN dev-story:
/bmad:bmm:workflows:dev-story

# AFTER dev-story (when story complete):
git push -u origin story/{epic}-{story}-{desc}     # Push branch
# Create PR or merge to main
```
