"""Settings module.

The settings may be overwritten by the *settings_local* module.
"""
# pylint: disable=wildcard-import,unused-wildcard-import
try:
    from vwkommi.settings_local import *
except ImportError:
    from vwkommi.settings_default import *
