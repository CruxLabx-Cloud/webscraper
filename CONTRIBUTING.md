# Contributing Guide

Thank you for your interest in contributing to ScrapeFlow! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional. We're building a welcoming community.

## Getting Started

### 1. Fork & Clone

```bash
git clone https://github.com/yourusername/scrapeflow.git
cd scrapeflow
```

### 2. Set Up Development Environment

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 3. Create Feature Branch

```bash
git checkout -b feature/amazing-feature
```

## Development Workflow

### Frontend Development

```bash
cd frontend

# Start dev server
npm run dev

# Run tests during development
npm run test:watch

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format
```

### Backend Development

```bash
cd backend

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Format code
black app/

# Type checking
mypy app/
```

## Code Standards

### TypeScript/JavaScript

- **Strict mode**: Enabled
- **Indentation**: 2 spaces
- **Quotes**: Double quotes
- **Semicolons**: Required
- **Line length**: 100 characters (guideline)

### Python

- **PEP 8**: Follow style guide
- **Line length**: 100 characters
- **Type hints**: Required for all functions
- **Docstrings**: Google style

### File Organization

```
src/
├── app/              # Pages
├── components/       # React components
│   ├── ui/          # Reusable UI components
│   └── features/    # Feature-specific components
├── lib/             # Utilities and helpers
│   ├── api.ts       # API layer
│   ├── logger.ts    # Logging
│   └── utils.ts     # Utilities
└── __tests__/       # Tests
```

## Commit Guidelines

Use conventional commits:

```
feat: Add user authentication
fix: Resolve search timeout issue
docs: Update deployment guide
refactor: Simplify API error handling
test: Add tests for export functionality
chore: Update dependencies
```

### Commit Checklist

- [ ] Code follows style guide
- [ ] Tests pass
- [ ] No console logs (except debugging)
- [ ] Types are correct
- [ ] Commit message is descriptive

## Pull Request Process

1. **Update main branch**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all checks**
   ```bash
   npm run lint
   npm run type-check
   npm run test
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/amazing-feature
   ```

4. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Testing
   Steps to test the changes

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No breaking changes (or documented)
   ```

## Testing Requirements

### Frontend

```bash
# Run all tests
npm test

# Specific test file
npm test -- api.test.ts

# With coverage
npm test -- --coverage
```

### Backend

```bash
# Run tests
pytest

# With coverage
pytest --cov=app

# Specific test
pytest tests/test_api.py
```

### Test Coverage

- **Minimum**: 70% coverage
- **Target**: 90%+ coverage for critical paths

## Documentation

### Code Comments

```typescript
/**
 * Validates and sanitizes URL input
 * @param url - The URL to validate
 * @returns true if valid, false otherwise
 * @throws TypeError if not a string
 */
function validateUrl(url: string): boolean {
  // Implementation
}
```

### Docstrings (Python)

```python
def search(
    query: str,
    max_results: int = 10,
    search_depth: str = "basic"
) -> SearchResponse:
    """
    Search using Tavily API.
    
    Args:
        query: Search query string
        max_results: Maximum results to return (1-50)
        search_depth: Search depth level (basic/advanced)
    
    Returns:
        SearchResponse with ranked results
    
    Raises:
        ValueError: If query is empty or max_results out of range
    """
```

### README Updates

Update README if you:
- Add new features
- Change API endpoints
- Add environment variables
- Modify setup instructions

## Reporting Issues

### Bug Report Template

```markdown
## Description
Clear description of the bug

## Reproduction
Steps to reproduce:
1. ...
2. ...
3. ...

## Expected vs Actual
- Expected: ...
- Actual: ...

## Environment
- OS: ...
- Node version: ...
- Python version: ...
- Browser: ...

## Logs/Screenshots
Include relevant logs or screenshots
```

### Feature Request Template

```markdown
## Description
Clear description of the feature

## Motivation
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternative Solutions
Any alternatives considered?
```

## Review Process

PRs are reviewed by maintainers within 2-3 days.

### Reviewer Checklist

- [ ] Code quality and style
- [ ] Test coverage
- [ ] Documentation completeness
- [ ] Performance impact
- [ ] Security implications
- [ ] Breaking changes

### Addressing Feedback

1. Make requested changes
2. Push updates to branch
3. Don't force-push (preserve discussion)
4. Re-request review

## Release Process

1. **Version Bump** (semver)
   ```bash
   npm version patch|minor|major
   ```

2. **Changelog Update**
   - Document changes in CHANGELOG.md
   - Link to related PRs/issues

3. **Tag & Release**
   ```bash
   git push origin main --tags
   ```

4. **Deployment**
   - Automated via GitHub Actions
   - Docker images pushed to registry
   - Documentation updated

## Getting Help

- **Questions**: Open a discussion
- **Issues**: File an issue with template
- **Chat**: Join our community Discord
- **Email**: developers@scrapeflow.dev

## Resources

- [API Documentation](./API.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Frontend Setup](./frontend/README.md)
- [Backend Setup](./backend/README.md)

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md
- Release notes
- Hall of fame section (for major contributions)

Thank you for contributing to ScrapeFlow! 🎉
