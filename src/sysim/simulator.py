"""
Class implementing the overall simulator within the System Simulation environment.
"""

import simpy
from sysim.events import UrgentEvent

class Simulator:
    """Main class that encapsulates the simulator functionality."""

    def __init__(self, instance, timescale=1, logger=None):
        """Initialize the simulator for a specific Module instance. The 'timescale'
        denotes the smallest unit of time available in the simulator. A 'logger' object
        can optionally be attached, which can be used for writing simulation events
        to a file."""
        self._env = simpy.Environment()
        self._timescale = timescale
        self._instance = instance
        self._logger = logger

    @property
    def timescale(self):
        """Returns the timescale configured for the simulation."""
        return self._timescale

    def change(self, signal, value):
      """If a logger is defined, change the value of a registered signal
      to the new value."""
      if self._logger is not None:
          self._logger.change(signal, value)

    def event(self):
        """Returns a generic event for use by processes in Modules."""
        return simpy.Event(self._env)

    def urgent_event(self):
        """Returns a generic urgent event for use by processes in Modules."""
        return UrgentEvent(self._env)

    def now(self, scaled=True):
        """Returns the current simulation time in units of the defined timescale
        or, optionally, in raw simulation integer time-ticks."""
        if scaled:
            return self._env.now*self.timescale
        else:
            return self._env.now

    def wait(self, time):
        """Returns an event that can be used for waiting for a given amount
        of time in units of the defined timescale."""
        return self._env.timeout(max(1, int(time/self.timescale)))

    def anyof(self, events):
        return simpy.events.AnyOf(self._env, events)

    def run(self, until):
        """Run the simulation until the given time in units of the defined timescale."""
        if self._env.now == 0:
            self._instance.initialize(self._instance.__class__.__name__)
            if self._logger is not None:
                self._logger.initialize(self._instance, self.timescale)
            self._instance.propagate_initial_values()
            self._instance.log_initial_values()
        self._env.run(until=int(until/self.timescale))
        if self._logger is not None:
            self._logger.flush(self._env.now)

    def process(self, event):
        """Registers an event for processing by the simulator."""
        return self._env.process(event)
