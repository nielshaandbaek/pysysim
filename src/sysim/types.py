"""
Classes supporting converting values for logging purposes.
"""

import copy

from re import S
from types import SimpleNamespace
from abc import ABC
from sysim.core import (
  change
)

class TypeBase(ABC):
    """Base class for providing information to the logger about how to format
    variables in the VCD file."""
    def __init__(self, log_type = None, log_size = None):
        self._log_type = log_type
        self._log_size = log_size
        super().__init__()

    @property
    def default(self):
        return 0

    def conv(self, value):
        return value

    def register(self, logger, scope, name, handle=None):
        if self._log_type is not None:
            if handle is not None:
                handle = logger.register_alias(handle, scope, name)
            else:
                handle = logger.register(scope, name, self._log_type, self._log_size)

        return handle

    def log(self, value, handle):
        change(handle, self.conv(value))

    def __call__(self, value):
        return self.conv(value)

class Struct(TypeBase):
    """Base class for composite type"""
    def __init__(self, **kwargs):
        self._entries = dict()
        self._entries.update(kwargs)
        super().__init__()

    def __contains__(self, key):
        return key in self._entries

    @property
    def fields(self):
        return self._entries.keys()

    def register(self, logger, scope, name, handles=None):
        if handles is None:
          handles = dict()

        for key, type in self._entries.items():
            if key in handles:
                logger.register_alias(handles[key], f"{scope}.{name}", key)
            elif not key.startswith('_'):
                handles[key] = logger.register(f"{scope}.{name}", key, type._log_type, type._log_size)

        return handles

    def log(self, value, handles):
        if value is None:
            return

        for i, key in enumerate(self._entries.keys()):
            try:
                key_value = None

                if key.startswith('_'):
                    continue
                elif hasattr(value, key):
                    key_value = getattr(value, key)
                elif isinstance(value, dict):
                    key_value = value[key]
                elif isinstance(value, list):
                    key_value = value[i]
                else:
                    key_value = value

                if key_value is not None:
                    change(handles[key], self._entries[key](key_value))

            except ValueError as e:
                print(f"Unable to assign element {key} with value {value} to type {type(self._entries[key]).__name__}")

    @property
    def default(self):
        return SimpleNamespace(**{key: value.default for key, value in self._entries.items()})

    def conv(self, value):
        conv_value = self.default
        if isinstance(value, dict):
            conv_value.update(value)
        elif isinstance(value, list):
            keys = self._entries.keys()
            for i, elem in enumerate(value):
                if i < len(keys):
                    conv_value[keys[i]] = elem
        else:
            conv_value = value

        return conv_value

    def __call__(self, **kwargs):
        conv_value = self.default
        for key, value in kwargs.items():
            setattr(conv_value, key, value)
        return conv_value

class Simple(TypeBase):
    """Singleton type for formatting e.g. single bit and integer signals."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

class Bit(Simple):
    """Type for formatting a signal as a bit labelled as 'wire' in a VCD file."""
    def __init__(self):
        super().__init__('wire', 1)

class BitVector(TypeBase):
    """Type for formatting a signal as a bit vector with a specific size and labelled as 'wire' in a VCD file."""
    def __init__(self, size):
        super().__init__('wire', size)

class Reg(Simple):
    """Type for formatting a signal as a bit labelled as 'reg' in a VCD file."""
    def __init__(self):
        super().__init__('reg', 1)

class RegVector(TypeBase):
    """Type for formatting a signal as a bit vector with a specific size and labelled as 'reg' in a VCD file."""
    def __init__(self, size):
        super().__init__('reg', size)

class String(TypeBase):
    def __init__(self, size):
        super().__init__('string', size)

    @property
    def default(self):
        return ''

class Int(Simple):
    """Type for formatting a signal as a 64-bit integer value labelled as 'wire' in a VCD file."""
    def __init__(self):
        super().__init__('integer')

class Real(Simple):
    """Type for formatting a signal as a 64-bit floating point value labelled as 'wire' in a VCD file."""
    def __init__(self):
        super().__init__('real')

class Event(Simple):
    """Type for formatting a signal as an 'event' in a VCD file."""
    def __init__(self):
        super().__init__('event')

    # Events cannot actually log anything
    def log(self, value, handle):
        change(handle, 1)

    def conv(self, value):
        return 1

    @property
    def default(self):
        return None