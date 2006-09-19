# Yet another gmail tray icon notifier
# Miki Tebeka <miki.tebeka@gmail.com>

from sys import path
from os.path import isfile, dirname, join
from poplib import POP3_SSL
from itertools import count
import webbrowser
import wx
from dotdict import DotDict
from threading import Lock
import gc
try:
    from version import VERSION
except ImportError:
    VERSION = "???"

# We keep UIDL of message in sqlite DB
try: # Python 2.5+ version
    from sqlite3 import connect, Error as DBError
except ImportError: # Older Python version
    from pysqlite2.dbapi2 import connect, Error as DBError

# Application directory
APPDIR = path[0]
if isfile(APPDIR): # py2exe
    APPDIR = dirname(APPDIR)

# Icons to use
ICON_NO_MAIL = "no_mail.ico"
ICON_NEW_MAIL = "new_mail.ico"
ICON_ERROR = "error.ico"

# No email tooltip
TIP_NO_MAIL = "No new mail"

DB_FILE = join(APPDIR, "messages.db")
DB = None

# Configuration file is Python syntax
# FIXME: Encrypt password
CONFIG_FILE = join(APPDIR, "gmailtray.ini")
DEFAULT_CONFIG =  DotDict({
    "login" : "",
    "password" : "",
    "web_page" : "http://gmail.google.com",
})

def load_config():
    if not isfile(CONFIG_FILE):
        return DEFAULT_CONFIG

    config = DotDict()
    execfile(CONFIG_FILE, globals(), config)
    return config

def save_config(config):
    fo = open(CONFIG_FILE, "wt")
    for key, value in config.iteritems():
        if isinstance(value, basestring):
            value = "r\"%s\"" % value
        print >> fo, "%s = %s" % (key, value)
    fo.close()

def run_config():
    config = load_config()
    dlg = ConfigDlg(config)
    if dlg.ShowModal() == wx.ID_OK:
        config = dlg.get_config()
        try:
            save_config(config)
        except DBError:
            wx.LogError("Error saving configuration")
    dlg.Destroy()

def initialize():
    cur = cursor()
    try:
        cur.execute("create table messages (id string)")
    except DBError:
        # FIXME: Should we ignore this?
        pass
    cur.connection.commit()
    cur.close()
    run_config()

def cursor():
    return DB.cursor()

def is_message_new(message_id):
    cur = cursor()
    try:
        cur.execute("select count(*) from messages where id = ?", 
                (message_id, ))
        count, = cur.fetchone()
        return count == 0
    finally:
        cur.close()

def get_message_id_list(user, password):
    pop = POP3_SSL("pop.gmail.com")
    message_id_list = []
    try:
        pop.user(user)
        pop.pass_(password)

        num_messages, size = pop.stat()
        for id in count(1):
            if id > num_messages:
                break
            id_line = pop.uidl(id)
            message_id_list.append(id_line.split()[-1])

        return message_id_list
    finally:
        pop.quit()

def save_messages(message_id_list):
    cur = cursor()
    try:
        for id in message_id_list:
            cur.execute("insert into messages (id) values (?)", (id, ))
    finally:
        cur.close()
        cur.connection.commit()

def get_new_message_ids(config):
    new_message_id_list = []
    for message_id in get_message_id_list(config.login, config.password):
        if is_message_new(message_id):
            new_message_id_list.append(message_id)

    return new_message_id_list

def load_icon(name):
    iconfile = join(APPDIR, name)
    if not isfile(iconfile):
        raise IOError

    return wx.Icon(iconfile, wx.BITMAP_TYPE_ICO)

# Email:    ______________
# Password: ______________
# --------------
# [Save] [Quit]
class ConfigDlg(wx.Dialog):
    def __init__(self, config):
        wx.Dialog.__init__(self, None, -1, "GmailTray Configuration")
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Email:    ______________
        # Password: ______________
        gsizer = wx.FlexGridSizer(4, 2) # Rows, cols
        def add(name, value, style=0):
            gsizer.Add(wx.StaticText(self, -1, "%s:" % name), 0,
                wx.ALIGN_CENTER_VERTICAL)
            text = wx.TextCtrl(self, -1, value=value, size=(300, -1),
                    style=style)
            gsizer.Add(text, 0, wx.EXPAND)
            return text

        self._login = add("Email", config["login"])
        self._password = add("Password", config["password"], wx.TE_PASSWORD)
        self._url = add("Web Page:", config["web_page"])

        sizer.Add(gsizer, 1, wx.EXPAND|wx.WEST, 2)

        # --------------
        sl = wx.StaticLine(self, -1, style=wx.LI_HORIZONTAL, size=(-1, 2))
        sizer.Add(sl, 0, wx.EXPAND|wx.NORTH|wx.SOUTH|wx.EAST|wx.WEST, 5)

        # [Save] [Quit]
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(wx.Button(self, wx.ID_OK))
        hsizer.Add(wx.Button(self, wx.ID_CANCEL))
        sizer.Add(hsizer, 0, wx.EXPAND)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def get_config(self):
        def _get(control):
            return control.GetValue().strip()

        return {
            "login" : _get(self._login),
            "password" : _get(self._password),
            "web_page" : _get(self._url),
        }

class GmailTray(wx.TaskBarIcon):
    TBMENU_REFRESH = wx.NewId()
    TBMENU_CLOSE = wx.NewId()
    TBMENU_VIEW = wx.NewId()
    TBMENU_CONFIG = wx.NewId()

    def __init__(self):
        wx.TaskBarIcon.__init__(self)
        self.set_icon(ICON_ERROR, "Connecting ...")
        self.num_new_messages = 0
        self.lock = Lock()

        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.timer = wx.Timer(self) 
        # wx.Timer gets milliseconds, we want 5 minutes
        self.timer.Start(1000 * 60 * 5)
        self.check_status()

        def handle_menu(id, handler):
            self.Bind(wx.EVT_MENU, handler, id=id)
        handle_menu(self.TBMENU_REFRESH, self.OnRefresh)
        handle_menu(self.TBMENU_CLOSE, self.OnClose)
        handle_menu(self.TBMENU_VIEW, self.OnView)
        handle_menu(self.TBMENU_CONFIG, self.OnConfig)
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.OnView)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def check_status(self):
        # Non blocking lock
        if not self.lock.acquire(0):
            return

        try:
            new_message_ids = get_new_message_ids(load_config())
            if new_message_ids:
                save_messages(new_message_ids)
                self.num_new_messages += len(new_message_ids)
                icon = ICON_NEW_MAIL
                tooltip = "%d new email(s)" % self.num_new_messages
            else:
                icon = ICON_NO_MAIL
                tooltip = TIP_NO_MAIL
        except Exception: # FIXME: Catch more specific errors
            icon = ICON_ERROR
            tooltip = "Connection error"
        finally:
            self.lock.release()

        self.set_icon(icon, tooltip)

    def OnRefresh(self, evt):
        self.check_status()

    def OnClose(self, evt):
        self.RemoveIcon()
        raise SystemExit

    def OnView(self, evt):
        self.num_new_messages = 0
        self.set_icon(ICON_NO_MAIL, TIP_NO_MAIL)
        webbrowser.open("http://gmail.google.com")

    def CreatePopupMenu(self):
        menu = wx.Menu()
        menu.Append(self.TBMENU_REFRESH, "Check now")
        menu.Append(self.TBMENU_VIEW, "View web page")
        menu.Append(self.TBMENU_CONFIG, "Configure ...")
        menu.AppendSeparator()
        menu.Append(self.TBMENU_CLOSE, "Exit")

        return menu

    def OnTimer(self, evt):
        self.check_status()
        gc.collect()

    def OnConfig(self, evt):
        run_config()

    def set_icon(self, icon_file, message):
        icon = load_icon(icon_file)
        tooltip = "[GmailTray] %s" % message
        self.SetIcon(icon, tooltip)

def main(argv=None):
    global DB

    if argv is None:
        import sys
        argv = sys.argv

    from optparse import OptionParser
    parser = OptionParser("usage: %prog [options]",
            version="GmailTray version %s" % VERSION)
    parser.add_option("--initialize", dest="initialize", default=0,
        action="store_true")

    opts, args = parser.parse_args(argv[1:])
    if args:
        parser.error("wrong number of arguments") # Will exit

    # This must be first
    app = wx.PySimpleApp()
    DB = connect(DB_FILE)

    if opts.initialize:
        try:
            initialize()
        except Exception, e:
            wx.LogError("%s" % e)
            raise SystemExit
        raise SystemExit

    gm = GmailTray()
    app.MainLoop()

if __name__ == "__main__":
    main()
