#!/usr/bin/env python
'''Print list of source files'''

# Miki Tebeka <miki.tebeka@gmail.com>

from os import listdir, popen
from os.path import isfile

pipe =  popen("svn --help > /dev/null 2>&1")
pipe.read()
if pipe.close():
    raise SystemExit("error: can't find 'svn' in path")

for filename in listdir("."):
    svnout = popen("svn st %s" % filename).read().strip()
    if not svnout:
        print filename
    elif svnout.split()[0] in ("M", "A"):
        print filename
