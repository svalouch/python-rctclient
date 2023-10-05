# Changelog

All notable changes to this project will be documented in this file.

## Release 0.0.5 - unreleased

### Breaking changes

- Bump minimum Python version to `3.9` (Debian Bullseye).
- Migrate project to `pyproject.toml`, managed by [Poetry](https://python-poetry.org/docs/).

### Documentation

- Add page to document inverter bitfields and enumerations.
- Add more fault codes and a warning that the added codes overflow the bitfield.
- Update description for ``battery.bat_status`` in the App mapping after RCT added a proper name to it, also add a description to the field in the Registry.

## Release 0.0.4 - 2023-10-05

### Documentation

- Add a page showing the overview screens of the RCT Power app and which OIDs are used to display the values.
- Mention that some behaviours and the entire content of the registry is an implementation detail of the vendor and are
  not mandated by the protocol itself and as such may not apply to other implementations.
- New page `Faults` for interpreting the `fault[*].flt` responses in RCT devices.
- Split documentation by moving the vendor-specific (aka RCT Inverter) parts to their own section (Registry, Faults and
  App mapping).
- Protocol overview:
  - Add section about lack of protocol-level error handling.
  - Add note about `EXTENSION` commands, their structure is unknown.
  - Document what is known about `READ_PERIODICALLY` and how it is supposed to work with vendor devices.
  - Mention checksum algorithm.
  - List all known commands as well as reserved ones.
  - Describe plant communication, which has not been tested yet.
- CLI invocation: Bash-completion activation changed with newer versions of `Click`.
- CLI: Document why there is now write support in the CLI.

### Features

- `Command` has new functions `is_write` and `is_response` to help working with received frames.
- `Command` learned about `READ_PERIODICALLY`, but it has not been tested yet.
- `Command` learned about the `PLANT_` equivalents of the other commands.

### Bugfixes

- CLI: Implement support for `Click 8.1` caused by API changes related to custom completions (Issue #17, PR #18).
- Make setuptools happy again by adhering to `PEP-508`.

### Dependency changes

- `Click`: Version `7.0` is the new minimum, it supported custom completion functions for the first time
- `Click`: Version `8.1` is the new maximum, to guard against API changes during unconditionally updating the
  dependencies.

## Release 0.0.3 - 2021-05-22

### Breaking changes

#### Receiving of frames has been completely reworked

It now uses a streaming approach where parts are decoded (almost) as soon as they are received instead of waiting for
the entire frame to be received. This was done in order to allow for more flexible handling. The correctness of the
data still cannot be determined before the entire frame has been received and the CRC16 checksum indicating correct
reception.

Except for invalid or unsupported (EXTENSION) commands, which will raise an exception and abort consumption, the
properties of `ReceiveFrame` are now populated as soon as possible and no longer raise an exception when accessed
before the frame is `complete()`.

**Rationale**: The main use case is the detection and handling of frames with invalid length field. As the correctness
of the frame could previously only be determined after it the advertised amount of data was received, frames that
advertise an abnormal amount of data consumed tens or hundreds of valid frames with no way for the application to
determine what was wrong. With the change, the application can now check for command and length, and abort the frame if
it seems reasonable. For example when it detects that a frame that carries a `DataType.UINT8` field wants to consume
100 bytes, which is far larger than what is needed to transport such a small type, it can abort the frame and skip past
the beginning of the broken frame, as an alternative to keeping track of buffer contents over multiple TCP packets, in
order to loop back once it is clear that the current frame is broken.

The exception `FrameNotComplete` was removed as it was not used any more, and `InvalidCommand` was added in its place.
Furthermore, if the parser detects that it overshot (which hints at a programming error), it raises
`FrameLengthExceeded`, enabling calling code to abort the frame.

### Known issues

- Time stamps in the output of tool `timeseries2csv.py` are off by one or two (during DST) hours.

### Features

- Registry: Update with new OIDs from OpenWB.
- Tool `read_pcap.py` now makes an attempt to decode frames that are complete but have an incorrect checksum to try to
  give a better insight into what's going on.
- Tool `read_pcap.py` prints the time stamp encoded in the dump with each packet.
- `ReceiveFrame`: Add a flag to allow decoding the content of a frame even if the CRC checksum does not match. This is
  intended as a debug measure and not to be used in normal operation.
- Added type hints for `decode_value` and `encode_value`. Requires `typing_extensions` for Python version 3.7 and
  below.
- Mention that tool `csv2influx.py` is written with InfluxDB version 1.x in mind (Issue #10).
- Debugging `ReceiveFrame` now happens using the Python logging framework, using the ``rctclient.frame.ReceiveFrame``
  logger, the ``debug()`` method has been removed.
- New CLI flag ``--frame-debug``, which enables debug output for frame parsing if ``--debug`` is set as well.
- Tool `timeseries2csv.py` can now output different header formats (none, the original header, and InfluxDB 2.x
  compatible headers). The command line switch ``--no-headers`` was replaced by ``--header-format``.

### Documentation

- Disable Smartquotes (https://docutils.sourceforge.io/docs/user/smartquotes.html) which renders double-dash strings as
  a single hyphen character, and the CLI documentation can't be copy-pasted to a terminal any more without manually
  editing it before submitting. (Issue #5).

### Bugfixes

- CLI: Fix incomplete example in `read-value` help output (Issue #5).
- CLI: Change output for OIDs of type `UNKNOWN` to a hexdump. This works around the problem of some of them being
  marked as being strings when instead they carry complex data that can't easily be represented as textual data.
- Registry: Mark some OIDs that are known to contain complex data that hasn't been decoded yet as being of type
  `UNKNOWN` instead of `STRING`. Most of them cannot be decoded to a valid string most of the time, and even then the
  content would not make sense. This change allows users to filter these out, e.g. when printing their content.
- Simulator: If multiple requests were sent in the same TCP packet, the simulator returned the answer for the first
  frame that it got for all of the requests in the buffer.
- Tool `read_pcap.py` now drops a frame if it ran over the segment boundary (next TCP packet) if the new segment looks
  like it starts with a new frame (`0x002b`). This way invalid frames with very high length fields are caught earlier,
  only losing the rest of the segment instead of consuming potentially hundreds of frames only to error out on
  CRC-check.
- Tool `csv2influx.py` had a wrong `--resolution` parameter set. It has been adapted to the one used in
  `timeseries2csv.py`. Note that the table name is made up from the parameters value and changes with it (Issue #8).
- `ReceiveFrame` used to extract the address in plant frames at the wrong point in the buffer, effectively swapping
  address and OID (PR #11).

## Release 0.0.2 - 2021-02-17

### Features

- New tool `timeseries2csv.py`: Reads time series data from the device and outputs CSV data for other tools to consume.
- New tool `csv2influx.py`: Takes a CSV generated from `timeseries2csv.py` and writes it to an InfluxDB database.
- Refactored frame generation: The raw byte-stream generation for sending a frame was factored out of class `SendFrame`
  and put into its own function `make_frame`. Internally, `SendFrame` calls `make_frame`.
- CLI: Implement simple handling of time series data. The data is returned as a CSV table and the start timestamp is
  always the current time.
- CLI: Implement simple handling of the event table. The data is returned as a CSV table and the start timestamp is
  always the current time. The data is printed as hexadecimal strings, as the meaning of most of the types is now known
  yet.
- `Registry`: Add handling of enum value mappings.
- Tool `read_pcap.py`: learned to output enum values as text (from mapping in `Registry`).
- Setup: The `rctclient` CLI is only installed if the `cli` dependencies are installed.
- Tests: Some unit-tests were added for the encoding and decoding of frames.
- Tests: Travis was set up to run the unit-tests.

### Documentation

- New tools `timeseries2csv.py` and `csv2influx.py` added.
- Enum-mappings were added to the Registry documentation.
- Event table: document recent findings.
- Protocol: documentation of the basic protocol has been enhanced.
- Added this changelog file and wired it into the documentation generation.

### Bugfixes

- Encoding/Decoding: `ENUM` data types are now correctly encoded/decoded the same as `UINT8`.
- Simulator: Fix mocking of `BOOL` and `STRING`.

## Release 0.0.1 - 2020-10-07

Initial release.
