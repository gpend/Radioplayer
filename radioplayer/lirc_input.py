import select
from gi.repository import GLib, Gio, GObject

try:
    import pylirc
except ImportError:
    pylirc = None

GObject.threads_init()

class InputProvider:

    def __init__(self, config, notifier):
        if not pylirc:
            return

        self.notifier = notifier
        rc_file = config.get("lirc", "keymap")
        self.socket = pylirc.init('radioplayer', rc_file)

    def _do_poll(self, job, cancellable, p):
        result = p.poll()
        for fd, event in result:
            if event == select.POLLIN:
                code = pylirc.nextcode()
                if code:
                    self.notifier.handle_input(code[0])
        Gio.io_scheduler_push_job(self._do_poll, p, GLib.PRIORITY_DEFAULT, None)

    def start(self):
        if not pylirc:
            return
        p = select.poll()
        p.register(self.socket, select.POLLIN | select.POLLERR | select.POLLHUP | select.POLLNVAL)

        Gio.io_scheduler_push_job(self._do_poll, p, GLib.PRIORITY_DEFAULT, None)