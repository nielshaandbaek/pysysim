"""
Classes supporting the creation of Modules. Modules a the basic unit of
organization within the System Simulation environment. Modules support the
creation of submodules and may contain Ports for interfacing with other modules,
Signals for internal state that can be logged to a result file, and processes
that execute actual functionality.
"""

from sysim.core import schedule
from sysim.signal import Signal, Port

def process(f):
    """Decorator function for setting a 'process' label on a function or method
    marking it for execution at the start of the simulation."""
    f.process = True
    return f

def _gather(item_or_dict_or_list, item_type):
    """Gather all instances of a specific type from a dict or a list."""
    instances = []

    if isinstance(item_or_dict_or_list, list):
        for index, item in enumerate(item_or_dict_or_list):
            instances.extend(_gather(item, item_type))
    elif isinstance(item_or_dict_or_list, dict):
        for attr, value in item_or_dict_or_list.items():
            if not attr.startswith('_'):
                instances.extend(_gather(value, item_type))
    elif isinstance(item_or_dict_or_list, item_type):
        instances.append(item_or_dict_or_list)

    return instances

class ModuleBase(type):
    """Metaclass for modules that enables methods to be tagged and maintains
    a list of those methods. In particular, this is used to enable the user
    to tag methods that are processes, which will then automatically be started
    when the simulation is initialized."""
    def __init__(cls, name, bases, attrs):
        tagged = set()
        for name, method in attrs.items():
            if hasattr(method, 'process'):
                tagged.add(name)

        @property
        def processes(self):
            tags = tagged.copy()
            try:
                tags.update(super(cls, self).processes)
            except AttributeError:
                pass
            return tags

        cls.processes = processes

class Module(metaclass=ModuleBase):
    """Class implementing a generic module that can contain ports, signals,
    processes as well as instances of other modules."""
    def __init__(self, **kwargs):
        self._name = None
        self._kwargs = kwargs

    def _initialize_recursive(self, name, value, data_type):
        if name.startswith('_'):
            return
        if isinstance(value, data_type):
            value.initialize(f"{self.name}.{name}")
        elif isinstance(value, list):
            for index, list_value in enumerate(value):
                self._initialize_recursive(f"{name}({index})", list_value, data_type)
        elif isinstance(value, dict):
            for attr, dict_value in value.items():
                self._initialize_recursive(f"{name}.{attr}", dict_value, data_type)

    def _initialize_port_bindings(self):
        # Setup any port bindings defined in our constructor arguments
        for attr, value in self._kwargs.items():
            if not hasattr(self, str(attr)):
                raise KeyError(f"In {self.name}, port {attr} has not been defined in {self.name}!")
            port = getattr(self, str(attr))
            if isinstance(port, list):
                if not isinstance(value, list):
                    if len(port) == 1:
                        value = [value]
                    else:
                        raise ValueError(f"In {self.name}, cannot bind list port {attr} to non-list signal.")
                for this, that in zip(port, value):
                    this.bind(that)
            elif isinstance(port, Port):
                port.bind(value)
            else:
                raise ValueError(f"In {self.name}, named object {attr} is not a port!")

    def initialize(self, name):
        """Initialize the module at the beginning of the simulation."""
        self._name = name

        # Setup all port bindings
        self._initialize_port_bindings()

        # Initialize all instances
        for attr, value in self.__dict__.items():
            self._initialize_recursive(attr, value, Module)

        # Initialize all signals ports
        for attr, value in self.__dict__.items():
            self._initialize_recursive(attr, value, Signal)

        for proc in self.processes:
            schedule(getattr(self, proc)())

    def propagate_initial_values(self):
        for instance in self.instances:
            instance.propagate_initial_values()

        for signal in self.signals:
            signal.propagate_initial_value()

    def log_initial_values(self):
        for instance in self.instances:
            instance.log_initial_values()

        for signal in self.signals:
            signal.log_initial_value()

    @property
    def name(self):
        """Returns the name of the instance of the module."""
        return self._name

    @property
    def instances(self):
        """Returns all instances defined in this module."""
        return _gather(self.__dict__, Module)

    @property
    def signals(self):
        """Returns all signals defined in this module."""
        return _gather(self.__dict__, Signal)
