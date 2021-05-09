# Changelog

All notable changes to this project will be documented in this file.

## Release 0.0.3 - Unreleased

**Features**

- Registry: Update with new OIDs from OpenWB.
- Tool `read_pcap.py` now makes an attempt to decode frames that are complete but have an incorrect checksum to try to
  give a better insight into what's going on.
- Tool `read_pcap.py` prints the time stamp encoded in the dump with each packet.
- `ReceiveFrame`: Add a flag to allow decoding the content of a frame even if the CRC checksum does not match. This is
  intended as a debug measure and not to be used in normal operation.

**Documentation**

- Disable Smartquotes (https://docutils.sourceforge.io/docs/user/smartquotes.html) which renders double-dash strings as
  a single hyphen character, and the CLI documentation can't be copy-pasted to a terminal anymore without manually
  editing it before submitting. (Issue #5).

**Bugfixes**

- CLI: Fix incomplete example in `read-value` help output (Issue #5).
- CLI: Change output for OIDs of type `UNKNOWN` to a hexdump. This works around the problem of some of them being
  marked as being strings when instead they carry complex data that can't easily be represented as textual data.
- Registry: Mark some OIDs that are known to contain complex data that hasn't been decoded yet as being of type
  `UNKNOWN` instead of `STRING`. Most of them cannot be decoded to a valid string most of the time, and even then the
  content would not make sense. This change allows users to filter these our, e.g. when printing their content.
- Simulator: If multiple requests were sent in the same TCP paket, the simulator returned the answer for the first
  frame that it got for all of the requests in the buffer.
- Tool `read_pcap.py` now drops a frame if it ran over the segment boundary (next tcp packet) if the new segment looks
  like it starts with a new frame (`0x002b`). This way invalid frames with very high length fields are caught earlier,
  only losing the rest of the segment instead of consuming potentially hundrets of frames only to error out on
  CRC-check.

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
