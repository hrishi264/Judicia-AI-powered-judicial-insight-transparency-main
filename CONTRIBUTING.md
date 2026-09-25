# Contributing to Judicia

First off, thank you for considering contributing to Judicia! It's people like you that make Judicia such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
```
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
 - OS: [e.g. Windows 10, macOS 13.0]
 - Browser: [e.g. Chrome, Safari]
 - Node Version: [e.g. 18.0.0]
 - Python Version: [e.g. 3.10]

**Additional context**
Add any other context about the problem here.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Create an issue and provide:
- **Clear title** describing the enhancement
- **Detailed description** of the suggested enhancement
- **Use cases** explaining why this would be useful
- **Possible implementation** if you have ideas

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Follow the coding style** of the project
3. **Write clear commit messages**
4. **Add tests** if applicable
5. **Update documentation** as needed
6. **Ensure all tests pass**
7. **Submit your pull request**

## Development Setup

### Prerequisites
- Node.js 16+
- Python 3.8+
- Git

### Setup Steps

1. Fork and clone the repository:
```bash
git clone https://github.com/your-username/judicia.git
cd judicia
```

2. Set up backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Configure your API keys
```

3. Set up frontend:
```bash
cd frontend
npm install
cp .env.example .env
```

4. Run the application:
```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Coding Standards

### Python (Backend)
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints where possible
- Write docstrings for functions and classes
- Keep functions focused and small
- Maximum line length: 100 characters

**Example:**
```python
def analyze_document(file_path: str) -> dict:
    """
    Analyze a legal document using AI agents.
    
    Args:
        file_path: Path to the PDF document
        
    Returns:
        Dictionary containing analysis results
    """
    # Implementation
    pass
```

### JavaScript/React (Frontend)
- Use functional components with hooks
- Follow the existing component structure
- Use meaningful variable and function names
- Keep components small and reusable
- Use Tailwind CSS for styling

**Example:**
```jsx
export default function AnalysisCard({ title, content }) {
    const [isExpanded, setIsExpanded] = useState(false);
    
    return (
        <div className="rounded-xl shadow-lg p-4">
            <h3 className="font-bold">{title}</h3>
            <p>{content}</p>
        </div>
    );
}
```

### Git Commit Messages
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when relevant

**Good commit messages:**
```
Add PDF validation in upload component
Fix analysis progress bar animation
Update README with installation instructions
Refactor agent orchestration logic (#123)
```

## Project Structure

```
judicia/
├── backend/
│   ├── agents.py          # AI agent logic
│   ├── main.py            # FastAPI server
│   ├── database.py        # Database operations
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Pydantic schemas
│   └── tests/             # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── services/      # API services
│   │   └── App.jsx        # Main app
│   └── tests/             # Frontend tests
└── docs/                  # Documentation
```

## Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Documentation

- Update README.md if you change functionality
- Add JSDoc comments for complex functions
- Update API documentation if endpoints change
- Keep CHANGELOG.md updated

## Questions?

Feel free to:
- Open an issue with the `question` label
- Join our discussions on GitHub Discussions
- Contact the maintainers

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions

Thank you for contributing to Judicia! 🏛️⚖️