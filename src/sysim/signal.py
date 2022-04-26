"""
Defines classes to represent signals and ports within the System Simulation
framework.
"""
import simpy
import copy

from sysim.core import (
    urgent_event, wait, now, schedule,
)
from sysim.types import (
  Struct
)

from enum import Enum

class PortDirection(Enum):
    """Port direction selection."""
    INPUT = 'input'
    OUTPUT = 'output'
    INOUT = 'inout'

class SubSignal:
    """Class representing a signal within a composite type."""
    def __init__(self, parent, name):
        self._parent = parent
        self._name = name

    def __ilshift__(self, other):
        """Remap the <<= operator to assignment."""
        self.assign(other)
        return self

    def assign(self, other, delay=None):
        next_value = self._parent.next_value
        setattr(next_value, self._name, other)
        self._parent.assign(next_value, delay)

class Signal:
    """Class representing a loggable signal. A signal can be assigned with or
    without a delay and can propagate its value to other signals."""

    def __init__(self, signal_type=None, initial_value=None):
        self._scope = None
        self._name = None
        # Connections to other signals driven by this signal
        self._sinks = []
        # Connections to other signals driving this signal
        self._sources = []
        # List of embedded signals for complex types
        self._signals = []
        # Last, next and current value
        self._last_value = None
        self._next_value = None
        self._value      = None
        self._initial_value = initial_value
        # Timestamp of when _last_value was updated
        self._last_value_change = 0
        # Registered events
        self._rising_edge = None
        self._falling_edge = None
        self._event = None
        # Information for logger
        self._signal_type = signal_type
        self._log_handles = None
        # Set when we are updating
        self._action = None
        # Special handling of Struct types
        if isinstance(signal_type, Struct):
            for field in signal_type.fields:
                setattr(self, field, SubSignal(self, field))

    def __call__(self, value=None):
        if value is None:
            return self._value
        else:
            self.assign(value)

    def _update_log(self, force=False):
        """Update the log in case our value has changed."""
        if self._value is not None and (force or (self._last_value != self._value)):
            try:
                self._signal_type.log(self._value, self._log_handles)
            except ValueError:
                print(f"Unable to assign {self._value} to {self.scope}.{self.name} of type {type(self._signal_type).__name__}")

    def _update_events(self):
        """Check how our value has changed and optionally fire off any relevant
        and registered events. For example, when a rising edge is detected, we fire
        the 'rising_edge' event in case it has been registered."""
        if self._last_value is not None and self._value is not None:
            if self._rising_edge is not None:
                if not int(self._last_value) and int(self._value):
                    self._rising_edge.succeed()
                    self._rising_edge = None

            if self._falling_edge is not None:
                if int(self._last_value) and not int(self._value):
                    self._falling_edge.succeed()
                    self._falling_edge = None

        if self._last_value != self._value:
            if self._event is not None:
                self._event.succeed()
                self._event = None

    def _update_state(self):
        """Update the state of the signal based on a registered next value. The
        state is only updated if the signal has reacted to an event or a new
        value has been assigned."""
        if self._value != self._next_value:
            self._last_value_change = now()
        self._last_value, self._value, self._next_value = self._value, self._next_value, None

    def _update_internals(self, source):
        """Update all the internals based on a given source, which is also assumed
        to be a signal. Also updates all connected signals. The source indicates
        the original source of the event that has triggered this update. The
        source is used to prevent infinite loops in case e.g. a bidirectional signal is drive."""
        self._update_state()
        self._update_events()
        self._update_log()

        # Also update all connected signals
        for connection in self._sinks:
            # But not if the connection is actually the source of the event
            if source is None or connection != source:
                connection._update_internals(source)

    def _update(self, delay=None, source=None):
        """Update the state of the signal after a certain delay. Optionally, the
        source of the update, in case it is another signal, can be indicated."""
        while True:
            # Use try/except to enable delay to be cancelled
            # by another update to the signal
            try:
                if delay is not None:
                    yield wait(delay)
                break
            except simpy.Interrupt as e:
                delay = e.cause
        self._update_internals(source)
        self._action = None

    def _update_last_value(self, value, source):
        """Force the last value of a signal without triggering an update. Also propagates
        the new value to all connected signals. Mainly used to propagate a new last value
        to all connected signals prior to starting the simulation."""

        self._last_value = value
        self._value = value

        for sink in self._sinks:
            if sink != source:
                sink._update_last_value(value, self)

    def _update_next_value(self, value, source):
        """Force the next value of a signal without triggering an update. Also propagates
        the new value to all connected signals. Mainly used to propagate a new value
        to all connected signals prior to invoking the delay functionality."""

        self._next_value = value
        for sink in self._sinks:
            if sink != source:
                sink._update_next_value(value, self)

    def propagate_initial_value(self):
        """Propagate initial value to self and all connected signals."""
        if self._initial_value is not None:
            self._update_last_value(self._initial_value, self)

    def log_initial_value(self):
        """Update log file with an initial value."""
        self._signal_type.log(self._value, self._log_handles)

    def initialize(self, path):
        """Initialize the state of the signal and optionally register it with a logger."""
        if self._name is None:
            self._name = path.split(".")[-1]
        if self._scope is None:
            self._scope = ".".join(path.split(".")[:-1])

    def disconnect(self, signal):
        """Remove a signal from the connection list of this signal or port."""
        if not isinstance(signal, Signal) or signal not in self._sinks:
            raise ValueError(f"{signal.name} not connected to {self.name}!")

        self._sinks.remove(signal)
        signal._sources.remove(self)

    def connect(self, other):
        """Add a signal to the connection list of this signal or port."""
        if not isinstance(other, Signal):
            raise ValueError(f"Unable to bind something that is not a signal to {self.name}!")

        if other in self._sinks:
            raise ValueError(f"{other.name} already connected to {self.name}!")

        self._sinks.append(other)
        other._sources.append(self)

    def __ilshift__(self, other):
        """Remap the <<= operator to the binding function for convenience. Can also
        be used for assignment."""
        if isinstance(other, Signal):
            other.connect(self)
        else:
            self.assign(other)

        return self

    def assign(self, value, delay=None):
        """Assign a new value to the signal after an optional delay in units
        of seconds."""
        self._update_next_value(value, self)
        if self._action is not None:
            self._action.interrupt(delay)
        else:
            self._action = schedule(self._update(delay, self))

    @property
    def rising_edge(self):
        """Create an event that is triggered by a rising edge on this signal."""
        if self._rising_edge is None:
            self._rising_edge = urgent_event()
        return self._rising_edge

    @property
    def falling_edge(self):
        """Create an event that is triggered by a falling edge on this signal."""
        if self._falling_edge is None:
            self._falling_edge = urgent_event()
        return self._falling_edge

    @property
    def event(self):
        """Create an event that is triggered by any change on this signal."""
        if self._event is None:
            self._event = urgent_event()
        return self._event

    def stable(self, interval):
        """Returns true if the signal has been stable (no value change) for the
        given amount of time."""
        return (now() - self._last_value_change) > interval

    def register(self, logger):
        """Register signal for logging."""
        self._log_handles = self._signal_type.register(logger, self.scope, self.name)

    def register_alias(self, logger, scope):
        """Register signal as alias for logging."""
        self._signal_type.register(logger, scope, self.name, self._log_handles)

    @property
    def name(self):
        """Return the name of the signal."""
        return self._name

    @property
    def scope(self):
        """Return the name of the scope of the signal, i.e. surrounding hierarchy."""
        return self._scope

    @property
    def type(self):
        """Return the type of the signal for data conversion purposes."""
        return self._signal_type

    @property
    def value(self):
        """Return the current value of the signal."""
        return self._value

    @property
    def last_value(self):
        """Return the value of the signal prior to the last change."""
        return self._last_value

    @property
    def next_value(self):
        """Return the value of the signal scheduled for the next update."""
        if self._next_value is None:
            return copy.copy(self._value)
        else:
            return self._next_value

    @property
    def last_event(self):
        """Return the time since the last value change on the signal."""
        return now() - self._last_value_change

    @property
    def sinks(self):
        """Return a list of signals driven by this one."""
        return self._sinks

    @property
    def sources(self):
        """Return a list of signals driving this one."""
        return self._sources

def signal(signal_type, initial_value=None):
    """Create a :class:`sysim.Signal` with the given type used for formatting purposes.

    :param signal_type: Type definition used for formatting the value of the signal for logging purposes.
    :type signal_type: :class:`sysim.TypeBase`
    :return: The created signal.
    :rtype: :class:`sysim.Signal`
    """
    return Signal(signal_type=signal_type, initial_value=initial_value)

class Port(Signal):
    """A port represents an interface on a module. A port can have a direction
    associated with it. A port will propagate its value to bound signals, but the
    direction of propagation is given by the port direction, enabling simpler syntax
    when binding it."""
    def __init__(self, port_direction=None, signal_type=None, initial_value=None):
        super().__init__(signal_type, initial_value=initial_value)
        self._direction = port_direction

    def bind(self, other):
        """Connect the port to another signal. Uses the configured direction to
        set up the source and sink of the connection correctly."""
        if self.direction == PortDirection.INPUT:
            other._sinks.append(self)
            self._sources.append(other)
        elif self.direction == PortDirection.OUTPUT:
            self._sinks.append(other)
            other._sources.append(self)
        elif self.direction == PortDirection.INOUT:
            other._sinks.append(self)
            other._sources.append(self)
            self._sinks.append(other)
            self._sources.append(other)

    @property
    def direction(self):
        """Returns the direction of the port."""
        return self._direction

def input(signal_type):
    """Create an input :class:`sysim.Port` with the given type used for formatting purposes.

    :param signal_type: Type definition used for formatting the value of the signal for logging purposes.
    :type signal_type: :class:`sysim.TypeBase`
    :return: The created port.
    :rtype: :class:`sysim.Port`
    """
    return Port(port_direction=PortDirection.INPUT, signal_type=signal_type)

def output(signal_type, initial_value=None):
    """Create an output :class:`sysim.Port` with the given type used for formatting purposes.

    :param signal_type: Type definition used for formatting the value of the signal for logging purposes.
    :type signal_type: :class:`sysim.TypeBase`
    :return: The created port.
    :rtype: :class:`sysim.Port`
    """
    return Port(port_direction=PortDirection.OUTPUT, signal_type=signal_type, initial_value=initial_value)

def inout(signal_type, initial_value=None):
    """Create a bidirectional :class:`sysim.Port` with the given type used for formatting purposes.

    :param signal_type: Type definition used for formatting the value of the signal for logging purposes.
    :type signal_type: :class:`sysim.TypeBase`
    :return: The created port.
    :rtype: :class:`sysim.Port`
    """
    return Port(port_direction=PortDirection.INOUT, signal_type=signal_type, initial_value=initial_value)
