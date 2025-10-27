# Changelog

All notable changes to **Pipecat** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fixed an issue that could cause delayed answer times when calling via Twilio
  / Daily SIP.

## [0.1.5] - 2025-10-27

### Added

- Added support for Daily SIP + Twilio dial-in and dial-out use cases.

- Added support for extensions. Other packages can now register commands that
  are automatically discovered by pipecat-cli, making it easy to extend pipecat
  with additional subcommands. For example, the following adds the Pipecat Cloud
  `cloud` command.

  ```
  [project.entry-points."pipecat_cli.extensions"]
  cloud = "pipecatcloud.cli.entry_point:entrypoint_cli_typer"
  ```

### Changed

- Updated Twilio example to include calling the Twilio REST API to get the
  caller's phone number. This example can be extended to fetch custom data for
  the bot.

- Updated Telnyx example to include extracting the From number from the
  websocket connection message. The From number can be used to ID the user in
  order to customize the bot.

### Removed

- Removed `TailObserver` and `TailRunner` exports. Use `pipecat_tail` package
  directly.

### Fixed

- Fixed an issue where `audio_buffer.start_recording()` was missing from
  generated files.

## [0.1.4] - 2025-10-23

### Added

- Added support for Daily PSTN dial-in and dial-out use cases.

### Changed

- Changes the DailyTransport client examples to use the /start endpoint to
  start both local and production bots.

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
