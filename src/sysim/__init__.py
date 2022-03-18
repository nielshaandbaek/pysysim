"""
The ``sysim`` module aggregates PySySim's most used components into a single
namespace. This is purely for convenience. You can of course also access
everything (and more!) via their actual submodules.

The following tables list all of the available components in this module.

{toc}
"""
from pkgutil import extend_path

from sysim.logging import (
    VcdLogger,
)
from sysim.types import (
    TypeBase, Struct, Bit, Reg, Int, Real, BitVector, RegVector, String,
)
from sysim.core import (
    initialize, now, run, event, urgent_event, wait, schedule, anyof
)
from sysim.signal import signal, input, output, inout
from sysim.module import Module, process

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
            toc += f'    ~{obj.__module__}.{obj.__name__}\n'
    return toc

toc = (
    ('Simulation', (
        signal, input, output, inout, Module, VcdLogger,
    )),
    ('Functions', (
        initialize, now, run, event, wait, process, schedule, urgent_event, anyof
    )),
)

# Use the toc to keep the documentation and the implementation in sync.
if __doc__:
    __doc__ = __doc__.format(toc=compile_toc(toc))
__all__ = [obj.__name__ for section, objs in toc for obj in objs]

__path__ = extend_path(__path__, __name__)
__version__ = '1.0.0'
