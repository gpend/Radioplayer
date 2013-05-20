import select
from gi.repository import GLib

try:
    import pylirc
except ImportError:
    pylirc = None

class InputProvider:

    def __init__(self, config, notifier):
        if not pylirc:
            return

        self.notifier = notifier
        rc_file = config.get("lirc", "keymap")
        self.socket = pylirc.init('radioplayer', rc_file)

    def _do_poll(self, p):
        result = p.poll()
        for fd, event in result:
            if event == select.POLLIN:
                code = pylirc.nextcode()
                if code:
                    self.notifier.handle_input(code[0])
        return True

    def start(self):
        if not pylirc:
            return
        p = select.poll()
        p.register(self.socket, select.POLLIN | select.POLLERR | select.POLLHUP | select.POLLNVAL)

        self.poll_source = GLib.idle_add(self._do_poll, p)
