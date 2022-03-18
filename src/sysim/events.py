"""
Classes implementing custom events.
"""

import simpy

class UrgentEvent(simpy.Event):
    """A generic event that gets scheduled as URGENT."""
    def __init__(self, env):
        super().__init__(env)

    def succeed(self, value=None):
        """Set the event's value, mark it as successful and schedule it for
        processing by the environment. Returns the event instance.
        """
        if self._value is not simpy.events.PENDING:
            raise RuntimeError(f'{self} has already been triggered')

        self._ok = True
        self._value = value
        self.env.schedule(self, simpy.events.URGENT)
        return self
