# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: activity.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)


import world_pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='activity.proto',
  package='Sanguo.protocol.activity',
  serialized_pb='\n\x0e\x61\x63tivity.proto\x12\x18Sanguo.protocol.activity\x1a\x0bworld.proto\"\xb9\x02\n\rActivityEntry\x12\n\n\x02id\x18\x01 \x02(\x05\x12\x15\n\rcurrent_value\x18\x02 \x02(\x05\x12\x11\n\tleft_time\x18\x03 \x02(\x05\x12M\n\nconditions\x18\x04 \x03(\x0b\x32\x39.Sanguo.protocol.activity.ActivityEntry.ActivityCondition\x1a\xa2\x01\n\x11\x41\x63tivityCondition\x12\n\n\x02id\x18\x01 \x02(\x05\x12P\n\x06status\x18\x02 \x02(\x0e\x32@.Sanguo.protocol.activity.ActivityEntry.ActivityCondition.Status\"/\n\x06Status\x12\x0b\n\x07HAS_GOT\x10\x01\x12\x0b\n\x07\x43\x41N_GET\x10\x02\x12\x0b\n\x07\x43\x41N_NOT\x10\x03\"^\n\x0e\x41\x63tivityNotify\x12\x0f\n\x07session\x18\x01 \x02(\x0c\x12;\n\nactivities\x18\x02 \x03(\x0b\x32\'.Sanguo.protocol.activity.ActivityEntry\"d\n\x14\x41\x63tivityUpdateNotify\x12\x0f\n\x07session\x18\x01 \x02(\x0c\x12;\n\nactivities\x18\x02 \x03(\x0b\x32\'.Sanguo.protocol.activity.ActivityEntry\"A\n\x18\x41\x63tivityGetRewardRequest\x12\x0f\n\x07session\x18\x01 \x02(\x0c\x12\x14\n\x0c\x63ondition_id\x18\x02 \x02(\x05\"l\n\x19\x41\x63tivityGetRewardResponse\x12\x0b\n\x03ret\x18\x01 \x02(\x05\x12\x0f\n\x07session\x18\x02 \x02(\x0c\x12\x31\n\x06reward\x18\x03 \x01(\x0b\x32!.Sanguo.protocol.world.Attachment')



_ACTIVITYENTRY_ACTIVITYCONDITION_STATUS = _descriptor.EnumDescriptor(
  name='Status',
  full_name='Sanguo.protocol.activity.ActivityEntry.ActivityCondition.Status',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='HAS_GOT', index=0, number=1,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CAN_GET', index=1, number=2,
      options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CAN_NOT', index=2, number=3,
      options=None,
      type=None),
  ],
  containing_type=None,
  options=None,
  serialized_start=324,
  serialized_end=371,
)


_ACTIVITYENTRY_ACTIVITYCONDITION = _descriptor.Descriptor(
  name='ActivityCondition',
  full_name='Sanguo.protocol.activity.ActivityEntry.ActivityCondition',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='Sanguo.protocol.activity.ActivityEntry.ActivityCondition.id', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='status', full_name='Sanguo.protocol.activity.ActivityEntry.ActivityCondition.status', index=1,
      number=2, type=14, cpp_type=8, label=2,
      has_default_value=False, default_value=1,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _ACTIVITYENTRY_ACTIVITYCONDITION_STATUS,
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=209,
  serialized_end=371,
)

_ACTIVITYENTRY = _descriptor.Descriptor(
  name='ActivityEntry',
  full_name='Sanguo.protocol.activity.ActivityEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='Sanguo.protocol.activity.ActivityEntry.id', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='current_value', full_name='Sanguo.protocol.activity.ActivityEntry.current_value', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='left_time', full_name='Sanguo.protocol.activity.ActivityEntry.left_time', index=2,
      number=3, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='conditions', full_name='Sanguo.protocol.activity.ActivityEntry.conditions', index=3,
      number=4, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[_ACTIVITYENTRY_ACTIVITYCONDITION, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=58,
  serialized_end=371,
)


_ACTIVITYNOTIFY = _descriptor.Descriptor(
  name='ActivityNotify',
  full_name='Sanguo.protocol.activity.ActivityNotify',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='session', full_name='Sanguo.protocol.activity.ActivityNotify.session', index=0,
      number=1, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='activities', full_name='Sanguo.protocol.activity.ActivityNotify.activities', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=373,
  serialized_end=467,
)


_ACTIVITYUPDATENOTIFY = _descriptor.Descriptor(
  name='ActivityUpdateNotify',
  full_name='Sanguo.protocol.activity.ActivityUpdateNotify',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='session', full_name='Sanguo.protocol.activity.ActivityUpdateNotify.session', index=0,
      number=1, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='activities', full_name='Sanguo.protocol.activity.ActivityUpdateNotify.activities', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=469,
  serialized_end=569,
)


_ACTIVITYGETREWARDREQUEST = _descriptor.Descriptor(
  name='ActivityGetRewardRequest',
  full_name='Sanguo.protocol.activity.ActivityGetRewardRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='session', full_name='Sanguo.protocol.activity.ActivityGetRewardRequest.session', index=0,
      number=1, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='condition_id', full_name='Sanguo.protocol.activity.ActivityGetRewardRequest.condition_id', index=1,
      number=2, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=571,
  serialized_end=636,
)


_ACTIVITYGETREWARDRESPONSE = _descriptor.Descriptor(
  name='ActivityGetRewardResponse',
  full_name='Sanguo.protocol.activity.ActivityGetRewardResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='ret', full_name='Sanguo.protocol.activity.ActivityGetRewardResponse.ret', index=0,
      number=1, type=5, cpp_type=1, label=2,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='session', full_name='Sanguo.protocol.activity.ActivityGetRewardResponse.session', index=1,
      number=2, type=12, cpp_type=9, label=2,
      has_default_value=False, default_value="",
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
    _descriptor.FieldDescriptor(
      name='reward', full_name='Sanguo.protocol.activity.ActivityGetRewardResponse.reward', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  extension_ranges=[],
  serialized_start=638,
  serialized_end=746,
)

_ACTIVITYENTRY_ACTIVITYCONDITION.fields_by_name['status'].enum_type = _ACTIVITYENTRY_ACTIVITYCONDITION_STATUS
_ACTIVITYENTRY_ACTIVITYCONDITION.containing_type = _ACTIVITYENTRY;
_ACTIVITYENTRY_ACTIVITYCONDITION_STATUS.containing_type = _ACTIVITYENTRY_ACTIVITYCONDITION;
_ACTIVITYENTRY.fields_by_name['conditions'].message_type = _ACTIVITYENTRY_ACTIVITYCONDITION
_ACTIVITYNOTIFY.fields_by_name['activities'].message_type = _ACTIVITYENTRY
_ACTIVITYUPDATENOTIFY.fields_by_name['activities'].message_type = _ACTIVITYENTRY
_ACTIVITYGETREWARDRESPONSE.fields_by_name['reward'].message_type = world_pb2._ATTACHMENT
DESCRIPTOR.message_types_by_name['ActivityEntry'] = _ACTIVITYENTRY
DESCRIPTOR.message_types_by_name['ActivityNotify'] = _ACTIVITYNOTIFY
DESCRIPTOR.message_types_by_name['ActivityUpdateNotify'] = _ACTIVITYUPDATENOTIFY
DESCRIPTOR.message_types_by_name['ActivityGetRewardRequest'] = _ACTIVITYGETREWARDREQUEST
DESCRIPTOR.message_types_by_name['ActivityGetRewardResponse'] = _ACTIVITYGETREWARDRESPONSE

class ActivityEntry(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType

  class ActivityCondition(_message.Message):
    __metaclass__ = _reflection.GeneratedProtocolMessageType
    DESCRIPTOR = _ACTIVITYENTRY_ACTIVITYCONDITION

    # @@protoc_insertion_point(class_scope:Sanguo.protocol.activity.ActivityEntry.ActivityCondition)
  DESCRIPTOR = _ACTIVITYENTRY

  # @@protoc_insertion_point(class_scope:Sanguo.protocol.activity.ActivityEntry)

class ActivityNotify(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _ACTIVITYNOTIFY

  # @@protoc_insertion_point(class_scope:Sanguo.protocol.activity.ActivityNotify)

class ActivityUpdateNotify(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _ACTIVITYUPDATENOTIFY

  # @@protoc_insertion_point(class_scope:Sanguo.protocol.activity.ActivityUpdateNotify)

class ActivityGetRewardRequest(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _ACTIVITYGETREWARDREQUEST

  # @@protoc_insertion_point(class_scope:Sanguo.protocol.activity.ActivityGetRewardRequest)

class ActivityGetRewardResponse(_message.Message):
  __metaclass__ = _reflection.GeneratedProtocolMessageType
  DESCRIPTOR = _ACTIVITYGETREWARDRESPONSE

  # @@protoc_insertion_point(class_scope:Sanguo.protocol.activity.ActivityGetRewardResponse)


# @@protoc_insertion_point(module_scope)