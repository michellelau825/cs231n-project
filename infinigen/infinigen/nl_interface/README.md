# Infinigen Natural Language Interface

This module provides a natural language interface for generating 3D assets in Infinigen. It allows users to describe assets in natural language and automatically converts these descriptions into the appropriate parameters for asset generation.

## Features

- Natural language prompt parsing
- Automatic parameter mapping
- Material and style extraction
- Asset validation
- Template-based prompt generation

## Usage

### Basic Usage

```python
from infinigen.nl_interface.nl_interface import InfinigenNLInterface

# Initialize the interface
nl_interface = InfinigenNLInterface()

# Generate an asset from a prompt
prompt = "Create a modern wooden chair with adjustable height and leather seat"
asset = nl_interface.generate_asset(prompt)
```

### Using Prompt Templates

```python
from infinigen.nl_interface.prompt_templates import PromptTemplates

# Initialize templates
templates = PromptTemplates()

# Get a template for a specific asset type
chair_template = templates.get_chair_template()
print(chair_template)

# Format a prompt using a template
prompt = templates.format_prompt(
    asset_type="chair",
    style="modern",
    material="wood",
    size="medium",
    features=["adjustable", "leather seat"]
)
```

### Utility Functions

```python
from infinigen.nl_interface.utils import parse_prompt, validate_prompt

# Parse a prompt into structured data
prompt = "Create a modern wooden chair"
parsed_data = parse_prompt(prompt)

# Validate a prompt
is_valid = validate_prompt(prompt)
```

## Prompt Structure

A valid prompt should include:

1. Asset type (e.g., chair, table, lamp)
2. Style (e.g., modern, traditional, minimalist)
3. Materials (e.g., wood, metal, glass)
4. Size (small, medium, large)
5. Optional features (e.g., adjustable, foldable)

Example prompts:
- "Create a modern wooden chair with adjustable height"
- "Generate a minimalist glass coffee table with metal legs"
- "Design a traditional wooden dining table with rustic finish"

## Supported Asset Types

- Chairs
- Tables
- Lamps
- Windows

## Supported Materials

- Wood
- Metal
- Glass
- Fabric
- Plastic
- Ceramic

## Supported Styles

- Modern
- Traditional
- Minimalist
- Industrial
- Rustic
- Contemporary

## Error Handling

The interface includes error handling for:
- Invalid prompts
- Missing required information
- Unsupported asset types or materials
- Generation failures

## Contributing

To add support for new asset types or materials:
1. Update the `parameter_mapper.py` file with new mappings
2. Add new templates in `prompt_templates.py`
3. Update the utility functions in `utils.py`
4. Add appropriate error handling in `nl_interface.py` 