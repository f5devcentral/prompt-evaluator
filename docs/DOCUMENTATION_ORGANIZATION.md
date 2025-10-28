# Documentation Organization

This document explains how the documentation is organized after the addition of improved dataset formats.

## 📁 Directory Structure

```
prompt-evaluator/
├── README.md                           # Main project README with "What's New" section
├── docs/                               # Core documentation
│   ├── README.md                       # Documentation index
│   ├── installation.md                 # Setup instructions
│   ├── usage.md                       # Usage examples
│   ├── datasets.md                    # Dataset management
│   ├── IMPROVED_DATASET_FORMATS.md    # New dataset formats guide
│   ├── troubleshooting.md            # Common issues
│   └── contributing.md                # Contribution guide
├── tools/                              # New dataset tools
│   ├── README.md                      # Tools documentation
│   ├── improved_dataset_converter.py  # Format converter
│   ├── enhanced_dataset_reader.py     # Unified reader
│   ├── migrate_datasets.py           # Migration tool
│   ├── example_improved_formats.py   # Interactive example
│   └── demo_improved_formats.py       # Complete demonstration
└── datasets/                          # Dataset files
    ├── *.csv                          # Original datasets
    ├── *.jsonl                        # Migrated datasets
    └── *.backup.*                     # Backup files
```

## 📚 Documentation Hierarchy

### 1. Main README (`README.md`)
- **Purpose**: Project overview and quick start
- **New Content**: "What's New" section highlighting improvements
- **Key Features**: Updated feature list with new capabilities
- **Quick Migration**: Step-by-step migration commands

### 2. Core Documentation (`docs/`)
- **`docs/README.md`**: Documentation index and navigation
- **`docs/installation.md`**: Setup instructions (unchanged)
- **`docs/usage.md`**: Usage examples (unchanged)
- **`docs/datasets.md`**: Dataset management (unchanged)
- **`docs/IMPROVED_DATASET_FORMATS.md`**: New comprehensive guide
- **`docs/troubleshooting.md`**: Common issues (unchanged)
- **`docs/contributing.md`**: Contribution guide (unchanged)

### 3. Tools Documentation (`tools/`)
- **`tools/README.md`**: Complete tools documentation
- **Individual tool files**: Self-documenting with help text

## 🆕 New Documentation Features

### What's New Section
The main README now includes a prominent "What's New" section that:
- Highlights the improved dataset formats
- Lists new tools and their purposes
- Provides quick migration commands
- Emphasizes backward compatibility

### Improved Dataset Formats Guide
Comprehensive documentation covering:
- Problems with original format
- New format options (JSONL, CSV, TSV, Parquet)
- Migration process
- Usage examples
- Format comparison
- Best practices

### Tools Documentation
Dedicated documentation for new tools:
- Command-line usage examples
- Python API examples
- Format comparison table
- Migration workflow
- Safety features

## 🔄 Migration Documentation

### User Journey
1. **Discovery**: Users see "What's New" in main README
2. **Learning**: Read improved dataset formats guide
3. **Tools**: Explore tools documentation
4. **Action**: Follow migration commands
5. **Validation**: Use demo tools to verify

### Documentation Flow
```
README.md (What's New)
    ↓
docs/IMPROVED_DATASET_FORMATS.md (Detailed Guide)
    ↓
tools/README.md (Tool Usage)
    ↓
tools/demo_improved_formats.py (Hands-on Demo)
```

## 📖 Documentation Principles

### 1. Progressive Disclosure
- Start with high-level overview in main README
- Provide detailed information in dedicated guides
- Include hands-on examples and demos

### 2. Backward Compatibility
- All existing documentation remains unchanged
- New content is additive, not replacing
- Clear migration path provided

### 3. Multiple Entry Points
- Main README for quick overview
- Dedicated guides for detailed information
- Tool-specific documentation for implementation
- Interactive demos for hands-on learning

### 4. User-Centric Organization
- Organized by user needs, not technical structure
- Clear navigation between related topics
- Consistent formatting and structure

## 🎯 Key Messages

### For Existing Users
- "Your existing code works unchanged"
- "Safe migration with automatic backups"
- "Gradual adoption supported"

### For New Users
- "Multiple format options available"
- "Proper handling of special characters"
- "Metadata support for rich datasets"

### For Developers
- "Comprehensive API documentation"
- "Extensible format support"
- "Backward compatibility maintained"

## 📋 Maintenance

### Documentation Updates
- Keep "What's New" section current
- Update tool documentation with new features
- Maintain format comparison tables
- Keep migration examples current

### User Feedback
- Monitor for common questions
- Update troubleshooting guide
- Improve examples based on usage
- Add new use cases as they emerge

This organization ensures that users can easily discover, understand, and use the new dataset format improvements while maintaining full backward compatibility with existing workflows.
