
########
Overview
########

The protocol is based on TCP and is based around commands targeting object IDs that work similar to OIDs in SNMP.
Messages are protected against transfer failures by means of a 2-byte CRC checksum. The protocol in itself isn't very
complicated, but there are some things like escaping, length calculation and plant communication to look out for.

The Protocol Data Units (PDU) are comprised of:

#. A start token (``+``)
#. The command byte
#. The length of the ID and data payload
#. For plant communication, the address, omitted for standard frames
#. The object ID
#. Payload (optional)
#. CRC16 checksum

Data is encoded as big endian.

+----------------+-------+---------------------------------------+
| Element        | Bytes | Remarks                               |
+================+=======+=======================================+
| Start token    | 1     | ``+`` character, ``0x2b``.            |
+----------------+-------+---------------------------------------+
| Command        | 1     |                                       |
+----------------+-------+---------------------------------------+
| Payload length | 1     | All but long read / long write        |
|                +-------+---------------------------------------+
|                | 2     | Long read / long write                |
+----------------+-------+---------------------------------------+
| Address        | 4     | For plant communication               |
|                +-------+---------------------------------------+
|                | 0     | Omitted for standard frames           |
+----------------+-------+---------------------------------------+
| Object ID      | 4     |                                       |
+----------------+-------+---------------------------------------+
| Payload        | N     | Payload is optional for some commands |
+----------------+-------+---------------------------------------+
| CRC16          | 2     |                                       |
+----------------+-------+---------------------------------------+

Escaping
********

Certain characters are escaped by inserting the escape token ``-`` (``0x2d``) into the stream before the byte that
requires escaping. When the start token (``+``) or escape token is encountered in the data stream (unless it's the very
first byte for the start token), the escape token is inserted before the token that it escapes. On decoding, when the
escape token is encountered, the next character is interpreted as data and not as start token or escape token. Thus, if
the task is to encode a plus sign (usually in a string), then a minus is added *before* the plus sign to escape it.

Commands
********

============= ======== ======================================================
Command       Value    Description
============= ======== ======================================================
READ          ``0x01`` Request the current value of an object ID. No payload.
WRITE         ``0x02`` Write the payload to the object ID.
LONG_WRITE    ``0x03`` When writing "long" payloads.
RESPONSE      ``0x05`` Normal response to a read or write command.
LONG_RESPONSE ``0x06`` Response with a "long" payload.
EXTENSION     ``0x3c`` Unknown.
============= ======== ======================================================

Frame length
************

The frame length is 1 byte for all commands except *LONG_RESPONSE* and *LONG_WRITE*, which use 2 bytes (most
siginificant byte first). The length denotes how many bytes of data follow it. Escape tokens are not counted, and it
does not include the two-byte header before it (start token and command) and does also not include the two-byte CRC16
at the end of the frame. In order to fully receive a frame, after reversing any escaping, the buffer should therefor
hold ``2 + length + 2`` bytes.

Frame by example
****************
The following is a dissection of a frame sent to the device (read request) and its response from the device.

Request
=======

Setting:

* *READ* request, so command is ``0x01``
* The OID ``battery.soc`` is ``0x959930BF``
* No payload and no address and nothing to escape.

::

   Data: 2b 01 04 959930bf 0d65

   ID:   1  2  3  4        5

== ============ =========================================================
ID Bytes        Description
== ============ =========================================================
1  ``2b``       Start token
2  ``01``       Command: *READ*
3  ``04``       Length of the data that follows, it's the OID of 4 bytes.
4  ``959930bf`` Data, which in this example consists of the OID only.
5  ``0d65``     CRC16 checksum.
== ============ =========================================================

Response
========

The response for the command (read battery state of charge) is disected below. The string has been split up for ease of
reading, but it is a single byte stream.

The raw response looks like this (in hexadecimal): ``002b0508959930bf3e97b1919c86``
::

   Data: 00 2b 05 08 959930bf 3e97b191 9c86

   ID:   1  2  3  4  5        6        7

== ============ ==============================================================================
ID Bytes        Description
== ============ ==============================================================================
1  ``00``       Data before the start of the command. It is ignored.
2  ``2b``       Start token, all data before this is ignored.
3  ``05``       Command, this is a `RESPONSE`.
4  ``08``       Length field, 4 byte OID and 4 byte payload.
5  ``959930bf`` The OID this response carries.
6  ``3e97b191`` Payload data, as per the OID this is a big endian float value of roughly 0.296
7  ``9x86``     CRC16 checksum.
== ============ ==============================================================================

The payload in this example is a big endian floating point number. The data type can be looked up in the
:ref:`Registry`.
