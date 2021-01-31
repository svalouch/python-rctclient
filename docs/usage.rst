
.. _usage:

#####
Usage
#####

This page describes the basic concepts of the module and how to use the different parts. See also the short
:ref:`security` section below.

Parts overview
**************

The module offers a range of classes and methods that allow for a relatively modular workflow. This makes it possible
to write a client application (the main goal of the module), but also a :ref:`simulator` to develop against. With a
little extra work, it is even possible to read from a `pcap` file and check past communication captured using `tcpdump`
or `wireshark`.

One thing that is not provided is methods for network communication, it is a
`sans I/O <https://sans-io.readthedocs.io/>`_ library. This effectively means that the user has to bring in their own
code for doing the network communication (though with the :ref:`CLI` there's some optional support for doing simple
calls). This might sound odd at first, but it allows for the library to be used in a very modular way, by not dictating
how network-communication is handled, and it frees the developers of this library from having to support different
communication schemes. There are some examples further down that actually deal with network communication.

Object IDs (OIDs)
=================
The protocol revolves around Object IDs (OIDs) that work similar to OIDs in `snmp`, in that they are an address that is
targeted by a command (read value from OID, send value to OID) and that is referenced in the response to such a
command. To deepen the similarities, a :ref:`registry` is provided that acts like a MIB definition file and enriches
the raw OIDs with human-readable names as well as data types for decoding/encoding and so on.

This information is kept in :class:`~rctclient.registry.ObjectInfo` objects inside a
:class:`~rctclient.registry.Registry` instance conveniently provided as `rctclient.registry.REGISTRY` for easier
consumption.

Looking at the information objects, they contain a ``name`` such as ``battery.soc``, an optional description ``SOC
(State of charge)`` and most importantly, the ``request_data_type`` and ``response_data_type`` fields. These fields are
used to specify how to encode or decode values for the particular OID. In most cases, the response type is the same as
the request type, but there are a few exceptions: :ref:`protocol-timeseries` and :ref:`protocol-event-table`.

Registry
========
The :class:`rctclient.registry.Registry` class maintains a list of OIDs. As the list is quite long and for the users
convenience, a module-scope instance is available as ``REGISTRY``.

Most of the examples will assume an import like the following:

.. code-block:: python

   from rctclient.registry import REGISTRY as R

This makes the registry available as ``R``. It provides a set of functions to query
:class:`~rctclient.registry.ObjectInfo` instances that describe OIDs as explained above. A complete list of the OIDs
shipped with the module is available at the :ref:`registry` page.

The most commonly used functions are :func:`~rctclient.registry.Registry.get_by_id` and
:func:`~rctclient.registry.Registry.get_by_name` that return a `ObjectInfo` instance for the OID or the name, observe:

.. code-block:: pycon

   >>> from rctclient.registry import REGISTRY as R
   >>> oinfo_name = R.get_by_name('battery.soc')
   >>> oinfo_name
   <ObjectInfo(id=0x959930BF, name=battery.soc)>
   >>> oinfo_name.description
   'SOC (State of charge)'
   >>> oinfo_id = R.get_by_id(0x959930BF)
   >>> oinfo_id
   <ObjectInfo(id=0x959930BF, name=battery.soc)>

For some OIDs, additional information such as a textual description or a unit like ``V`` for volts is available.

Frames
======
Individual requests and responses that are sent to or received from a device are called "Frame". These are the raw
bytes that are exchanged between client and server (device).

Frames contain a command such as *read* and a OID such as ``0x959930BF``. Some commands (such as *write*) can contain a
payload and there's a way to communicate to a network of devices, called plant communication which has not been tested
with this library yet. The details of the encoding of the mentioned parts is not of relevance here.

For creating a frame that is to be sent to a device, there's two ways:

* Creating it directly using :func:`~rctclient.frame.make_frame`, which takes the above mentioned input parameters and
  returns the byte stream ready to be sent
* Using the higher-level class :class:`~rctclient.frame.SendFrame` which internally calls ``make_frame``, but stores
  the input parameters as well. This is especially useful for checking how things work, as its ``__repr__`` dunder
  pretty-prints both input and output.

For receiving, there's the :class:`~rctclient.frame.ReceiveFrame`, which is fed with raw data from the wire and that
signals when a complete frame is received.

SendFrame
---------
:class:`~rctclient.frame.SendFrame` is used to craft the byte stream used to send a request to the device. Uppon
constructing the frame, it automatically crafts the byte stream, which is then available in the ``data`` property and
can be sent to the device.

.. note::

   The payload has to be encoded before passing it to ``SendFrame`` e.g. using :func:`~rctclient.utils.encode_value`.

The following example crafts a read command for the battery state of charge (``battery.soc``). The data that is to be
sent via a network socket can be read from ``frame.data`` in the end:

.. code-block:: pycon

   >>> from rctclient.registry import REGISTRY as R
   >>> from rctclient.frame import SendFrame
   >>> from rctclient.types import Command
   >>>
   >>> oinfo = R.get_by_name('battery.soc')
   >>> frame = SendFrame(command=Command.READ, id=oinfo.id)
   >>> frame
   <SendFrame(command=1, id=0x959930BF, payload=0x)>
   >>> frame.data.hex()
   '2b0104959930bf0d65'

make_frame
----------
As discussed earlier, :func:`~rctclient.frame.make_frame` is used internally by ``SendFrame``. It basically behaves the
same but does not require object instantiation and all that comes with it, but instead simply returns the generated
bytes to be sent.

.. code-block:: pycon

   >>> from rctclient.registry import REGISTRY as R
   >>> from rctclient.frame import make_frame
   >>> from rctclient.types import Command
   >>>
   >>> oinfo = R.get_by_name('battery.soc')
   >>> frame_data = make_frame(command=Command.READ, id=oinfo.id)
   >>> frame_data.hex()
   '2b0104959930bf0d65'

ReceiveFrame
------------
:class:`rctclient.frame.ReceiveFrame` is used to receive a frame of data from the device. It is designed so that it can
``consume`` a frame as it is received over the network. The instance signals when a frame has been received
(``complete()`` returns *True*) or raise an exception when an error occurs, such as a checksum mismatch. The
``consume`` function returns the amount of bytes it consumed, which allows for removing the consumed data from the
buffer and start receiving the next frame immediately, which will become clearer in the examples below.

If the checksum does not match, an exception (:class:`~rctclient.exceptions.FrameCRCMismatch`) is raised that contains
the received and computed checksums for debugging and also carries the amount of consumed bytes, so one can slice off
those bytes and start with the next frame. Due to the way the devices work, CRC mismatches are not uncommon, and even
a matching checksum does not guarantee that the data in the payload is complete. More on that later.

As an example, we'll read the frame data from the above *SendFrame* example as an input to the ReceiveFrames consume
method. The output above was (in hexadecimal notation) ``2b0104959930bf0d65`` which can be transformed back into a byte
stream using the ``bytearray.fromhex`` method:

.. code-block:: python

   from rctclient.registry import REGISTRY as R
   from rctclient.frame import ReceiveFrame

   frame = ReceiveFrame()
   print(frame.complete())
   #> False

   data = bytearray.fromhex('2b0104959930bf0d65')
   consumed_bytes = frame.consume(data)
   print(f'Consumed: {consumed_bytes}, input length: {len(data)}')
   #> Consumed: 9, input length: 9

   print(frame)
   #> <ReceiveFrame(cmd=1, id=959930bf, address=0, data=)>
   print(R.get_by_id(frame.id))
   #> <ObjectInfo(id=0x959930BF, name=battery.soc)>

(This script is complete, it should run "as is")

This is a rather constructed use case, as normally the data to parse would be a response frame from the device. But it
shows the modularity of the approach. Now, using the ``read-value`` subcommand to the :ref:`cli` tool, extract the
payload from a real response. This safes us from needing to explain the entire network handling in this section. By
starting the tool in ``--debug`` mode, the payload can be read as hex string:

.. code-block:: shell-session

   $ rctclient --debug read-value -h 192.168.0.1 --name battery.soc
   2020-10-02 15:11:02,367 - rctclient.cli - INFO - rctclient CLI starting
   2020-10-02 15:11:02,367 - rctclient.cli - DEBUG - Object info by name: <ObjectInfo(id=0x959930BF, name=battery.soc)>
   2020-10-02 15:11:02,367 - rctclient.cli - DEBUG - Connecting to host
   2020-10-02 15:11:02,368 - rctclient.cli - DEBUG - Connected to 192.168.19.13:8899
   2020-10-02 15:11:02,431 - rctclient.cli - DEBUG - Received 14 bytes: 002b0508959930bf3f590f868810
   2020-10-02 15:11:02,432 - rctclient.cli - DEBUG - Frame consumed 14 bytes
   2020-10-02 15:11:02,432 - rctclient.cli - DEBUG - Got frame: <ReceiveFrame(cmd=5, id=959930bf, address=0, data=3f590f86)>
   0.8478931188583374

The raw byte stream that the device responded with is ``002b0508959930bf3f590f868810`` in hexadecimal notation. The
following example uses it to manually craft a response frame and also demonstrates how to decode the payload:

.. code-block:: python

   from rctclient.registry import REGISTRY as R
   from rctclient.frame import ReceiveFrame
   from rctclient.utils import decode_value

   frame = ReceiveFrame()
   frame.consume(bytearray.fromhex('002b0508959930bf3f590f868810'))

   # check that the frame is complete
   print(frame.complete())
   #> True

   # take a look at the frame
   print(frame)
   #> <ReceiveFrame(cmd=5, id=959930bf, address=0, data=3f590f86)>

   # get information about the object
   oinfo = R.get_by_id(frame.id)
   print(oinfo.name, oinfo.response_data_type)
   #> battery.soc DataType.FLOAT

   # decode the value using the response data type
   value = decode_value(oinfo.response_data_type, frame.data)
   print(value)
   #> 0.8478931188583374

(This script is complete, it should run "as is")

Encoding and decoding data
==========================
The two functions :func:`rctclient.utils.decode_value` and :func:`rctclient.utils.encode_value` are used to transform
data between high-level data types and byte streams in both directions.

Each OID (see above) has a data type associated for sending and one for receiving (though they are the same for most
OIDs). To encode a value for sending with a `SendFrame`, supply the ``request_data_type`` as first parameter to
``encode_value``. For the opposite direction, supply the ``response_data_type`` to ``decode_value`` along with the
content from the ``data`` attribute from the completed `ReceiveFrame`.

If the data can't be decoded, a ``struct.error`` is raised by the `struct` module.

.. warning::

   It is not uncommon for the device to send incomplete payload along with a valid checksum. Always catch the
   exceptions raised by the functions.

Basic workflow
**************
The most basic workflow involves sending a request to the device and receive the response:

#. Open a TCP socket to the device.
#. If payload is to be sent (write commands), use :func:`~rctclient.utils.encode_value` to encode the data.
#. Craft a frame (using :class:`~rctclient.frame.SendFrame` or :func:`~rctclient.frame.make_frame`) with the correct
   object ID and command set and, if required, include the payload.
#. Send the frame via a TCP socket to the device.
#. Read the response into a :class:`~rctclient.frame.ReceiveFrame`
#. Once complete, decode the response value using :func:`~rctclient.utils.decode_value`
#. Repeat steps 2-6 as long as required.
#. Close the socket to the device.

Basic example
*************
Assuming the :ref:`simulator` is running in its default config (listening on ``localhost:8899``) by starting it without
parameters like so: ``rctclient simulator``, the following script can be used to query for the battery state of charge
(SOC) value:

.. code-block:: python

   #!/usr/bin/env python3

   import socket, select, sys
   from rctclient.frame import ReceiveFrame, make_frame
   from rctclient.registry import REGISTRY as R
   from rctclient.types import Command
   from rctclient.utils import decode_value

   # open the socket and connect to the remote device:
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   sock.connect(('localhost', 8899))

   # query information about an object ID (here: battery.soc):
   object_info = R.get_by_name('battery.soc')

   # construct a byte stream that will send a read command for the object ID we want, and send it
   send_frame = make_frame(command=Command.READ, id=object_info.object_id)
   sock.send(send_frame)

   # loop until we got the entire response frame
   frame = ReceiveFrame()
   while True:
       ready_read, _, _ = select.select([sock], [], [], 2.0)
       if sock in ready_read:
           # receive content of the input buffer
           buf = sock.recv(256)
           # if there is content, let the frame consume it
           if len(buf) > 0:
               frame.consume(buf)
               # if the frame is complete, we're done
               if frame.complete():
                   break
           else:
               # the socket was closed by the device, exit
               sys.exit(1)

   # decode the frames payload
   value = decode_value(object_info.response_data_type, frame.data)

   # and print the result:
   print(f'Response value: {value}')

(This script is complete, it should run "as is")

When run against a real device (by exchanging the ``localhost`` above with the address of the device), the result is
like this:

.. code-block:: shell-session

   $ ./basic-example.py
   Response value: 0.6453145742416382

Obviously, this example lacks any error handling for the sake of simplicity.

Caveats
*******
This section leaves the protocol part and hops into the real world, to the real hardware devices. Some things are
important to know as they can lead to confusion. The inverters are embedded devices and take some shortcuts when it
comes to network communication.

.. _security:

Security
========

**There is none.**

The protocol itself has no security primitives such as authentication and encryption. The device itself does not allow
the usage of TLS (Transport Layer Security) or other encryption standards. Whoever can reach the device via the network
(be it via ethernet cable or the WIFI access point the devices create by default) has full control over all settings of
the device. The official app *does* require passwords to access more than just the basics, but that password is only
used to enable features in the app itself and is not sent over the wire ever. It is really important to understand this
when connecting the device to any network.

.. warning::

   To re-iterate: There is no security, anyone who can reach the device on the network has full control over it.

.. _incomplete-responses:

Incomplete, incorrect or missing responses
==========================================
The devices are not meant to communicate with multiple network clients simultaneously. They will interrupt what they
are doing when another request comes in. This results in incomplete frames that have a valid checksum, as the device
may be interrupted while preparing the payload, then calculates the checksum over the partial response and send it over
the wire. This is especially noticable when requesting large OIDs such as strings or the :ref:`protocol-timeseries` or
:ref:`protocol-event-table` OIDs, as they appear to be cut at arbitrary places, yet the attached checksum matches the
calculated checksum.

Sometimes the response can be lost alltogether, this can be seen in the app as timeouts, or when it appears that some
parts of a table (e.g. the battery overview) are initially empty and are filled in after all the other values on the
next poll.

If the device is communicating with the vendors servers for external control, this communication could be impacted by
having the app open or using another client to query the device.

When creating programs that communicate with the devices (which is the sole purpose of this module), always take into
account that queries may simply get lost or have incomplete payload, so make sure to implement some sort of retry
mechanism.

Conclusion
**********
With the information provided on this page it should be possible to create client applications with ease. The
:ref:`CLI` tool may also give some insights into how things work, they're implemented in the ``cli.py`` file, the
:ref:`simulator` can be found in ``simulator.py``.

If things are still unclear, of bugs are found or if there are any questions, don't hestitate to get in contact using
the projects issue tracker in GitHub.
