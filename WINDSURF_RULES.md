# Windsurf Workplace Coding Guidelines

## 1. Project Structure and Organization
### 1.1 Cascade must always be Context-Aware : IMPORTANT!

- Always be mindful of the context of the codebase, including existing features and new features being added
- Ensure that new features are compatible with old features and that nothing is broken
- Use decorators to add new features and avoid hardcoding values or behavior
- When adding new features or modifying existing ones, Cascade needs to ensure that the codebase remains consistent and functional
- Cascade will do edits in a focused and targeted manner, after scanning the file, to avoid wasting time or throwing errors and wasting credits

### 1.2 File Placement
- All URL endpoints MUST be defined in `url_endpoints.py`
- Each feature should have its dedicated feature-specific file (e.g., `water_quality.py` for water quality-related functionality)
- Maintain a clear and logical directory structure

## 2. Coding Practices

### 2.1 Hard Coding Prohibition
- NEVER hard-code values, configurations, or sensitive information
- Use environment variables, configuration files, or constants for all configurable values
- Sensitive information (API keys, credentials) must be stored in `.env` files or secure configuration management

### 2.2 Modularity and Separation of Concerns
- Each module/file should have a single, well-defined responsibility
- Keep functions and methods focused and concise
- Use type hints and docstrings to clearly define function purposes and inputs/outputs

### 2.3 URL Endpoint Management
- All route definitions must be centralized in `url_endpoints.py`
- Use descriptive and consistent naming conventions for endpoints
- Implement proper error handling and validation for all endpoints

## 3. Configuration and Environment

### 3.1 Dependency Management
- Maintain an up-to-date `requirements.txt` file
- Pin specific versions of dependencies
- Regularly update and audit dependencies for security and compatibility

### 3.2 Environment Configuration
- Use `python-dotenv` for managing environment variables
- Never commit `.env` files to version control
- Provide a `.env.example` template for other developers

## 4. Code Quality and Best Practices

### 4.1 Code Review Guidelines
- All code changes must go through a peer review process
- Follow PEP 8 style guidelines for Python code
- Use type annotations and maintain high code readability
- Write comprehensive docstrings for all functions and classes

### 4.2 Error Handling
- Implement robust error handling and logging
- Use specific exception types
- Log errors with sufficient context for debugging

## 5. Security Considerations

### 5.1 Input Validation
- Validate and sanitize all user inputs
- Implement proper authentication and authorization checks
- Use parameterized queries to prevent SQL injection

### 5.2 Sensitive Data Protection
- Never log or expose sensitive information
- Use secure hashing for passwords
- Implement proper access controls

## 6. Performance and Optimization

### 6.1 Database Interactions
- Use database indexing and query optimization techniques
- Implement caching where appropriate
- Minimize database round trips

### 6.2 Code Efficiency
- Avoid unnecessary computations
- Use list comprehensions and generator expressions
- Profile and optimize performance-critical code paths

## 7. Testing and Quality Assurance

### 7.1 Test Coverage
- Write unit tests for all critical functionality
- Aim for high test coverage
- Use pytest for Python testing
- Implement integration and end-to-end tests

### 7.2 Continuous Integration
- Set up automated testing and linting
- Use tools like Black for code formatting
- Implement pre-commit hooks for code quality checks

## 8. Documentation

### 8.1 Code Documentation
- Maintain a comprehensive README.md
- Document project setup, dependencies, and running instructions
- Keep inline comments clear and concise
- Update documentation with each significant change

9. UX/UI Design Principles
9.1 Consistent Layout and Design
Use a consistent layout across all pages.
Ensure responsive design for different screen sizes.


---

**Note**: These guidelines are living documents. They should be regularly reviewed and updated to reflect the evolving needs of the project and best practices in software development.
