# Changelog

All notable changes to this project will be documented in this file.

## Release 0.0.3 - Unreleased

**Features**

**Documentation**

- Disable Smartquotes (https://docutils.sourceforge.io/docs/user/smartquotes.html) which renders double-dash strings as
  a single hyphen character, and the CLI documentation can't be copy-pasted to a terminal anymore without manually
  editing it before submitting. (Issue #5).

**Bugfixes**

- CLI: Fix incomplete example in `read-value` help output (Issue #5).

## Release 0.0.2 - 2021-02-17

**Features**

- New tool `timeseries2csv.py`: Reads time series data from the device and outputs CSV data for other tools to consume.
- New tool `csv2influx.py`: Takes a CSV generated from `timeseries2csv.py` and writes it to an InfluxDB database.
- Refactored frame generation: The raw byte-stream generation for sending a frame was factored out of class `SendFrame`
  and put into its own function `make_frame`. Internally, `SendFrame` calls `make_frame`.
- CLI: Implement simple handling of time series data. The data is returned as a CSV table and the start timestamp is
  always the current time.
  the start timestamp yet.
- CLI: Implement simple handling of the event table. The data is returned as a CSV table and the start timestamp is
  always the current time. The data is printed as hexadecimal strings, as the meaning of most of the types is now known
  yet.
- `Registry`: Add handling of enum value mappings.
- Tool `read_pcap.py`: learned to output enum values as text (from mapping in `Registry`).
- Setup: The `rctclient` CLI is only installed if the `cli` dependencies are installed.
- Tests: Some unit-tests were added for the encoding and decoding of frames.
- Tests: Travis was set up to run the unit-tests.

**Documentation**

- New tools `timeseries2csv.py` and `csv2influx.py` added.
- Enum-mappings were added to the Registry documentation.
- Event table: document recent findings.
- Protocol: documentation of the basic protocol has been enhanced.
- Added this changelog file and wired it into the documentation generation.

**Bugfixes**

- Encoding/Decoding: `ENUM` data types are now correctly encoded/decoded the same as `UINT8`.
- Simulator: Fix mocking of `BOOL` and `STRING`.

## Release 0.0.1 - 2020-10-07

Initial release.
