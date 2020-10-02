
.. _simulator:

#########
Simulator
#########

To aid in developing tools or this module itself, a simulator offers an easy way to safely test code without
interfacing with real hardware and potentially causing problems. The simulator can be run by using the subcommand
``simulator`` of the :ref:`cli`.

Starting the simulator
**********************
The simulator will, by default, bind to `localhost` on port `8899`, which is the default port for the protocol. These
can be changed using the ``--host`` and ``--port`` options. To stop the simulator, press `Ctrl+c` on the terminal.

Without ``--verbose``, the simulator won't output anything to the terminal. Adding the flag yields output:

.. code-block:: shell-session

   $ rctclient simulator --verbose
   INFO:rctclient.simulator:Waiting for client connections
   INFO:rctclient.simulator:connection accepted: <socket.socket fd=4, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('127.0.0.1', 8899), raddr=('127.0.0.1', 55038)> ('127.0.0.1', 55038)
   INFO:rctclient.simulator.socket_thread.55038:Read   : #394 0x90B53336 temperature.sink_temp_power_reduction        -> 2b050890b53336000000006157

For a better view on the inner workings, supply the ``--debug`` parameter to ``rctclient``, but be warned: this will
print a lot of text:

.. code-block:: shell-session

   $ rctclient --debug simulator
   2020-10-02 12:14:09,935 - rctclient.cli - INFO - rctclient CLI starting
   2020-10-02 12:14:09,936 - rctclient.simulator - INFO - Waiting for client connections
   2020-10-02 12:14:12,486 - rctclient.simulator - DEBUG - connection accepted: <socket.socket fd=4, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0, laddr=('127.0.0.1', 8899), raddr=('127.0.0.1', 55044)> ('127.0.0.1', 55044)
   2020-10-02 12:14:12,486 - rctclient.simulator.socket_thread.55044 - DEBUG - Read 9 bytes: 2b010490b533361775
   2020-10-02 12:14:12,486 - rctclient.simulator.socket_thread.55044 - DEBUG - Frame consumed 9 bytes
   2020-10-02 12:14:12,486 - rctclient.simulator.socket_thread.55044 - DEBUG - Complete frame: <ReceiveFrame(cmd=1, id=90b53336, address=0, data=)>
   2020-10-02 12:14:12,486 - rctclient.simulator.socket_thread.55044 - INFO - Read   : #394 0x90B53336 temperature.sink_temp_power_reduction        -> 2b050890b53336000000006157
   2020-10-02 12:14:12,486 - rctclient.simulator.socket_thread.55044 - DEBUG - Sending frame <SendFrame(command=5, id=0x90B53336, payload=0x00000000)> with 13 bytes 0x2b050890b53336000000006157
   2020-10-02 12:14:12,487 - rctclient.simulator.socket_thread.55044 - DEBUG - Closing connection <socket.socket [closed] fd=-1, family=AddressFamily.AF_INET, type=SocketKind.SOCK_STREAM, proto=0>
   2020-10-02 12:14:16,063 - rctclient.simulator - DEBUG - Keyboard interrupt, shutting down

How it works
************
The simulator acts as a server for the protocol. It receives the commands, decodes them and then creates a new frame as
answer to the command. So far, only read-requests for non-plant communication are implemented.

Using the :class:`~rctclient.registry.Registry`, it looks up information about the object ID received from the client
software and uses the ``sim_data`` property to craft a valid response. For trivial types, a sensible default is used:

* Boolean types return ``False``
* Floating point types return ``0.0``
* Integer types return ``0``
* Strings return ``ASDFGH``

Additionally, when creating the :class:`~rctclient.registry.ObjectInfo` objects, a value can be set using the
``sim_data`` keyword argument to provide a more fitting result.

Limitations
***********
The simulator won't return invalid data, that means that it always calculates the correct checksum and won't send
incomplete data. When developing against the simulator, bear in mind the limitations of the real world device:

If a request is received while serving another request, the response that the device is currently prepairing is cut at
the current point and a CRC checksum is computed. This results in frames that can't be decoded, but have a valid
checksum for the incomplete payload.

For now, it only returns normal replies, even though some replies should be long replies. This may be fixed in the
future.
