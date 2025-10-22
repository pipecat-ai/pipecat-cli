# Changelog

All notable changes to **Pipecat** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-10-22

### Added

- Added Whisker and Tail as observability options for generated projects.

### Fixed

- Fixed an issue where recording and transcription features were missing
  imports.

## [0.1.2] - 2025-10-21

### Added

- Added Python API exports for `TailObserver` and `TailRunner` from
  `pipecat-ai-tail`. Users can now import these from `pipecat_cli.tail`:
  ```python
  from pipecat_cli.tail import TailObserver, TailRunner
  ```

### Changed

- Reordered the "Next Steps" to put the client steps first.

- Aligned Google Vertex env names across services. Removed unnecessary text
  from the env.example file.

### Fixed

- Fixed an issue where the Vanilla JS client code required the
  `@pipecat-ai/small-webrtc-transport`.

## [0.1.1] - 2025-10-20

### Added

- Added `on_audio_data` and `on_transcript_update` event handlers to bot file
  templates.

- Added `pyright` to the `dev` `dependency-groups`.

## [0.1.0] - 2025-10-17

### Added

- Core CLI commands:

  - `pipecat init` - Interactive project scaffolding
  - `pipecat tail` - Real-time bot monitoring
  - `pipecat cloud` - Deployment and management commands for Pipecat Cloud

- `pc` alias for all commands
