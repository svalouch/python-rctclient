
.. _cli_write_support:

#############
Write support
#############

The CLI does **not** include support for changing values. This will not change in the foreseeable future.

Rationale
*********
.. warning::

   TL;DR: It's just too dangerous.

The tool is intended to be used by end users, and it does not look like the devices being able to protect themselves
against invalid data.

The protocol lacks any measure to communicate failure of any sorts. While the device has a rich set of error conditions
that can be queried (``fault[*].flt``), it does not have a feature to communicate "this value is invalid". It isn't
known how a device will react. It may simply ignore the value or send a specific value back that is not part of the
documentation, or simply apply it somehow. What would happen if the trailing ``\0`` on a string was missing, or if the
payload was far larger than what the device supports, for example? Would it run over the intended length of the string
into its own adjacent memory, causing it to… do what, crash and reset, or would it become bricked? There have been
instances where a padded string payload was received, containing garbled data after the trailing ``\0`` that looked
like another frame, hinting at less-than-ideal memory management in that particular version of the control software. Or
the network interface card, it's not known how the data is passed around. It is also unknown how to recover, though
ultimately replacing components is a valid recovery strategy, albeit potentially costly.

It is also known that certain values must be within bounds, such as a maximum or minimum value for an integer, or a
maximum length for a string. But what these bounds are is not documented by the vendor, although the Android app seems
to have knowledge of them. In order to prevent accidentally causing damage, the client application would need to have
knowledge of the bounds, which is not possible at the moment. It is unknown how the devices deal with invalid data.
From various reports, it is safe to assume that (at the time of writing) there are little to no checks, such as
corrupting the display.

Some OIDs are not meant to be written to, yet the device does allow writing to at least some of them and reports the
new value in further read-requests. The documentation does not include information on which are writeable or supposed
to be written to, or which of these are persisted to flash. Yet the client would need to know this to prevent
overwriting important information.

The vendor provides zero support for usage of the device by means other than their App or portal. Others who tried to
implement the protocol in their own applications have reported that while they got access to a -- presumably stripped
down or even simulated -- device to test against, the support did not answer any of their questions regarding specifics
related to the protocol, let alone how the devices react or how one is supposed to react to certain behaviours that the
device shows.

Potential for (physical) damage: With the above, imagine that the device simply applies the data. This may potentially
lead to impact in the real world, e.g. by over-stressing its own components, impacting the power grid or cause damage
to electronics within the house. The devices seem to rely on the App to prevent invalid data from being send.

Testing is non-trivial, as a device would be required. Most devices are in use (installed into domestic houses or
factories), so testing on them is out of the question. At this moment, most "testing" is done by looking at *tcpdumps*
to extract WRITE calls issued by the official app and compare it with the output of functions like
:func:`~rctclient.frame.make_frame`. This is very limited as well, as only a very small subset of OIDs can be changed
while the device is in use (without causing trouble).

Do it yourself!
***************
If you want to implement this on your own, here are some tips:

Values appear to be ephemeral by default, meaning their values will be reset when the device reboots. To persist them,
you need to do the COM-dance by writing ``0x05`` to ``com_service`` and then set it back to ``0x00`` after a couple of
seconds.

If this was a success is unknown, one knows when the next reboot happens and the old value shows up. Also, this wears
the flash down, these chips typically have a very limited lifetime (anywhere from a few dozen to a couple hundred
writes, depending on the actual chip and how it is implemented), so one does not want to write to flash other than
absolutely necessary, and the device most likely breaks when the flash is dead. There are certain counters that can be
queried that seem to report the number of write-cycles though, but it's not specifically documented and how many it can
sustain is unknown.

That being said, the client does support writing: The ``timeseries`` data is queried by issuing ``WRITE``-commands with
the current unix timestamp to the device and it answers with a ``timestamp: value-table``. That was, by the way,
reverse-engineered by staring at hexdumps, as the format is not in the documentation. But all the code is there, just
not wired up the way you want.

