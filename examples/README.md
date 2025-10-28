# Testing Custom Frame Processors

This directory contains examples of custom frame processors and how to test them using `pipecat test`.

## Example: UppercaseProcessor

The `uppercase_processor.py` file contains a simple processor that converts text to uppercase.

### Running Tests

**Exploratory mode** (no expected output):
```bash
pipecat test uppercase_processor.py --frames test_uppercase_exploratory.json
```

This will show you what frames are output, which you can then use to create expected output.

**Validation mode** (with expected output):
```bash
pipecat test uppercase_processor.py --frames test_uppercase.json
```

This will validate that the processor outputs match the expected frames.

**Verbose mode** (show detailed frame data):
```bash
pipecat test uppercase_processor.py --frames test_uppercase.json --verbose
```

## Test File Format

Test files are JSON with the following structure:

```json
{
  "input_frames": [
    {"type": "TextFrame", "text": "hello world"}
  ],
  "expected_output": [
    {"type": "TextFrame", "text": "HELLO WORLD"}
  ]
}
```

- `input_frames`: Required. Array of frames to send to the processor.
- `expected_output`: Optional. If provided, the test validates output matches. If omitted, the test runs in exploratory mode and displays the output.

## Creating Your Own Processor Tests

1. Write your custom processor that extends `FrameProcessor`
2. Create a JSON test file with input frames
3. Run in exploratory mode first to see the output
4. Add `expected_output` to validate behavior
5. Run tests as part of your development workflow

## Frame Types

Common frame types you can use in tests:
- `TextFrame` - Text data (fields: `text`)
- `EndFrame` - End of stream marker
- `StartFrame` - Start of stream marker
- `OutputAudioRawFrame` - Raw audio data (fields: `audio`, `sample_rate`, `num_channels`)
- `TranscriptionFrame` - Transcribed text (fields: `text`, `user_id`, `timestamp`)

See the [Pipecat documentation](https://docs.pipecat.ai) for a complete list of frame types.
