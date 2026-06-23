from importlib import import_module
import sys


def alias_module(local_name, core_name):
    module = import_module(core_name)
    sys.modules[local_name] = module
    return module


def alias_submodules(local_package, core_package, names):
    for name in names:
        alias_module(f"{local_package}.{name}", f"{core_package}.{name}")
