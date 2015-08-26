
from gi.repository import GLib, Gio

class Notification:

    def __init__(self, app_name, closed_cb=None):
        self.app_name = app_name
        self.summary = ""
        self.body = ""
        self.actions = []
        self._actions = {}
        self.icon_name = ""
        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        service_name = "org.freedesktop.Notifications"
        object_path = "/org/freedesktop/Notifications"
        interface_name = "org.freedesktop.Notifications"
        self.remote_object = Gio.DBusProxy.new_sync(self.bus, 0, None, service_name, object_path, interface_name, None)
        self.id = -1

        def on_signal(proxy, sender_name, signal_name, parameters):
            params = tuple(parameters)
            if params[0] != self.id:
                return
            if signal_name == "NotificationClosed":
                if closed_cb:
                    closed_cb(*params[1:])
            elif signal_name == "ActionInvoked":
                callback = self._actions[params[1]]
                callback(self, params[1])

        self.remote_object.connect("g-signal", on_signal)

    def show(self):
        if self.id < 0:
            replaces_id = 0
        else:
            replaces_id = self.id
        self.hints = {"transient": GLib.Variant("b", True)}
        expire_timeout = 5000
        args = (self.app_name, replaces_id, self.icon_name, self.summary, self.body,
                self.actions, self.hints, expire_timeout)
        variant_args = GLib.Variant("(susssasa{sv}i)", args)
        result  = self.remote_object.call_sync("Notify", variant_args, 0, -1, None)
        self.id = result[0]

    def close(self):
        variant_args = GLib.Variant("(u)", (self.id,))
        result  = self.remote_object.call_sync("CloseNotification", variant_args, 0, -1, None)

    def update(self, summary, body):
        self.summary = summary
        self.body = body

    def add_action(self, name, label, callback):
        self._actions[name] = callback
        self.actions.extend([name, label])

    def clear_actions(self):
        self.actions = []
        self._actions = {}

if __name__ == "__main__":
    import sys

    loop = GLib.MainLoop()

    def closed_cb(reason):
        print reason
        loop.quit()

    def close(notification):
        notification.close()

    def resume_action_cb(notification, action):
        print "resume"

    notification = Notification("foo", closed_cb)
    notification.update("FOO", "BAR")
    notification.add_action("resume", "Resume playback", resume_action_cb)
    notification.icon_name = "media-playback-stop-symbolic"
    notification.show()
    GLib.timeout_add_seconds(20, close, notification)
    loop.run()
