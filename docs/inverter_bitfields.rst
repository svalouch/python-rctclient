
.. _inverter_bitfields:

##########################
Bitfields and Enumerations
##########################

As is common with embedded devices, the inverters use bitfields to save space, as a single byte can represent a number
of individual states in 255 possible combinations. The downside is: One cannot interpret these without an explanation.

``fault[*].flt``
****************
With four 32-bit-OIDs and thus 128 bits, the ``fault[*].flt`` family is so large that it gets its own page at
:ref:`inverter_faults`.

``battery.bat_status``
**********************
This 32-bit wide value describes the status of the battery stack as a whole. Some of the values have been empirically
identified, but most of it is largely unknown.

* ``value & 1032 == 0`` causes the App to display ``(calib.)`` [1]_. Note that this sets two bits at the same time.
* ``value & 2048 == 0`` denotes that balancing is in progress (App displays ``(balance)``) [1]_

.. [1] Found by "oliverrahner": `weltenwort/home-assistant-rct-power-integration#264 (comment) <https://github.com/weltenwort/home-assistant-rct-power-integration/issues/264#issuecomment-1503165691>`__