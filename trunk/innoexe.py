#!/usr/bin/env python
'''Find InnoSetup executable'''

# Miki Tebeka <miki.tebeka@gmail.com>

from sys import platform

UNINST = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
ISCC = "ISCC.exe"
INNO = "Inno Setup"
NOT_FOUND = "error: can't find Inno Setup registery key"
LOCK_KEY = "InstallLocation"

if platform == "win32": 
    from _winreg import OpenKey, QueryValueEx, EnumKey, CloseKey, \
            HKEY_LOCAL_MACHINE 
    from itertools import count
    from os.path import join


    key = OpenKey(HKEY_LOCAL_MACHINE, UNINST)
    next = count(0).next

    # Find unistall key
    while 1:
        try:
            keyname = EnumKey(key, next())
            if INNO in keyname:
                break
        except WindowsError: # Passed last one
            raise SystemExit(NOT_FOUND)

    CloseKey(key)
    key = OpenKey(HKEY_LOCAL_MACHINE, UNINST + "\\" + keyname)
    # Get install directory
    value, type = QueryValueEx(key, LOCK_KEY)
    CloseKey(key)

    # Print full path to compiler
    print join(value, ISCC)

    raise SystemExit

# Cygwin starts here
from os import popen
UNINST = UNINST.replace("\\", "/")
for line in popen("/bin/regtool list /HKLM/%s" % UNINST):
    if INNO in line:
        break
else:
    raise SystemExit(NOT_FOUND)
keyname = line.strip()
path = popen("/bin/regtool get '/HKLM/%s/%s/%s'" % \
        (UNINST, keyname, LOCK_KEY)).read().strip()
path += ISCC
print popen("/bin/cygpath -au '%s'" % path).read().strip()
