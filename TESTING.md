# Testing Custom Frame Processors

This document describes the new testing infrastructure for custom frame processors in pipecat-cli.

## Overview

The `pipecat test` command allows you to unit test custom frame processors by:
1. Loading test frames from a JSON file
2. Running them through your processor
3. Validating the output (or displaying it for exploratory testing)

## Quick Start

```bash
# Run in exploratory mode (see what your processor outputs)
pipecat test my_processor.py --frames test_input.json

# Run with validation (test passes/fails based on expected output)
pipecat test my_processor.py --frames test_with_expected.json

# Show detailed output
pipecat test my_processor.py --frames test.json --verbose
```

## Implementation Details

### Files Added to Pipecat Core

**`../pipecat/src/pipecat/tests/`** - Testing utilities (added to existing tests module)
- `__init__.py` - Public API exports (updated)
- `serialization.py` - Frame serialization/deserialization
- `test_runner.py` - Test execution logic
- `utils.py` - Existing test utilities (pre-existing)

Key functions:
- `dict_to_frame(data)` - Convert JSON dict to Frame object
- `load_frames_from_json(filepath)` - Load frames from JSON file
- `run_test_from_file(processor, test_file)` - Run a test from JSON

### Files Added to Pipecat CLI

**`src/pipecat_cli/commands/test.py`** - Test command implementation
- Auto-discovers FrameProcessor classes in Python files
- Loads and runs tests from JSON files
- Displays results with rich formatting
- Supports exploratory and validation modes

**`src/pipecat_cli/main.py`** - Updated to register test command

**`examples/`** - Example processor and tests
- `uppercase_processor.py` - Simple example processor
- `test_uppercase.json` - Test with expected output
- `test_uppercase_exploratory.json` - Test without expected output
- `README.md` - Examples documentation

## JSON Test File Format

```json
{
  "input_frames": [
    {"type": "TextFrame", "text": "hello"},
    {"type": "TextFrame", "text": "world"}
  ],
  "expected_output": [
    {"type": "TextFrame", "text": "HELLO"},
    {"type": "TextFrame", "text": "WORLD"}
  ]
}
```

### Fields

- `input_frames` (required): Array of frame objects to send to the processor
- `expected_output` (optional): Array of expected output frames
  - If provided: Test validates output matches expected
  - If omitted: Test runs in exploratory mode and displays output

### Frame Format

Each frame is a JSON object with:
- `type` (required): Frame class name (e.g., "TextFrame", "EndFrame")
- Additional fields depend on frame type (e.g., `text` for TextFrame)

Common frame types:
- `TextFrame` - Text data (fields: `text`)
- `EndFrame` - End marker (no additional fields)
- `StartFrame` - Start marker (no additional fields)
- `OutputAudioRawFrame` - Audio data (fields: `audio` [base64], `sample_rate`, `num_channels`)
- `TranscriptionFrame` - Transcription (fields: `text`, `user_id`, `timestamp`)

## Command Usage

```bash
pipecat test <processor_file> [OPTIONS]
```

### Arguments

- `processor_file` - Python file containing your FrameProcessor class

### Options

- `--frames`, `-f` - JSON file with test frames (required)
- `--processor`, `-p` - Processor class name (auto-detected if only one exists)
- `--verbose`, `-v` - Show detailed frame data
- `--help` - Show help message

## Testing Workflow

### 1. Write Your Processor

```python
# my_processor.py
from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

class MyProcessor(FrameProcessor):
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        if isinstance(frame, TextFrame):
            # Process the frame
            modified = TextFrame(text=frame.text.upper())
            await self.push_frame(modified, direction)
        else:
            await self.push_frame(frame, direction)
```

### 2. Create Input Frames

```json
{
  "input_frames": [
    {"type": "TextFrame", "text": "hello"}
  ]
}
```

### 3. Run in Exploratory Mode

```bash
pipecat test my_processor.py --frames input.json
```

This shows you what frames are output. The command will display a formatted table and provide JSON you can copy for `expected_output`.

### 4. Add Expected Output

Update your JSON file:

```json
{
  "input_frames": [
    {"type": "TextFrame", "text": "hello"}
  ],
  "expected_output": [
    {"type": "TextFrame", "text": "HELLO"}
  ]
}
```

### 5. Validate

```bash
pipecat test my_processor.py --frames input.json
```

Now the test validates output matches expected and returns exit code 0 (pass) or 1 (fail).

## Features

### Exploratory Mode

When `expected_output` is omitted, the command:
- Runs your processor with the input frames
- Displays all output frames in a formatted table
- Shows JSON you can copy-paste to create `expected_output`
- Always exits with code 0 (no validation)

This is perfect for:
- Understanding what your processor outputs
- Debugging processor behavior
- Creating test expectations

### Validation Mode

When `expected_output` is provided, the command:
- Runs your processor with the input frames
- Compares actual output to expected output
- Shows pass/fail result
- Displays comparison table (on failure or with --verbose)
- Exits with code 0 (pass) or 1 (fail)

Validation checks:
- Frame count matches
- Frame types match
- Frame field values match (if specified in expected_output)

### Auto-Discovery

The command automatically finds your FrameProcessor class:
- Searches for classes that inherit from `FrameProcessor`
- If multiple classes found, asks you to specify with `--processor`
- Handles imports and instantiation automatically

### Rich Output

Uses Rich library for beautiful terminal output:
- Color-coded status (green=pass, red=fail, yellow=exploratory)
- Formatted tables for frame comparison
- Syntax-highlighted JSON output
- Progress indicators

## Examples

See `examples/` directory for a complete working example:

```bash
cd examples/

# Exploratory mode
pipecat test uppercase_processor.py --frames test_uppercase_exploratory.json

# Validation mode
pipecat test uppercase_processor.py --frames test_uppercase.json

# Verbose mode
pipecat test uppercase_processor.py --frames test_uppercase.json --verbose
```

## Future Enhancements

Planned for later (not yet implemented):
- MessagePack format support (for Whisker recordings)
- Frame filtering tools (extract specific frames from recordings)
- Snapshot testing (auto-generate expected output)
- TUI (terminal user interface) for interactive testing

## Architecture Notes

### Why Two Packages?

- **pipecat core** (`../pipecat/src/pipecat/tests/`) - Core testing utilities
  - Frame serialization/deserialization
  - Test runner for programmatic use
  - Located in existing tests module alongside test utilities
  - Can be used programmatically by other tools
  
- **pipecat-cli** (`src/pipecat_cli/commands/test.py`) - CLI interface
  - Command-line parsing and argument handling
  - Processor discovery and loading
  - Rich formatting and user interaction
  - Depends on Typer, Rich, etc.

This separation allows:
- Core testing utilities to live alongside existing test infrastructure
- CLI to provide polished UX without bloating core
- Other tools to import and use testing utilities directly from pipecat.tests

### Design Decisions

1. **JSON format** - Human-readable, easy to edit, language-agnostic
2. **Exploratory mode** - Discover behavior before writing expectations
3. **Type-only validation** - Match frame types, optionally validate fields
4. **Auto-discovery** - Reduce boilerplate, "just works" for simple cases
5. **Exit codes** - 0=pass, 1=fail for CI/CD integration

## Troubleshooting

### "No FrameProcessor subclass found"

Make sure your processor:
- Inherits from `FrameProcessor`
- Is defined in the specified file
- Use `--processor ClassName` if auto-discovery fails

### "Could not instantiate processor"

Your processor needs a no-argument constructor or default arguments:

```python
class MyProcessor(FrameProcessor):
    def __init__(self, param="default"):  # Provide default
        super().__init__()
```

### "Unknown frame type"

Make sure the frame type exists in `pipecat.frames.frames`. Check spelling and capitalization.

### Import errors

Make sure pipecat-ai is installed in your environment. The CLI requires pipecat-ai to be importable.

## Contributing

To extend the testing infrastructure:

1. **Add new serialization features** - Edit `pipecat/src/pipecat/tests/serialization.py`
2. **Add new validation logic** - Edit `pipecat/src/pipecat/tests/test_runner.py`
3. **Enhance CLI output** - Edit `pipecat_cli/commands/test.py`
4. **Add examples** - Create new processors in `examples/`

All code should follow existing patterns and include docstrings.
