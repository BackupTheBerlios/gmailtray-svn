from distutils.core import setup
import py2exe

setup(
    windows = [{
            "script": "gmailtray.py",
            "icon_resources": [(1, "no_mail.ico")]
        }]
)
