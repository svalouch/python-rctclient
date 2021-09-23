
########
Overview
########

The protocol is based on TCP and is based around commands targeting object IDs that work similar to OIDs in SNMP.
Messages are protected against transfer failures by means of a 2-byte CRC checksum. The protocol in itself isn't very
complicated, but there are some things like escaping, length calculation and plant communication to look out for.

There is no method to tell that a communication was not understood at the protocol level, meaning that it is up to the
implementor to figure out a way to let the client know that something was not understood. Vendor devices may simply
fail to respond or respond with an empty payload, or do something else. It is advised to pay attention to the checksums
and errors during payload decoding. Vendor devices do facilitate special OIDs that contain information about their
state, but that is an implementation detail of the specific devices. If implementing an application, one could specify
some OIDs that can be used to report if the previous command resulted in an error, for example.

Protocol Data Units
*******************
The Protocol Data Units (PDU) are comprised of:

#. A start token (``+``)
#. The command byte
#. The length of the ID and data payload
#. For plant communication, the address, omitted for standard frames
#. The object ID
#. Payload (optional)
#. CRC16 checksum

Data is encoded as big endian, a leading ``0x00`` before the start token is allowed.

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

.. hint::

   The OIDs are actually an implementation detail of the device. The protocol only defines that they are 4 bytes in
   length. All other details like the data type, whether a payload can be used and so on are up to the implementer, so
   in order to implement your own application, you would simply define your own OIDs with associated data types instead
   of using the ones in the :ref:`registry` or the examples.

Escaping
========

Certain characters are escaped by inserting the escape token ``-`` (``0x2d``) into the stream before the byte that
requires escaping. When the start token (``+``) or escape token is encountered in the data stream (unless it's the very
first byte for the start token), the escape token is inserted before the token that it escapes. On decoding, when the
escape token is encountered, the next character is interpreted as data and not as start token or escape token. Thus, if
the task is to encode a plus sign (usually in a string), then a minus is added *before* the plus sign to escape it.

Checksum
========
The checksum algorithm used is a special version of CRC16 using a CCITT polynom (``0x1021``). It varies from other
implementation by appending a NULL byte to the input if its length is uneven before commencing with the calculation.


Commands
********
There are two groups of commands: *Standard* communication commands that are sent to a device and the device replies,
as well as *Plant* communication commands, which are standard commands ORed with ``0x40``.

Commands not listed here are either not known or are reserved, and should not be used with the devices as it is not
known what effect this could have.

======================= ============= ======================================================
Command                 Value         Description
======================= ============= ======================================================
READ                    ``0x01``      Request the current value of an object ID. No payload.
WRITE                   ``0x02``      Write the payload to the object ID.
LONG_WRITE              ``0x03``      When writing "long" payloads.
*RESERVED*              ``0x04``
RESPONSE                ``0x05``      Normal response to a read or write command.
LONG_RESPONSE           ``0x06``      Response with a "long" payload.
*RESERVED*              ``0x07``
READ_PERIODICALLY       ``0x08``      Request automatic, periodic sending of an OIDs value.
*Reserved*              ``0x09-0x40``
PLANT_READ              ``0x41``      *READ* for plant communication.
PLANT_WRITE             ``0x42``      *WRITE* for plant communication.
PLANT_LONG_WRITE        ``0x43``      *LONG_WRITE* for plant communication.
*RESERVED*              ``0x44``
PLANT_RESPONSE          ``0x45``      *RESPONSE* for plant communication.
PLANT_LONG_RESPONSE     ``0x46``      *LONG_RESPONSE* for plant communication.
*RESERVED*              ``0x47``
PLANT_READ_PERIODICALLY ``0x48``      *READ_PERIODICALLY* for plant communication.
EXTENSION               ``0x3c``      Unknown, see below.
======================= ============= ======================================================

The EXTENSION command
=====================
EXTENSION does not follow the semantics of other commands and cannot be parsed by *rctclient*. It is believed to be a
single-byte payload; a frame often observed is ``0x2b3ce1``, which is sent by the official app uppon connecting to a
device to "switch to COM protocol". In this case, ``0xe1`` is the commands payload, and a normal frame follows
immediately after, which leads to the conclusion of this command always being three bytes in length.

READ_PERIODICALLY
=================
Registers a OID for being sent periodically. The device will send the current value of the OID at an interval defined
in ``pas.period`` (see :ref:`registry`). Up to 64 OIDs can be registered with vendor devices, but the protocol does not
impose a limit, and all registered OIDs will be served at the same interval setting. When sending this command, the
device immediately responds with the current value of the OID, and will then periodically send the current value.

To disable, set ``pas.period`` to 0, which clears the list of registered OIDs, effectively disabling the feature. No
method exists for removing a single OID, one has to clear it, then set ``pas.period`` and re-register all desired OIDs.

.. warning::

   The implementation has not been tested yet, please don't hesitate to open an issue if you run into problems or have
   more insight into the matter.

Frame length
************

The frame length is 1 byte for all commands except *LONG_RESPONSE* and *LONG_WRITE* and their *PLANT_* counterparts,
which use 2 bytes (most siginificant byte first). The length denotes how many bytes of data follow it. Escape tokens
are not counted, and it does not include the two-byte header before it (start token and command) and does also not
include the two-byte CRC16 at the end of the frame. In order to fully receive a frame, after reversing any escaping,
the buffer should therefor hold ``2 + length + 2`` bytes.

Plant communication
*******************
With plant communication, one device acts as plant leader and relays commands addressed at subordinate devices to them
and their responses back to the client. Vendor devices need to be linked together, each has its own ``address``.

To use plant communication, use the ``PLANT_*`` variations of the normal commands (``READ`` → ``PLANT_READ`` and so on)
and supply the ``address`` property. The leader device forwards the command to the device that has the address set, all
other devices ignore the frame. The answer from the addressed device is then sent back to the client by the leader,
with a ``PLANT_*`` response command and the ``address`` set to that of the addressed device.

.. warning::

   Plant communication has not been tested and the implementation simply follows what is known. The authors do not have
   a setup to test this kind of communication. We'd greatly appreciate traffic dumps of actual plant communication or
   feedback if it works or not.

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
