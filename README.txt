iRacing Python API client
=========================

Will build this as I learn how it works as there's no worked Python example.

Description
-----------

Uses memory-mapped files, has slow-updating YAML data and fast (60Hz) updating
telemetry data.

API
---

This file api.py provides read-only access to the iRacing memory mapped file
session and telemetry API.

To get all meta, the api.py has an API of it's own. It's a very simple dict
interface:

    api.API()[KEY]

And there's a dict-like .keys() helper:

    api.API().keys()

I'll do my best to support this as a minimum, going forward, but I'm hoping to
add more clevers as well of course.

Tests
-----

Run using:
    python runtests.py

Benchmarking
------------

To check telemetry read performance on your machine, run:
    python benchmark.py

Requires
--------

Python 2.7, PyYAML