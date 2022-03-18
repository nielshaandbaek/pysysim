"""
Classes supporting logging simulation results in various formats. Currently, only
a logging class supporting writing signal events to VCD files is provided.
"""
import math
import vcd

from sysim.core import (
    now,
)
from sysim.signal import Signal
from sysim.module import Module

def timescale2str(timescale):
    """Converts a timescale as a real number into a string with units of s, ms, etc."""
    units = ['s', 'ms', 'us', 'ns', 'ps', 'fs']
    unit = 0
    ts = timescale
    while unit < len(units):
        _, whole = math.modf(ts)
        if whole >= 1:
            return f"{int(ts)} {units[unit]}"
        else:
            unit += 1
            ts *= 1000

    raise ValueError(f"Invalid timescale {timescale} selected!")

class VcdLogger:
    """Class for logging signal events to Value Change Dump (VCD) files."""

    def __init__(self, path):
        """Initialize the logger to write to a specific path."""
        self._path = path
        self._vars = dict()

    def initialize(self, instance, timescale):
        """Initialize the logger with a given timescale. Causes the VCD file to
        be created."""
        self._vcd = vcd.VCDWriter(open(self._path, 'w'), timescale=timescale2str(timescale))
        self.register(instance)

    def register(self, item):
        """Register a signal or an instance for logging. For signals,
        a specific scope and name will be used for logging. The type property
        describes how the variable will be formatted in the file."""
        if isinstance(item, Module):
            # Register all signals
            for signal in item.signals:
                self.register(signal)

            # The register all sub-instances
            for instance in item.instances:
                self.register(instance)
        elif isinstance(item, Signal) and item.type is not None:
            if item.scope not in self._vars:
                self._vars[item.scope] = list()

            if item.name in self._vars[item.scope]:
                raise KeyError(f"Variable in scope {item.scope} with name {item.name} has already been defined!")
            item.register(self._vcd)
            self._vars[item.scope].append(item.name)
            #self.change(item, item.value)

    def change(self, signal, value):
        """Change the value in the log file of the given signal. Will simply return
        in case the signal has not been registered."""
        if signal.scope in self._vars and \
           signal.name in self._vars[signal.scope]:
            self._vars[signal.scope][signal.name].change(self._vcd, value)

    def flush(self, timestamp=None):
        """Flush the already logged data to the VCD file."""
        self._vcd.flush(timestamp)
