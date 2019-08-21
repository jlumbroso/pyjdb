"""
Python package to interface with the standard CLI Java Debugger `jdb` to
extract information about the execution of Java programs.
"""
from pexpect import EOF

from .jdb_process import JdbProcess
