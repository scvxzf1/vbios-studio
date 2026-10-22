"""Pure domain layer for VBIOS Studio.

The domain package contains immutable data-transfer objects, risk levels,
structured errors, the ROM structure/checksum model, the field catalog mapper
and the edit manifest builder. It must not import GTK, adapters, ports, the UI,
the application layer, subprocess or platform-specific modules; see
``docs/architecture.md`` and the ``domain-pure`` import-linter contract.
"""
