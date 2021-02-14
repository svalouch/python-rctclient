#####################################
Welcome to rctclient's documentation!
#####################################

This documentation covers the `rctclient` python library, used to interact with solar inverters by `RCT Power GmbH` by
implementing their proprietary "RCT Power Serial Communication Protocol". It also serves as documentation of the
protocol itself.
 
**Disclaimer**: Neither the python library nor this documentation is in any way affiliated with or supported by RCT
Power GmbH in any way. Do **not** ask them for support regarding anything concerning the content of the material
provided by this project.

**2nd Disclaimer**: Use the material provided by this project (code, documentation etc.) at your own risk. None of the
contributors can be held liable for any damage that may occur by using the information provided. See also the `LICENSE`
file for further information.

.. toctree::
   :maxdepth: 2
   :caption: Module contents

   usage
   cli
   registry
   simulator
   api
   tools
   CHANGELOG

.. toctree::
   :maxdepth: 1
   :caption: Protocol

   protocol_overview
   protocol_event_table
   protocol_timeseries

History
*******
The original implementation was done by GitHub user `pob90 <https://github.com/pob90>`_, including a simulator that
can be used for development and a command line tool to manually query single objects from the device. The simulator
proved to be invaluable when developing software that interfaces with RCT devices and when porting the code to Python
3. According to a
`forum post <https://openwb.de/forum/viewtopic.php?f=9&t=676&sid=47509f12301afec98936c0697d59bf97&start=10#p11183>`_
and comments in the code base, the implementation is based on the official documentation by the vendor, version 1.8.

The original implementation can be found here: `<https://github.com/pob90/openWB/tree/master/modules/rct_power>`_

The implementation was done for use with the `OpenWB <https://openwb.de/main/>`_ project. The projects goal is to
provide an open source wall box for charging electric cars, and it needs to interface with various devices in order to
optimize its usage of energy, such as only charging when the solar inverter signals an abundance of energy.

The integration can be found in their repository:

* `bezug_rct <https://github.com/snaptec/openWB/tree/master/modules/bezug_rct>`_ (python implementation and call
  example using shell).
* `speicher_rct <https://github.com/snaptec/openWB/tree/master/modules/speicher_rct>`_ (shell calls only)
* `wr_rct <https://github.com/snaptec/openWB/tree/master/modules/wr_rct>`_ (shell calls only)

The project was, however, implemented as pure Python 2 code. As Python 2 is officially dead and (as of writing this)
the first distributions completed its removal, the first step was to convert everything to Python 3. Once the code
worked (again), the structure was changed to span multiple files instead of one single file, some classes were split,
many were renamed and variable constants were converted to enums and
`PEP-484 <https://www.python.org/dev/peps/pep-0484/>`_ type hinting was added.
