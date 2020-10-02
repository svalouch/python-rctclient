
########
Overview
########

The protocol is based on TCP and is based around commands targeting object IDs that work similar to OIDs in SNMP.
Messages are protected against transfer failures by means of a 2-byte CRC checksum.

The Protocol Data Units (PDU) are comprised of:

#. A start token (``+``)
#. The command byte
#. The length of the payload
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

Commands
********

* `READ`: ``0x01``, request the current value of an object ID. No payload.
* `WRITE`: ``0x02``, write the payload to the object ID.
* `LONG_WRITE`: ``0x03``, when writing "long" payloads.
* `RESPONSE`: ``0x05``, normal response to a read or write command.
* `LONG_RESPONSE`: ``0x06``, response with a "long" payload.
* `EXTENSION`: ``0x3c``.


