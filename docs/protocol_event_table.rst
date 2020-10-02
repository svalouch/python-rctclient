
.. _protocol-event-table:

###########
Event Table
###########

The event table (OID ``0x6F3876BC``) comes as a long response. It is queried by **writing** a UNIX timestamp to the
OID, and the device will respond with a list of entries that occured `earlier` than that timestamp. The amount of
entries varies, so in order to receive a larger amount multiple queries are required, by using the timestamp of the
"oldest" entry as timestamp for the next query.

Similar to the histogram metrics, the first element is the UNIX timestamp that was used in the request, then a table
follows. Each table row consists of five UINT32 values, though not all of them are used with all entry types. Each row
represents a single entry in the table. The first element (element 0) is the **type** of the event, a single ASCII
character. The next element is a UNIX timestamp that denotes either the precise moment the event occured for some
types, or the begin of an event. The meaning of the other three elements can be read from the table below, as they are
dependant on the type of event.

Data format
***********
All elements are 4 bytes wide. The response looks like this:

+--------+-------------------------------------------------------------------------------------------------------+
| Number | Meaning                                                                                               |
+========+=======================================================================================================+
| 0      | Query timestamp, repeated from the write request.                                                     |
+--------+-------------------------------------------------------------------------------------------------------+
| 1      | ASCII character denoting the type of the entry (see table below).                                     |
+--------+-------------------------------------------------------------------------------------------------------+
| 2      | Timestamp denoting the start of the event (for ranged events) or the point in time the event occured. |
+--------+-------------------------------------------------------------------------------------------------------+
| 3      | Type-specific value. This is the end timestamp for ranged types, but also carries other information.  |
+--------+-------------------------------------------------------------------------------------------------------+
| 4      | Type-specific value.                                                                                  |
+--------+-------------------------------------------------------------------------------------------------------+
| 5      | Type specific value.                                                                                  |
+--------+-------------------------------------------------------------------------------------------------------+
| 6      | ASCII character for the type of the next entry                                                        |
+--------+-------------------------------------------------------------------------------------------------------+
| 7      | Timestamp of the event.                                                                               |
+--------+-------------------------------------------------------------------------------------------------------+
| ...    | ...                                                                                                   |
+--------+-------------------------------------------------------------------------------------------------------+

Unless an error occurs, which may happen when the device receives another command while working on this request,
resulting in a correct CRC but incomplete data, the structure is always ``<number of entries> * 5 + 1`` 4-byte
sequences, the extra element is the timestamp at the very beginning.

Event overview
**************

.. warning::

   The table lists the known events only. That means that the authors have not seen other event codes than the ones
   below and could not cross-check the others with the official smartphone app, so this list is likely incomplete.

+-------+---------------+--------------+-------------+----------------------+
| Type  | Element 2     | Element 3    | Element 4   | Name                 |
+=======+===============+==============+=============+======================+
| ``c`` | End timestamp | Case number  | unknown     | ``PHASE_POS``        |
+-------+---------------+--------------+-------------+----------------------+
| ``d`` | End timestamp | Float value  |             | ``BAT_OVERVOLTAGE``  |
+-------+---------------+--------------+-------------+----------------------+
| ``k`` | End timestamp | unknown      | unknown     | ``CAN_TIMEOUT``      |
+-------+---------------+--------------+-------------+----------------------+
| ``r`` | End timestamp | Error code   |             | ``BAT_INTERN``       |
+-------+---------------+--------------+-------------+----------------------+
| ``s`` | Object ID     | Old value    | New value   | ``PRM_CHANGE``       |
+-------+---------------+--------------+-------------+----------------------+
| ``v`` | End timestamp | unknown      | ignored     | ``RESET``            |
+-------+---------------+--------------+-------------+----------------------+
| ``w`` | 0             | Old version  | New version | ``UPDATE``           |
+-------+---------------+--------------+-------------+----------------------+
| ``y`` | End timestamp | unknown      | unknown     | ``FRT_UNDERVOLTAGE`` |
+-------+---------------+--------------+-------------+----------------------+
| ``x`` | End timestamp | unknown      | unknown     | ``FRT_OVERVOLTAGE``  |
+-------+---------------+--------------+-------------+----------------------+
| ``O`` | End timestamp | Float value  | ignored     | ``SW_ON_UMIN_L1``    |
+-------+---------------+--------------+-------------+----------------------+
| ``P`` | End timestamp | Float value  | ignored     | ``SW_ON_UMAX_L1``    |
+-------+---------------+--------------+-------------+----------------------+
| ``R`` | End timestamp | Float value  | ignored     | ``SW_ON_FMAX_L1``    |
+-------+---------------+--------------+-------------+----------------------+
| ``S`` | End timestamp | Float value  | ignored     | ``SW_ON_UMIN_L2``    |
+-------+---------------+--------------+-------------+----------------------+
| ``T`` | End timestamp | Float value  | ignored     | ``SW_ON_UMAX_L2``    |
+-------+---------------+--------------+-------------+----------------------+
| ``W`` | End timestamp | Float value  | ignored     | ``SW_ON_UMIN_L3``    |
+-------+---------------+--------------+-------------+----------------------+
| ``X`` | End timestamp | Float value  | ignored     | ``SW_ON_UMAX_L3``    |
+-------+---------------+--------------+-------------+----------------------+
| ``Y`` | End timestamp | unknown      | ignored     | ``SURGE``            |
+-------+---------------+--------------+-------------+----------------------+
| ``Z`` | End timestamp | Case number  | unknown     | ``NO_GRID``          |
+-------+---------------+--------------+-------------+----------------------+

Event details
*************
For each of the event types observed, this section provides a short explanation and an example of the corresponding
message taken from the official app.


PHASE_POS
=========

A ranged event, containing a "case number" and an unknown element. The app reports this as follows:

::

   Duration: -
   Phase position error (not 120° as expected)
   case <case number>


BAT_OVERVOLTAGE
===============
A ranged event with the floating point number of the battery voltage at the time of the event start as only parameter.
The app reports this as follows:

::

   Duration: 00:00:22
   Battery overvoltage
   U = <value> V


CAN_TIMEOUT
===========
Ranged event reporting a timeout in the CAN-bus communication with a component. It is not known yet if there is a
separate RS485 timeout event or if these events are handled here as well. The app reports this as follows:

::

   Duration: 00:00:22
   "CAN communication timeout with battery"


BAT_INTERN
==========
This ranged event reports an abnormal condition with the battery stack. The payload seems to contain an error code and
another unknown element. The app reports this as follows (example, there are other messages possible):

::

   Duration: 00:00:22
   Internal battery error (<error code>)
   Battery 0
   UI-Board (0x123)
   Error class 1: Charge overcurrent


PRM_CHANGE
==========
This event has no end timestamp as it reports a singular event: the change of a parameter. Thus, it carries the object
ID of the changed object as element 2 and the old and new values as elements 3 and 4. The meaning of the values depends
on the object ID, obviously, as the raw values are reported. To make a meaning of them, the values have to be decoded
according to the data types associated with the object ID.

The app automatically performs a lookup and translates the object ID to its name in many but not all cases. For
parameters that are unlikely to be changed by the user, it reports the name of the object ID. The app does not
interpret the values, so boolean values are reported as ``0`` or ``1``, for example.

::

   Duration: -
   Parameter changed
   "Enable rescan for global MPP on solar generator A": 0 --> 1

::

   Duration: -
   Parameter changed
   "display_struct.variate_contrast": 1 --> 0


RESET
=====
This ranged event reports the reset or restart of the system. This is, for example, done after a firmware update. The
app reports this as follows:

::

   Duration: 00:00:22
   System start


UPDATE
======
A non-ranged event, reporting the successful update of the controller software. It includes the old and new software
version as alements 3 and 4, element 2 contains the number ``0``. The app reports this like so:

::


   Duration: -
   Update <old value> <new value>


FRT_UNDERVOLTAGE
================
A ranged event, containing two unknown parameters that are not shown in the app.

::

   Duration: 00:00:22
   FRT under-voltage


FRT_OVERVOLTAGE
===============
A ranged event, containing two unknown parameters that are not shown in the app.

::

   Duration: 00:00:22
   FRT over-voltage


SW_ON_UMIN_L1
=============
Ranged event, containing the voltage as element 3.

::

   Duration: 00:00:22
   Switching On Conditions Umin phase 1
   U = <value> V

SW_ON_UMAX_L1
=============
Ranged event, carrying the voltage level as element 3.

::

   Duration: 00:00:22
   Switching On Conditions Umax phase 1
   U = <value> V


SW_ON_FMAX_L1
=============
Ranged event, caryying the frequency as element 3. This seems to be the only frequency level event, as there is no room
in the type list for FMAX events for the other two phases. Also, some inverters are capable of putting all power into
one single phase if so desired.

::

   Duration: 00:00:22
   Switching On Conditions Fmax phase 1
   f = <value> Hz

SW_ON_UMIN_L2
=============
See ``SW_ON_UMIN_L1``.

SW_ON_UMAX_L2
=============
See ``SW_ON_UMAX_L1``.

SW_ON_UMIN_L3
=============
See ``SW_ON_UMIN_L1``.

SW_ON_UMAX_L3
=============
See ``SW_ON_UMIN_L1``.


SURGE
=====
A ranged event reporting a surge event. An unknown value is transported in element 3. The app reports this as follows:

::

   Duration: 00:00:01
   Phase failure detected

NO_GRID
=======
A ranged event reporting a loss of the power grid. The elements 3 and 4 are the same as for ``PHASE_POS``, but the case
number is not shown by the app.

::

   Duration: 00:00:00
   Reserved
