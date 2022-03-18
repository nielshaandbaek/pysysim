"""
Classes supporting converting values for logging purposes.
"""

import copy

from re import S
from collections import namedtuple
from sysim.core import (
  now
)

class TypeBase:
    """Base class for providing information to the logger about how to format
    variables in the VCD file."""
    def __init__(self, log_type, log_size):
        self._logger = None
        self._log_handle = None
        self._log_type = log_type
        self._log_size = log_size

    def conv(self, value):
        return value

    def register(self, logger, scope, name):
        self._logger = logger
        self._log_handle = logger.register_var(scope, name, self._log_type, self._log_size)

    def log(self, value):
        if self._logger is not None and value is not None:
            self._logger.change(self._log_handle, now(False), value)

    def __call__(self, value):
        return value

class Struct:
    """Base class for composite type"""
    def __init__(self, **kwargs):
        self._entries = dict()
        self._log_handles = dict()
        for key, type in kwargs.items():
            self._entries[key] = copy.copy(type)

    @property
    def entries(self):
        return self._entries

    def register(self, logger, scope, name):
        self._logger = logger
        for key, type in self._entries.items():
            self._log_handles[key] = logger.register_var(f"{scope}.{name}", key, type._log_type, type._log_size)

    def log(self, value):
        for key in self._entries.keys():
            try:
                self._logger.change(self._log_handles[key], now(False), getattr(value, key))
            except AttributeError:
                if isinstance(value, dict):
                    self._logger.change(self._log_handles[key], now(False), value[key])
                else:
                    self._logger.change(self._log_handles[key], now(False), value)

    def conv(self, value):
        if isinstance(value, dict):
            return namedtuple("StructConv", value.keys())(**value)
        else:
            return value

    def __call__(self, **kwargs):
        return namedtuple("StructValue", kwargs.keys())(**kwargs)

class BitVector(TypeBase):
    """Type for formatting a signal as a bit vector with a specific size and labelled as 'wire' in a VCD file."""
    def __init__(self, size):
        super().__init__('wire', size)

class RegVector(TypeBase):
    """Type for formatting a signal as a bit vector with a specific size and labelled as 'reg' in a VCD file."""
    def __init__(self, size):
        super().__init__('reg', size)

class String(TypeBase):
    def __init__(self, size):
        super().__init__('string', size)

Bit  = TypeBase('wire', 1)
"""Short-hand type for a single bit 'wire'."""

Reg  = TypeBase('reg', 1)
"""Short-hand type for a single bit 'reg'."""

Int  = TypeBase('integer', None)
"""Short-hand type for a 64-bit integer labelled as 'wire'."""

Real = TypeBase('real', None)
"""Short-hand type for a 64-bit floating point value labelled as 'wire'."""
