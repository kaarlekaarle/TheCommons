# Contributing to The Commons

Thank you for your interest in contributing to The Commons! This document provides guidelines and instructions for contributing to the project.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/kaarlehurtig/the-commons.git
   cd the-commons
   ```

2. **Set up Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r backend/requirements-test.txt
   ```

4. **Set up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

1. **Create a New Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-fix-name
   ```

2. **Make Your Changes**
   - Follow the coding standards
   - Write tests for new features
   - Update documentation
   - Ensure proper logging

3. **Run Tests**
   ```bash
   pytest
   pytest --cov=backend  # For coverage report
   ```

4. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"  # or "fix: fix bug"
   ```

5. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Use the PR template
   - Link related issues
   - Request reviews from maintainers

## Coding Standards

### Python Code Style

1. **Formatting**
   - Use Black for code formatting
   - Line length: 88 characters
   - Use double quotes for strings
   - Python 3.10+ features are allowed

2. **Type Hints**
   - Use type hints for all function parameters and return values
   - Use Optional[] for nullable values
   - Use Union[] for multiple possible types
   - Use the new Python 3.10+ union syntax (|) where appropriate

3. **Docstrings**
   - Use Google-style docstrings
   - Include Args, Returns, and Raises sections
   - Document all public functions and classes

Example:
```python
def process_vote(vote_id: int, weight: int | None = None) -> Vote:
    """Process a vote with the given weight.

    Args:
        vote_id: The ID of the vote to process
        weight: Optional weight to apply to the vote

    Returns:
        Vote: The processed vote object

    Raises:
        ValidationError: If the vote data is invalid
        ResourceNotFoundError: If the vote doesn't exist
    """
```

### Logging and Audit Trails

1. **Structured Logging**
   - Use the `structlog` library for all logging
   - Include relevant context in log events
   - Use appropriate log levels
   - Follow the logging configuration in `backend/core/logging.py`

2. **Audit Trails**
   - Log all security-relevant events
   - Include user context in audit logs
   - Use the audit logging middleware
   - Follow the audit logging guidelines

Example:
```python
import structlog

logger = structlog.get_logger()

async def process_vote(vote_id: int, user_id: int) -> Vote:
    logger.info(
        "processing_vote",
        vote_id=vote_id,
        user_id=user_id,
        event_type="vote_processed"
    )
```

### Database

1. **Migrations**
   - Create new migrations for schema changes
   - Test migrations both up and down
   - Include meaningful migration messages

2. **Queries**
   - Use async/await for database operations
   - Use SQLAlchemy's query builder
   - Include proper error handling

### Testing

1. **Test Structure**
   - Place tests in the `tests` directory
   - Use descriptive test names
   - Follow the Arrange-Act-Assert pattern
   - Use fixtures for common setup

2. **Test Coverage**
   - Aim for high test coverage
   - Test edge cases and error conditions
   - Use fixtures for common setup
   - Include load tests for performance-critical features

Example:
```python
@pytest.mark.asyncio
async def test_create_poll_with_invalid_data(client: AsyncClient):
    """Test creating a poll with invalid data."""
    # Arrange
    invalid_data = {"title": ""}  # Missing required description

    # Act
    response = await client.post("/api/polls/", json=invalid_data)

    # Assert
    assert response.status_code == 422
    assert "description" in response.json()["detail"]
```

### API Development

1. **Endpoint Design**
   - Follow RESTful principles
   - Use appropriate HTTP methods
   - Include proper status codes
   - Implement proper error handling

2. **Request/Response**
   - Validate input data
   - Use Pydantic models
   - Include proper error responses
   - Document all endpoints

3. **Documentation**
   - Document all endpoints
   - Include request/response examples
   - Update API.md for changes
   - Include security considerations

## Pull Request Process

1. **Before Submitting**
   - Run all tests
   - Check code formatting
   - Update documentation
   - Rebase on main branch
   - Ensure proper logging

2. **PR Description**
   - Describe the changes
   - Link related issues
   - Include testing instructions
   - Note any breaking changes
   - Document logging changes

3. **Review Process**
   - Address review comments
   - Keep PR focused and small
   - Update PR as needed
   - Ensure all tests pass

## Code Review Guidelines

1. **What to Look For**
   - Code quality and style
   - Test coverage
   - Documentation
   - Security considerations
   - Performance impact
   - Logging implementation

2. **Review Comments**
   - Be constructive
   - Explain reasoning
   - Suggest improvements
   - Link to relevant docs

## Release Process

1. **Versioning**
   - Follow semantic versioning
   - Update version in pyproject.toml
   - Update CHANGELOG.md
   - Tag releases appropriately

## Getting Help

- Open an issue for bugs
- Use discussions for questions
- Join our community chat
- Check existing documentation

## License

By contributing to The Commons, you agree that your contributions will be licensed under the project's MIT License.