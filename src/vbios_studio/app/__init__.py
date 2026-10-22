"""Application layer: composition root and command-line entry points.

The application may depend on every other package. It wires concrete adapters
into ports and decides which UI or CLI front end runs. Keeping this logic out
of the UI means adapters can be replaced in tests without touching GTK.
"""
