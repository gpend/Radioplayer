
from gi.repository import GLib, Gio
from gi._glib import GError

class DBusException(Exception):
    pass

class UnknownServiceException(DBusException):
    pass

class ImProxy:
    saved_status = ""
    service_name = ""
    object_path = ""
    interface_name = ""

    def __init__(self, bus):
        self.remote_object = Gio.DBusProxy.new_sync(bus, 0, None, self.service_name, self.object_path, self.interface_name, None)
        if not self.remote_object.get_name_owner():
            raise UnknownServiceException()

    def _call_method(self, name, signature, *args):
        # TODO: somehow get method signature from introspection data.
        variant_args = GLib.Variant(signature, args)
        return self.remote_object.call_sync(name, variant_args, 0, -1, None)

    def save_status(self):
        self.saved_status = self.get_status()
        return self.saved_status

    def restore_status(self):
        self.set_status(self.saved_status)

    def get_status(self):
        pass

    def set_status(self, message):
        pass

class PidginProxy(ImProxy):
    service_name = "im.pidgin.purple.PurpleService"
    object_path = "/im/pidgin/purple/PurpleObject"
    interface_name = "im.pidgin.purple.PurpleInterface"

    def _get_current(self):
        return self._call_method("PurpleSavedstatusGetCurrent", "()")

    def get_status(self):
        return self._call_method("PurpleSavedstatusGetMessage", "(s)",
                                 self._get_current())

    def set_status(self, message):
        current = self._get_current()
        self._call_method("PurpleSavedstatusSetMessage", "(ss)", current, message)
        self._call_method("PurpleSavedstatusActivate", "(s)", current)

class TelepathyProxy(ImProxy):
    service_name = "org.freedesktop.Telepathy.MissionControl5"
    object_path = "/org/freedesktop/Telepathy/AccountManager"
    interface_name = "org.freedesktop.DBus.Properties"
    am_iface_name = "org.freedesktop.Telepathy.AccountManager"
    account_iface_name = "org.freedesktop.Telepathy.Account"

    def get_status(self):
        for acct_obj_path in self.remote_object.Get("(ss)", self.am_iface_name, 'ValidAccounts'):
            acct_proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, 0, None,
                                                        self.service_name, acct_obj_path,
                                                        self.interface_name, None)
            ret = acct_proxy.Get("(ss)", self.account_iface_name, "RequestedPresence")
            if ret[2] != "":
                return ret[2]
        return ""

    def set_status(self, message):
        for acct_obj_path in self.remote_object.Get("(ss)", self.am_iface_name, 'ValidAccounts'):
            acct_proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION, 0, None,
                                                        self.service_name, acct_obj_path,
                                                        self.interface_name, None)
            status = acct_proxy.Get("(ss)", self.account_iface_name, "RequestedPresence")
            vstatus = GLib.Variant("(uss)", (status[0], status[1], message))
            acct_proxy.Set("(ssv)", self.account_iface_name, "RequestedPresence", vstatus)

class GajimProxy(ImProxy):
    service_name = "org.gajim.dbus"
    object_path = "/org/gajim/dbus/RemoteObject"
    interface_name = "org.gajim.dbus.RemoteInterface"

    def get_status(self):
        try:
            val = self._call_method("get_status_message", "(s)", "").get_child_value(0)
        except:
            return ""
        return val.dup_string()[0]

    def set_status(self, message):
        accounts = self._call_method("list_accounts", "()").get_child_value(0)
        for account in accounts:
            account_infos = self._call_method("account_info", "(s)", account).get_child_value(0)
            if account_infos["status"] != u'offline':
                try:
                    self._call_method("change_status", "(sss)", account_infos["status"],
                                      message, account)
                except Exception, exc:
                    print exc


class ImStatusManager:
    ProxyTypes = [PidginProxy, TelepathyProxy, GajimProxy]
    im_proxy_classes = dict([(p.service_name, p) for p in
                             ProxyTypes])

    def __init__(self, bus):
        self._timeout = None
        self._bus = bus
        self.im_proxies = {}

        self._load_all_proxies()

        for t in self.ProxyTypes:
            Gio.bus_watch_name(Gio.BusType.SESSION, t.service_name,
                               Gio.BusNameWatcherFlags.NONE, self._on_name_appeared, self._on_name_vanished)


    def _load_all_proxies(self):
        for service_name, klass in self.im_proxy_classes.iteritems():
            try:
                proxy = klass(self._bus)
            except UnknownServiceException, exc:
                print "Unknown d-bus service: %s" % service_name
                continue
            self.im_proxies[service_name] = proxy

    def _on_name_appeared(self, connection, service, *data):
        klass = self.im_proxy_classes.get(service)
        if klass:
            proxy = klass(self._bus)
            proxy.save_status()
            self.im_proxies[service] = proxy

    def _on_name_vanished(self, connection, service, *data):
        if service in self.im_proxies:
            del self.im_proxies[service]

    def _call_proxy_method(self, name, *args):
        results = []
        for proxy in self.im_proxies.values():
            results.append(getattr(proxy, name)(*args))
        return results

    def save_status(self):
        return self._call_proxy_method("save_status")

    def restore_status(self):
        self._call_proxy_method("restore_status")

    def set_status(self, message):
        self._call_proxy_method("set_status", message)

    def get_status(self):
        return self._call_proxy_method("get_status")

    def set_status_async(self, message):
        if self._timeout:
            GLib.source_remove(self._timeout)
        self._timeout = GLib.timeout_add(0, self._set_status_now,
                                            message)
    def _set_status_now(self, message):
        self.set_status(message)
        self._timeout = None
        return False

if __name__ == "__main__":
    import sys

    message = sys.argv[-1]
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    manager = ImStatusManager(bus)
    print "saved state: ", manager.save_status()
    print "current: ", manager.get_status()
    manager.set_status(message)
    print "new: ", manager.get_status()
