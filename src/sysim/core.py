"""
Core functions and main simulator object for event-discrete simulation environment.
"""

from sysim.simulator import Simulator
from functools import wraps

simulator = None
"""Global simulation object."""

def simulator_check(func):
    """Decorator for ensuring that the simulator object has been initialized."""
    @wraps(func)
    def wrapper_simulator_check(*args, **kwargs):
        if simulator is None:
            raise RuntimeError("Simulator has not been initialized")
        return func(*args, **kwargs)
    return wrapper_simulator_check

def initialize(instance, timescale=1, logger=None):
    """Initialize the simulator for the given module instance and the given timescale, i.e. minimum simulation step.

    :param instance: :class:`Module` instance to simulate.
    :type instance: :class:`Module`
    :param timescale: Minimum simulation timestep size, defaults to 1
    :type timescale: int, optional
    :param logger: :class:`Logger` object for logging events, defaults to None
    :type logger: :class:`Logger`, optional
    """
    global simulator
    simulator = Simulator(instance, timescale, logger)

@simulator_check
def now(scaled=True):
    """Returns the current simulation time in units of seconds or in simulation time
    units.

    :param scaled: Scale the simulation time to seconds, defaults to True
    :type scaled: bool, optional
    :return: Simulation time as a float value when the unit is seconds or an integer when the unit is simulation time.
    :rtype: float or int
    """
    return simulator.now(scaled)

@simulator_check
def wait(delay):
    """Returns an event suitable for waiting for the given delay in seconds.

    :param delay: Number of seconds to wait.
    :type delay: float
    :return: Event that can be returned in a yield statement.
    :rtype: :class:`simpy.Event`
    """
    return simulator.wait(delay)

@simulator_check
def run(until):
    """Runs the simulation until the given time value in seconds.

    :param until: Time until which the simulation should run in seconds.
    :type until: real
    """
    simulator.run(until)

@simulator_check
def schedule(generator):
    """Schedule a process (generator) for execution by the simulator.

    :param generator: The generator to be scheduled.
    :type generator: :class:`simpy.ProcessGenerator`
    :return: An object capturing the details of the process.
    :rtype: :class:`simpy.Process`
    """
    return simulator.process(generator)

@simulator_check
def event():
    """Create a generic simulation event.

    :return: The generic event object.
    :rtype: :class:`simpy.Event`
    """
    return simulator.event()

@simulator_check
def urgent_event():
    """Create a generic simulation event marked for urgent execution.

    :return: The generic event object.
    :rtype: :class:`sysim.UrgentEvent`
    """
    return simulator.urgent_event()

@simulator_check
def change(handle, value):
    """Change the value of the given signal to the given value for logging purposes.

    :param handle: The signal whose value was changed.
    :type handle: :class:`Variable`
    :param value: The new value of the signal.
    :type value: Any Python type
    """
    simulator.change(handle, value)

@simulator_check
def anyof(events):
    """Returns an event that succeeds if any of the events in the list succeeds.

    :param events: List of events to wait for
    :type events: List[Event]
    """
    return simulator.anyof(events)
