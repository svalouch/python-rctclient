
.. _protocol-timeseries:

##########
Timeseries
##########

The ``logger`` group of object IDs (with the exception of the event log) returns time series data (values with an
associated timestamp taken at regular intervals) as a long response. Similar to th event log, the data is queried by
writing a UNIX timestamp to the object ID, uppon which the device returns data that was logged **before** that
timestamp. The amount of data varies similar to the event log, so in order to get a full days of data for a single time
series, an average of 7 queries are required.

As with the event table, the first element is a unix timestamp, repeating the value written to the object ID. Then
follows a list of pairs, first a UNIX timestamp and then the floating point value.

Thus, the request data type is ``INT32`` for the timestamp, and the response data type is the special ``TIMESTAMP``
data type to cause the :func:`~rctclient.utils.decode_value` function to correctly parse the data into a data
structure.

Data resolution
***************
The data resolution varies between object IDs. Object IDs with ``minutes`` in their name, such as
``logger.day_egrid_load_log_ts`` have a resolution of 5 minutes.

+-------------+------------+
| Time part   | Resolution |
+=============+============+
| ``minutes`` | 5 minutes  |
+-------------+------------+
| ``day``     |            |
+-------------+------------+
| ``month``   |            |
+-------------+------------+
| ``year``    |            |
+-------------+------------+

Data storage
************
The devices use some sort of ring buffer to manage their data, meaning that old elements are overwritten as new data is
stored. For ``minutes`` graphs, this leads to ~90 days of history.

Data format
***********
All elements are always 4-bytes long and are either UINT32 for the timestamp or FLOAT for the value.

+--------+-----------------------------------------------------+
| Number | Meaning                                             |
+========+=====================================================+
| 0      | Query timestamp, repeated from the write request.   |
+--------+-----------------------------------------------------+
| 1      | Timestamp 0, associated with the following element. |
+--------+-----------------------------------------------------+
| 2      | Value 0.                                            |
+--------+-----------------------------------------------------+
| 3      | Timestamp 1.                                        |
+--------+-----------------------------------------------------+
| 4      | Value 1.                                            |
+--------+-----------------------------------------------------+
| 5      | Timestamp 2.                                        |
+--------+-----------------------------------------------------+
| ...    | ...                                                 |
+--------+-----------------------------------------------------+

Unless an error occurs, the structure is always ``<number of entries> * 2 + 1`` 4-byte sequences, the extra sequence
being the timestamp at the very beginning.
