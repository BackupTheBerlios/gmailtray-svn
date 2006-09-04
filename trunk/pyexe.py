#!/usr/bin/env python

from sys import platform, executable
from os import popen

if platform == "win32":
    print executable
    raise SystemExit

# If we're here it's cygwin
PY_BASE = "/HKLM/Software/Python/PythonCore"

versions = []
for line in popen("/bin/regtool list %s" % PY_BASE):
    versions.append(line.strip())

if not versions:
    raise SystemExit("error: can't find Python in the registry")

versions.sort(lambda v1, v2: cmp(float(v1), float(v2)))
ver = versions[-1]

path = popen("/bin/regtool get '%s/%s/InstallPath/'" % \
        (PY_BASE, ver)).read().strip()
path += "python.exe"
path = path.replace("\\", "\\\\")

print popen("cygpath -au '%s'" % path).read().strip()
