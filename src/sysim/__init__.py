"""
The ``sysim`` module aggregates PySySim's most used components into a single
namespace. This is purely for convenience. You can of course also access
everything (and more!) via their actual submodules.

The following tables list all of the available components in this module.

{toc}
"""
import pkgutil

from .logging import (
    VcdLogger,
)
from .types import (
    Struct, Bit, Reg, Int, Real, BitVector, RegVector, String, Event,
)
from .core import (
    initialize, now, run, event, urgent_event, wait, schedule, anyof
)
from .signal import signal, input, output, inout
from .module import Module, process

def compile_toc(entries, section_marker='='):
    """Compiles a list of sections with objects into sphinx formatted
    autosummary directives."""
    toc = ''
    for section, objs in entries:
        toc += '\n\n'
        toc += f'{section}\n'
        toc += f'{section_marker * len(section)}\n\n'
        toc += '.. autosummary::\n\n'
        for obj in objs:
            try:
                toc += f'    ~{obj.__module__}.{obj.__name__}\n'
            except AttributeError:
                pass
    return toc

toc = (
    ('Simulation', (
        signal, input, output, inout, Module, VcdLogger,
    )),
    ('Functions', (
        initialize, now, run, event, wait, process, schedule, urgent_event, anyof,
    )),
    ('Types', (
        Int, Bit, Reg, Real, BitVector, RegVector, String, Struct, Event,
    )),
)

# Use the toc to keep the documentation and the implementation in sync.
if __doc__:
    __doc__ = __doc__.format(toc=compile_toc(toc))

__path__ = pkgutil.extend_path(__path__, __name__)
__version__ = '1.0.0'
