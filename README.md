# pySySim

Python package for making simple System Simulations using an event
driven simulation framework.

## Getting started

The following code shows a minimal example of a testbench with a simple
clock signal and a counter. The simulation is executed for 100 ns and
generates a VCD file with all registered signals.

```python
import sysim

class Counter(sysim.Module):
    """A simple clocked integer counter."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create clock input
        self.clk_i = sysim.input(sysim.Bit)
        # Create counter output
        self.cnt_o = sysim.output(sysim.Int)

    @sysim.process
    def run(self):
        """Main clocked process executed when simulation starts."""
        # Reset clock output
        self.cnt_o.assign(0)
        # Counter will run until simulation finishes
        while True:
            # Wait for a rising edge on the clock
            yield self.clk_i.rising_edge()
            # Update counter value
            self.cnt_o <<= self.cnt_o.value + 1

class TB(sysim.Module):
    """A simple testbench for the counter module."""
    def __init__(self):
        super().__init__()
        # Create testbench signal for clock with default value 0
        self.clk = sysim.signal(sysim.Bit, 0)
        # Create testbench signal for counter value
        self.cnt = sysim.signal(sysim.Int)
        # Instantiate counter and bind ports to testbench signals
        self.i_cnt = Counter(clk_i=self.clk, cnt_o=self.cnt)

    @sysim.process
    def clock(self):
        """Clock process running forever."""
        while True:
            # Generate square wave on clock with 20 ns period (all times
            # are in units of seconds)
            self.clk <<= 1
            yield sysim.wait(10e-9)
            self.clk <<= 0
            yield sysim.wait(10e-9)

# Create an instance of the testbench
tb = TB()
# Create a VCD type logger
logger = sysim.VcdLogger("test_cnt.vcd")
# Initialize simulation with a timescale of 1 ns and the specified logger
sysim.initialize(tb, 1e-9, logger)
# Run simulation for 100 ns
sysim.run(100e-9)
logger.flush()
assert tb.cnt.value == 5
```

## Requirements

pySySim requires Python >= 3.7, pyVCD and SimPy. The requirements should be installed
automatically as they are available on PyPI.

## Installation

Install locally using [pip](http://pypi.python.org/pypi/pip):

```bash
$ pip3 install -e pysysim
```

## Documentation

In the `docs`folder simply run

```bash
$ make html
```

to build the documentation, which can then be found in the build folder.
