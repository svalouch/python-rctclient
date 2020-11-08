
.. _tools:

#################
Tools and scripts
#################

Extra scripts and tools can be found in the ``tools`` subfolder of the repository. They usually require extra
dependencies or cater to special use-cases and are thus not integrated into the main :ref:`cli` tool. The tools usually
lack a sophisticated user interface and error handling is kept at a minimum.

histogram2csv.py
****************
This tool exports a days worth of histogram data from the device and stores it as CSV file. It requires `click` and
`pytz`.

The script assumes that the measurement interval is `5 minutes` (meaning that ``logger.log_rate`` equals ``300``).
The script requires a few parameters, the ``--help`` output lists them all:

::

   Usage: histogram2csv.py [OPTIONS] DAY_BEFORE_TODAY

     Extract a day of history data from the RCT device. This tool connects to a
     device and reads the fine-grained "minute" values of a day which is
     DAY_BEFORE_TODAY number of days before the current day.

     The output format is CSV. If --output is not given, then a name is
     constructed from the current date. Specify "-" to have the tool print the
     table to standard output, for use with other tools.

   Options:
     -h, --host TEXT     Host to query  [required]
     -p, --port INTEGER  Port on the host to query [8899]
     -o, --output FILE   Output file (use "-" for standard output), omit for
                         "data_<date>.csv"

     -H, --no-headers    When specified, does not output the column names as
                         first row

     --time-zone TEXT    Timezone of the device (not the host running the script)
                         [Europe/Berlin]

     -q, --quiet         Supress output
     --help              Show this message and exit.

The most important one is the argument at the end, called ``DAY_BEFORE_TODAY``, which is a positive integer to denote
the day "back from today" to query. This might sound odd at first, but allows for a cronjob that runs sometime past
midnight, querying the day before by having ``1`` as argument, so it doesn't require date calculations in the cronjob
while still allowing it to fetch much older data without having a different method to pass the desired date.

.. note::

   The time zone is assumed to be `Europe/Berlin`, which can be overwritten using the ``--time-zone`` parameter.

The script prints all log/error information to standard error to allow the output of the tool to be read from standard
output if instructed so.

Output file
===========
The ``--output`` parameter can be omitted, which causes the tool to write to a file using the pattern
``data_<date>.csv``, where ``<date>`` is an isoformat-formated date and time of the day the dataset represents. So,
when called on 2020-11-08 with ``DAY_BEFORE_TODAY``, the file will be named ``data_2020-11-07T00:00:00.csv``.

If ``-`` (a dash) is passed, the CSV table will be written to standard output for use by another tool via a pipe.

Finally, if a filename is passed, this file will be used.

Files are written atomically, to prevent incomplete files from being present while the tool works.

Handling of incomplete data
===========================
The script will try to get a complete dataset, but due to the devices returning a random amount of data (it takes an
average of seven queries to receive one complete day for a single metric), it can only jump over holes not longer than
a few hours and will request the same portion over and over again.

Holes in the devices data can occur:

* If the battery ran empty (``power_mng.soc`` reached ``power_mng.soc_min`` or ``power_mng.soc_min_island``) during the
  night (during the day, the device powers itself from the strings).
* If the time of the device was changed forward by more than a few hours.
* If the device was switched off for some hours.

If the device sends invalid data (incomplete dataset with valid CRC or data with invalid CRC), the query is retried
until valid data is received. Likewise, if the device sends frames that are not of interest (as may occur when another
client such as the app communicates with it at the same time), the OID of that frame is logged and ignored.

csv2influxdb.py
***************
This tool takes the output CSV of the aforementioned tool `histogram2csv.py` and sends it to an InfluxDB database. The
tool trusts both the timestamps and the header lines and does not validate the data in any way. If a column is missing,
it will be missing in the InfluxDB table, if rows are missing they will be missing from the table, too.

::

   Usage: csv2influxdb.py [OPTIONS]
   
     Reads a CSV file produced by `histogram2csv.py` (requires headers) and
     pushes it to an InfluxDB database. This tool is intended to get you
     started and not a complete solution. It blindly trusts the timestamps and
     headers in the file.

   Options:
     -i, --input FILE           Input CSV file (with headers). Supply "-" to read
                                from standard input  [required]

     -n, --device-name TEXT     Name of the device [rct1]
     -h, --influx-host TEXT     InfluxDB hostname [localhost]
     -p, --influx-port INTEGER  InfluxDB port [8086]
     -d, --influx-db TEXT       InfluxDB database name [rct]
     -u, --influx-user TEXT     InfluxDB user name [rct]
     -P, --influx-pass TEXT     InfluxDB password [rct]
     --help                     Show this message and exit.

Influx
======
The script assumes that the database in the InfluxDB instance to exist. It will write to a table called ``history``.
The ``--device-name`` is used as value for the ``rct`` tag, and the fields are all float. The names are read from the
first (header) line of the CSV. In a CSV produced by `histogram2csv.py`, the names are the middle portion of the
``logger.minutes_<name>_log_ts`` as name. Thus, ``logger.minutes_ea_log_ts`` can be found in the ``ea`` field.

Input
=====
Input can be read from a file, or from standard input when called with the filename ``-``. This allows data to be piped
from another program, such as `histogram2csv.py` without hitting the disk.

read_pcap.py
************
This tool requires `scapy <https://scapy.net>`_ to be installed. It reads a `pcap
<https://en.wikipedia.org/wiki/Pcap>`_ file and displays the requests and responses to or from the device. This is most
useful for debugging `rctclient`, as it allows to take a look at the requests that the official smartphone app
performs. The tool assumes that all traffic in the capture file is protocol traffic.

.. warning::

   This is a tool intended for debugging, knowledge of both Python and binary data representaton is required.

The tool does some tricks to try to work around communication errors that appear when multiple requests from different
devices are to be processed, which commonly happens when the app is used on two different phones at the same time or
the device is communicating with the vendor. Further, it removes frames whose content is either ``AT+\r`` or
``0x2b3ce1``. The former is used by the vendors server at the beginning of each communication session (or as
keep-alive), the latter is used by the app which refers to the sequence as "switching to COM protocol". Despite two
protocols mentioned already, both communicate with the same protocol after these initial bytes, so the tool simply
slices them off.

An example how to work with the resulting data is provided at the end.

Preparation
===========
The first thing to do is to capture network traffic. This is most easily done at the router or another central point.
The most commonly used tool for the task is ``TCPDUMP(1)``, which is available for all commonly used operating systems.
Assuming that the device under test has IP address `192.168.0.1`, a command like the following should be all that's
needed for a first try:

``tcpdump -w rct-dump-$(date +%s).pcap host 192.168.0.1``

This command writes a new file with a unique enough name each time it is invoked, allowing for quick jumps between
captures. The host filer makes sure that only traffic to or from the device under test is captured.

Notice that the above command does not differentiate between protocols or TCP ports. This could easily be added to the
capture filter, but for demonstration purposes we'll utilize ``tshark`` from the `wireshark
<https://www.wireshark.org/>`_ project to further filter the traffc:

``tshark -r rct-dump-<timestamp>.pcap -Y 'ip.addr == 192.168.0.1 and tcp.port == 8899' -w rct-dump-<timestamp>.filtered.pcap``

The command reads the source capture file, applies the filter for TCP port 8899 and writes a new file. The new file
will be the input to the `read_pcap.py` tool.

In order for the tool to work, `scapy` needs to be installed, either system-wide or in a virtualenv (``pip install -U
scapy``).

Invocation
==========
The tool expects the input file name as only parameter: ``./read_pcap.py rct-dump-<timestamp>.filtered.pcap``.

.. warning::

   Reading the capture file with scapy is extremely slow and very resource-intensive (mostly RAM). Avoid big files. A
   35MB pcap file may take well over a minute to load.

The tool first prints an overview over the tcp sessions found inside the file. This is not to be confused with the
`Follow TCP stream` feature in Wireshark, which follows the packets in both ways, whereas Scapy splits the sent and
received packets into two streams. This has an important implication: The tool does not show the responses to requests
in a concise manner, but will read one stream after the other. The result is a long list of requests, then a long list
of answers.

An example for the streams looks like this:

::

   Stream    0 TCP 192.168.0.10:52730 > 192.168.0.1:8899 <PacketList: TCP:187 UDP:0 ICMP:0 Other:0> 6840 bytes
   Stream    1 TCP 192.168.0.1:8899 > 192.168.0.10:52730 <PacketList: TCP:167 UDP:0 ICMP:0 Other:0> 30281 bytes
   Stream    2 TCP 192.168.0.1:3580 > 192.168.0.11:8899 <PacketList: TCP:159 UDP:0 ICMP:0 Other:0> 30281 bytes
   Stream    3 TCP 192.168.0.11:8899 > 192.168.0.1:3580 <PacketList: TCP:159 UDP:0 ICMP:0 Other:0> 0 bytes

There are four streams of two devices (``192.168.0.10`` and ``192.168.0.11``) communicating with the device.

After the streams have been listed, the parsing process begins. Here are a few examples from the first stream, which
contains the `READ`-requests:

::

   frame consumed 9 bytes, 36 remaining
   Frame complete: <ReceiveFrame(cmd=READ, id=b403a7e6, address=0, data=)>
   Could not find ID in registry
   frame consumed 9 bytes, 27 remaining
   Frame complete: <ReceiveFrame(cmd=READ, id=663f1452, address=0, data=)>
   Could not find ID in registry
   frame consumed 9 bytes, 18 remaining
   Frame complete: <ReceiveFrame(cmd=READ, id=f8c0d255, address=0, data=)>
   Received read :  651 battery.cells[0]
   frame consumed 9 bytes, 9 remaining
   Frame complete: <ReceiveFrame(cmd=READ, id=8ef6fbbd, address=0, data=)>
   Received read :  385 battery.cells[1]

This might look confusing and the output could surely be improved, but it tells you all there is to know:

The first frame consumed 9 bytes and left 36 in the buffer. That means that a :class:`~rctclient.frame.ReceiveFrame`
read 9 bytes. The next line shows that the frame is complete, meaning that the frame got the entire message and the
checksums matched. It is a `READ` command to ID ``0xB403A7E6`` without payload (as is common for `READ`-requests.
The interesting part is the next line that reads **Could not find ID in registry**. That line makes it a very
interesting artifact, it's a frame that the official app created and where the registry has no details about yet. If
you search for the ``id`` in the output, the response frame should appear somewhere. More on that later.

The second frame is another unknown one, then follow two known ones: `READ`-requests to ``battery.cells[0]`` and
``battery.cells[1]``. Going further, let's scroll down in the capture, searching for the first unknown ID from above,
``b403a7e6``. This yields a hit:

::

   Frame 0 CRC mismatch, got 260 but calculated 735. Buffer: 2b0508b403a7e647e0692b0104
   002b
   frame consumed 2 bytes, 235 remaining
   Frame complete: <ReceiveFrame(cmd=_NONE, id=0, address=0, data=)> Buffer: 2b0508b403a7e647e0692b0104
   Could not find ID in registry
   Frame 0 CRC mismatch, got 26175 but calculated 7121. Buffer: 2b0104002b0505663f
   0508
   frame consumed 18 bytes, 217 remaining
   Frame complete: <ReceiveFrame(cmd=_NONE, id=0, address=0, data=)> Buffer: 2b0104002b0505663f
   Could not find ID in registry
   frame consumed 111 bytes, 106 remaining

Bummer. Something happened, perhaps a concurrent call from the other app on the second device. The frame could read the
data just fine but the checksum didn't match in the end. It prints the content of the frames buffer
(``2b0508b403a7e647e0692b0104``) which contains the id after the header, command and length, and that's what the search
found.

The tool then tries to work around invalid data and slices off the next few bytes from the buffer and tries again,
yielding another checksum mismatch: It has been observed that sometimes, the device will return invalid data and
slicing off the frame header allows a new `ReceiveFrame` instance to latch on to the next frame that was read from the
buffer by the broken one. It would otherwise be missed. This is not a valid approach for real-world code that
interfaces with the devices, but this is a debugging tool.

Before looking at a valid result with this OID, let's look at another valid result that is in the registry:

::

   frame consumed 14 bytes, 46 remaining
   Frame complete: <ReceiveFrame(cmd=RESPONSE, id=6388556c, address=0, data=00001441)>
   Received reply:  261 battery.stack_software_version[0]        type: UINT32            value: 5185

The OID is known, and the tool automatically decoded the value and shows the index, name, data type and value. (This
does not yet work for complex types like :ref:`protocol-timeseries`).

Let's look at the successfull response for our missing ID then:

::

   frame consumed 14 bytes, 223 remaining
   Frame complete: <ReceiveFrame(cmd=RESPONSE, id=b403a7e6, address=0, data=47000000)>
   Could not find ID in registry

Here we can see that the frame was parsed, but since it is unknown, the tool could not parse the data. The data field
is printed above in hexadecimal notation as ``data=47000000``. This is the point where one can play around with the
data by trying to convert it into something reasonable, let's take a small detour.

Decoding unknown data
=====================
The above OID ``0xB403A7E6`` got a response payload of ``0x47000000``. Let's try to make sense from the data.

To work with the data, it needs to be converted to a byte stream first. The easiest way is to use `bytearray.fromhex
<https://docs.python.org/3/library/stdtypes.html#bytearray.fromhex>`_:

.. code-block:: pycon

   >>> b = bytearray.fromhex('47000000')
   >>> b
   bytearray(b'G\x00\x00\x00')

With the byte stream in the variable ``b``, let's try to convert it into something usable. For this, `struct.unpack
<https://docs.python.org/3/library/struct.html#struct.unpack>`_ is used with a set of format strings. First, try a 32
bit unsigned integer as is commonly used with `unix timestamps`:

.. code-block:: pycon

   >>> import struct
   >>> struct.unpack('>I', b)[0]
   1191182336
   >>> from datetime import datetime
   >>> datetime.fromtimestamp(1191182336)
   datetime.datetime(2007, 9, 30, 21, 58, 56)

This 'could' very well be a timestamp, albeit representing point in time quite long ago, from 2007. Although it looks
like a false track, it might still be worth checking the app to find a timestamp in that range. Sometimes, timestamps
in the past are set for some settings that have not been updated. Assuming nothing was found, let's try converting it
to a floating point number:

.. code-block:: pycon

   >>> struct.unpack('>f', b)[0]
   32768.0

This looks like a power of two. Search the app again for values that have such a number.

In this example, the data type looks like a number. This is not always the case, for example a sequence of data that
ends with a large number of ``00`` sequences typically contains a string (C uses NULL bytes to terminate strings).
Some OIDs carry additional garbage data after the NULL byte, too, so this is something to look out for.
