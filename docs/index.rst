#####################################
Welcome to rctclient's documentation!
#####################################

This documentation covers the `rctclient` python library, used to interact with solar inverters by `RCT Power GmbH` by
implementing their proprietary "RCT Power Serial Communication Protocol". It also serves as documentation of the
protocol itself. As such, the main focus is on supporting the vendors devices, but the library can be used for own
implementations just as well.

**Disclaimer**: Neither the python library nor this documentation is in any way affiliated with or supported by RCT
Power GmbH in any way. Do **not** ask them for support regarding anything concerning the content of the material
provided by this project.

**2nd Disclaimer**: Use the material provided by this project (code, documentation etc.) at your own risk. None of the
contributors can be held liable for any damage that may occur by using the information provided. See also the `LICENSE`
file for further information.

Target audience
***************
* The :ref:`cli` is meant for end users who wish to easily extract values without having to write a program.
* The :ref:`library <api>` is intended for developers who wish to enable their software to interact with the devices.
* The documentation is also mostly targeted at developers, but some of the information may be of use for everyone else,
  too.

The CLI is pretty low-level, however, and you may wish to use a ready-to-use solution for integrating the devices into
your own home automation or to monitor them. In this case, here's a randomly sorted list open source tools that may be
of interest for you:

* `home-assistant-rct-power-integration <https://github.com/weltenwort/home-assistant-rct-power-integration>`__ by
  `@weltenwort <https://github.com/weltenwort>`__ integrates an inverter into Home Assistant (using this library).
* `solaranzeige.de <https://solaranzeige.de/phpBB3/solaranzeige.php>`__ (German) is a complete solution running on a
  Raspberry Pi.
* `rctmon <https://github.com/svalouch/rctmon>`__ exposes a Prometheus endpoint and fills an InfluxDB (using this
  library).
* `OpenWB <https://openwb.de/>`__ (German) is an open source wallbox.
* Integrations for Node-Red, Homematic and a lot of other systems can be found in their respective communities.

.. toctree::
   :maxdepth: 2
   :caption: Module contents

   usage
   cli
   cli_write_support
   simulator
   api
   tools
   CHANGELOG

.. toctree::
   :maxdepth: 1
   :caption: RCT Inverter Documentation

   inverter_registry
   inverter_faults
   inverter_bitfields
   inverter_app_mapping

.. toctree::
   :maxdepth: 1
   :caption: Protocol

   protocol_overview
   protocol_event_table
   protocol_timeseries

History
*******
The original implementation was done by GitHub user `pob90 <https://github.com/pob90>`__, including a simulator that
can be used for development and a command line tool to manually query single objects from the device. The simulator
proved to be invaluable when developing software that interfaces with RCT devices and when porting the code to Python
3. The original code is based on the official documentation by the vendor (version 1.8, later updated to 1.13).

The original implementation can be found here: `<https://github.com/pob90/openWB/tree/master/modules/rct_power>`__

The implementation was done for use with the `OpenWB <https://openwb.de/main/>`__ project. The projects goal is to
provide an open source wall box for charging electric cars, and it needs to interface with various devices in order to
optimize its usage of energy, such as only charging when the solar inverter signals an abundance of energy.

The project was, however, implemented as pure Python 2 code. As Python 2 is officially dead and the first distributions
completed its removal, the first step was to convert everything to Python 3. Once the code worked (again), the
structure was changed to span multiple files instead of one single file, some classes were split, many were renamed and
variable constants were converted to enums and `PEP-484 <https://www.python.org/dev/peps/pep-0484/>`__ type hinting was
added.

See the *CHANGELOG* for the history since.
