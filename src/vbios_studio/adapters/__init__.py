"""Adapter layer: upstream bridge and system integrations.

Adapters implement the Protocols declared in ``vbios_studio.ports``. They may
depend on the pure domain and, for the upstream bridge, on the vendored
``nvidia_vbios`` package. They must not import the UI or the application
layer; see ``docs/architecture.md``.
"""
