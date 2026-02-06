# Changelog

All notable changes to this project will be documented in this file.

## [1.0.1] - 2026-02-06

### Fixed
- Fixed Python 3.9 compatibility issues by replacing union type syntax (`|`) with `Optional` and `Union` from typing module
- Added missing `environment.yml` for Conda CI workflow
- Improved test robustness with better error handling for network-dependent tests

### Changed
- Updated minimum Python version requirement to 3.9 (from 3.8)

## [1.0.0] - 2025-02-04

### Added
- Initial release of Seekify.
- Unified text search API supporting Google, Bing, DuckDuckGo, Brave, Yahoo, Yandex, Mojeek, Grokipedia.
- Multimedia search support (Images, Videos) via DuckDuckGo.
- News search support via Bing, DuckDuckGo, Yahoo.
- Book search support via Anna's Archive.
- Robust CLI tool with export capabilities (CSV, JSON).
- Full proxy support (HTTP/SOCKS5).
- Comprehensive test suite.
