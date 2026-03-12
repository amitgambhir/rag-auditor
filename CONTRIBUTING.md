# Contributing to RAG Auditor

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/rag-auditor`
3. Create a feature branch: `git checkout -b feat/your-feature`
4. Make your changes
5. Run tests (see below)
6. Submit a pull request

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Running Tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm test
```

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Add tests for new functionality
- Update the README if you add a new feature
- Run the test suite before submitting
- Describe what and why in the PR description

## Reporting Issues

Use the GitHub issue templates:
- Bug reports: describe steps to reproduce
- Feature requests: explain the problem and proposed solution

## Code Style

- Backend: follow PEP 8, use `ruff` for linting
- Frontend: consistent with existing Tailwind/React patterns
- No commented-out code in PRs
