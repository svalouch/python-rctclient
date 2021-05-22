# rctclient - Python implementation of the RCT Power GmbH "Serial Communication Protocol"

This Python module implements the "Serial Communication Protocol" by RCT Power GmbH, used in their line of solar
inverters. Appart from the API, it also includes a registry of object IDs and a command line tool. For development, a
simple simulator is included.

This project is not in any way affiliated with or supported by RCT Power GmbH.

## Documentation

Below is a quickstart guide, the project documentation is on [Read the Docs](https://rctclient.readthedocs.io/).

## Installing

Install and update using [pip](https://pip.pypa.io/en/stable/quickstart/):

```
$ pip install -U rctclient
```

To install the dependencies required for the CLI tool:

```
$ pip install -U rctclient[cli]
```

## Example

Let's read the current battery state of charge:
```python

import socket, select, sys
from rctclient.frame import ReceiveFrame, make_frame
from rctclient.registry import REGISTRY as R
from rctclient.types import Command
from rctclient.utils import decode_value

# open the socket and connect to the remote device:
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.0.1', 8899))

# query information about an object ID (here: battery.soc):
object_info = R.get_by_name('battery.soc')

# construct a frame that will send a read command for the object ID we want, and send it
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
```

## Reading values from the command line

The module installs the `rctclient` command (requires `click`). The subcommand `read-values` reads a single value from
the device and returns its output. Here is a call example using the object ID with verbose output:

```
$ rctclient read-value --verbose --host 192.168.0.1 --id 0x959930BF
#413 0x959930BF battery.soc         SOC (State of charge)              0.29985150694847107
```

Without `--verbose`, the only thing that's printed is the received value. This is demonstrated below, where the
`--name` parameter is used instead of the `--id`:
```
$ rctclient read-value --host 192.168.0.1 --name battery.soc
0.2998138964176178
```
This makes it suitable for use with scripting environments where one just needs some values. If `--debug` is added
before the subcommands name, the log level is set to DEBUG and all log messages are sent to `stderr`, which allows for
scripts to continue processing the value on stdout, while allowing for observations of the inner workings of the code.

## Generating the documentation

The documentation is generated using Sphinx, and requires that the software be installed to the local environment (e.g.
via virtualenv). With a local clone of the repository, do the following (activate your virtualenv before if so
desired):
```
$ pip install -e .[docs,cli]
$ cd docs
$ make clean html
```
The documentation is put into the `docs/_build/html` directory, simply point your browser to the `index.html` file.

The documentation is also auto-generated after every commit and can be found at
[https://rctclient.readthedocs.io/](https://rctclient.readthedocs.io/).
