"""System adapters: Windows registry override, Linux loader and nvflash guard.

Every module in this subpackage must keep subprocess calls behind the ports
abstraction, pass argument lists and use ``shell=False``. The nvflash guard is
the only place allowed to name the nvflash executable and must reject any
modified image before launching a process.
"""
