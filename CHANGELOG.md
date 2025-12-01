# Changelog

All notable changes to Brutally Honest AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-01

### Added
- Centralized design system with CSS variables
- Dark mode support with `[data-theme="dark"]`
- OTA deployment with version control
- SSH access via brutallyhonest.io domain
- Fact validation against document knowledge base
- Profile management (clients, brands, persons)
- Multi-file audio transcription
- Interview analysis with voice metrics
- Real-time WebSocket notifications

### Changed
- Migrated all hardcoded colors to design tokens
- Updated deployment scripts to use brutallyhonest.io
- Improved responsive design for mobile

### Fixed
- Frontend WebSocket port conflicts
- Service restart issues on deployment

## [0.9.0] - 2025-11-28

### Added
- Initial release
- Whisper transcription
- LLAMA analysis
- Document upload and search
- ESP32S3 device support

