# Contributing

Contributions are welcome! Here are some guidelines for contributing to this project.

## Getting Started

1. **Fork the repository**: Create your own fork of the project to work on.
2. **Create a feature branch**: Make your changes in a new branch.
3. **Follow coding standards**: 
   - Use consistent indentation (4 spaces for Python)
   - Follow PEP 8 style guidelines
   - Add comments for complex logic
   - Include docstrings for functions and classes
4. **Write tests**: Add tests for any new functionality.
5. **Update documentation**: Keep the README and other documentation up to date.
6. **Submit a pull request**: When your changes are ready, submit a PR with a clear description of what you've done.

## Pull Request Process

1. Update the README.md with details of changes if needed.
2. Update the documentation if you're changing functionality.
3. The PR will be merged once you have the sign-off of at least one maintainer.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other community members

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/your-username/prompt-evaluator.git
   cd prompt-evaluator
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up pre-commit hooks (if available):
   ```bash
   pre-commit install
   ```

## Testing

Before submitting a pull request, make sure to:

1. Run existing tests:
   ```bash
   python -m pytest tests/
   ```

2. Test your changes with sample datasets:
   ```bash
   python prompt_evaluator.py --input datasets/prompt_inject_dataset.csv --lines 10
   ```

3. Verify documentation is updated and accurate

## Documentation

When making changes that affect functionality:

1. Update the relevant documentation files in the `docs/` folder
2. Add examples if introducing new features
3. Update the main README if adding new major features
4. Ensure all code examples are tested and working

Thank you for your contributions!
