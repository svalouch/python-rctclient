
:wide_page: true

.. _registry:

########
Registry
########

The registry is a data structure that maintains a list of all known :class:`~rctclient.registry.ObjectInfo`. It is
implemented as :class:`~rctclient.registry.Registry`, please head to the API documentation for means to query it for
object ID information. As the registry is a heavy object, it is maintained as an instance ``REGISTRY`` in the
``registry`` module and can be imported where needed.

The following list is a complete index of all the object IDs currently maintained by the registry.

.. the following tables are generated from the registry in registry.py using generate_registry.py

acc_conv
========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_acc_conv.csv

adc
===

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_adc.csv

bat_mng_struct
==============

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_bat_mng_struct.csv

battery
=======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_battery.csv

buf_v_control
=============

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_buf_v_control.csv

can_bus
=======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_can_bus.csv

cs_map
======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_cs_map.csv

cs_neg
======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_cs_neg.csv

db
==

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_db.csv

dc_conv
=======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_dc_conv.csv

display_struct
==============

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_display_struct.csv

energy
======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_energy.csv

fault
=====

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_fault.csv

flash_param
===========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_flash_param.csv

flash_rtc
=========
.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_flash_rtc.csv

grid_lt
=======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_grid_lt.csv

grid_mon
========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_grid_mon.csv

g_sync
======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_g_sync.csv

hw_test
=======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_hw_test.csv

io_board
========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_io_board.csv

iso_struct
==========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_iso_struct.csv

line_mon
========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_line_mon.csv

logger
======
The `logger` group contains time series data and the event log. These are special, compound data structures that
require a bit of work to parse. They generally work by writing the timestamp of the newest element of interest to them
and respond with the entries or events **older** than that time stamp. For more details, take a look at the
:ref:`protocol-event-table` and :ref:`protocol-timeseries` pages.

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_logger.csv

modbus
======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_modbus.csv

net
===

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_net.csv

nsm
===

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_nsm.csv

others
======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_others.csv

power_mng
=========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_power_mng.csv

p_rec
=====

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_p_rec.csv

prim_sm
=======

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_prim_sm.csv

rb485
=====

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_rb485.csv

switch_on_board
===============

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_switch_on_board.csv

temperature
===========

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_temperature.csv

wifi
====

.. csv-table::
   :header-rows: 1
   :widths: 10, 5, 5, 5, 15, 40
   :file: objectgroup_wifi.csv
