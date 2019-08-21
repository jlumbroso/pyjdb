"""
pyjdb

Python package to interface with the standard CLI Java Debugger `jdb` to
extract information about the execution of Java programs.

   Name: pyjdb
 Author: Jérémie Lumbroso
  Email: lumbroso@cs.princeton.edu
    URL: github.com/codepost-io/codepost-python
License: Copyright (c) 2019 Jérémie Lumbroso, under LGPL3 license
"""
# Documentation
from codepost.version import __version__
from pexpect import EOF

from .jdb_process import JdbProcess
