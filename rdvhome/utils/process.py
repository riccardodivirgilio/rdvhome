# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from functools import partial

from rdvhome.utils.functional import iterate

import os
import subprocess

process = partial(
    subprocess.Popen,
    stdout = subprocess.PIPE,
    stdin  = subprocess.PIPE,
    stderr = subprocess.STDOUT
)

def _auto_expand(path):
    if path.startswith("~"):
        return os.path.realpath(os.path.expanduser(path))
    return path

def system_open(path, cmd = "open"):
    return process(tuple(iterate((cmd, ), map(_auto_expand, iterate(path)))))