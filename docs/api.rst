
###
API
###

Types
*****

.. autoclass:: rctclient.types.Command
   :members:

.. autoclass:: rctclient.types.ObjectGroup
   :members:
   :undoc-members:

.. autoclass:: rctclient.types.FrameType
   :members:

.. autoclass:: rctclient.types.DataType
   :members:

.. autoclass:: rctclient.types.EventEntry
   :members:


Exceptions
**********

.. autoclass:: rctclient.exceptions.RctClientException

.. autoclass:: rctclient.exceptions.FrameError

.. autoclass:: rctclient.exceptions.FrameNotComplete

.. autoclass:: rctclient.exceptions.FrameCRCMismatch


Classes
*******

.. autoclass:: rctclient.registry.ObjectInfo
   :members:

.. autoclass:: rctclient.registry.Registry
   :members:

.. autoclass:: rctclient.frame.ReceiveFrame
   :members:

.. autoclass:: rctclient.frame.SendFrame
   :members:

Functions
*********

.. autofunction:: rctclient.frame.make_frame

.. autofunction:: rctclient.utils.decode_value

.. autofunction:: rctclient.utils.encode_value

.. autofunction:: rctclient.utils.CRC16
