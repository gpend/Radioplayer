
import gobject
import dbus
import dbus.exceptions

class DBusException(Exception):
    pass

class UnknownServiceException(DBusException):
    pass

def exception_from_dbus_exception(exc):
    mapping = {"org.freedesktop.DBus.Error.ServiceUnknown": UnknownServiceException}
    try:
        return mapping[exc._dbus_error_name](*exc.args)
    except KeyError:
        print "Unknown exception: %r" % exc._dbus_error_name
        return exc

class ImProxy:
    saved_status = ""
    service_name = ""
    object_path = ""
    interface_name = ""

    def __init__(self, bus):
        try:
            remote_object = bus.get_object(self.service_name, self.object_path)
        except dbus.exceptions.DBusException, exc:
            raise exception_from_dbus_exception(exc)

        self.interface = dbus.Interface(remote_object, self.interface_name)

    def _call_method(self, name, *args):
        func = getattr(self.interface, name)
        result = func(*args)
        return result

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
        return self._call_method("PurpleSavedstatusGetCurrent")

    def get_status(self):
        return self._call_method("PurpleSavedstatusGetMessage",
                                 self._get_current())

    def set_status(self, message):
        current = self._get_current()
        self._call_method("PurpleSavedstatusSetMessage", current, message)
        self._call_method("PurpleSavedstatusActivate", current)

class TelepathyProxy(ImProxy):
    service_name = "org.freedesktop.Telepathy.MissionControl"
    object_path = "/org/freedesktop/Telepathy/MissionControl"
    interface_name = "org.freedesktop.Telepathy.MissionControl"

    def get_status(self):
        return self._call_method("GetPresenceMessage")

    def set_status(self, message):
        try:
            presence = self._call_method("GetPresence")
        except dbus.exceptions.DBusException, exc:
            raise exception_from_dbus_exception(exc)
        self._call_method("SetPresence", presence, message)

class GajimProxy(ImProxy):
    service_name = "org.gajim.dbus"
    object_path = "/org/gajim/dbus/RemoteObject"
    interface_name = "org.gajim.dbus.RemoteInterface"

    def get_status(self):
        return self._call_method("get_status_message", "")

    def set_status(self, message):
        accounts = self._call_method("list_accounts")
        for account in accounts:
            account_infos = self._call_method("account_info", account)
            if account_infos["status"] != u'offline':
                self._call_method("change_status", account_infos["status"],
                                  message, account)


class ImStatusManager:
    im_proxy_classes = dict([(p.service_name, p) for p in
                             [PidginProxy, TelepathyProxy, GajimProxy]])

    def __init__(self, bus):
        self._timeout = None
        self._bus = bus
        self.im_proxies = {}

        self._load_all_proxies()

        dbus_obj = self._bus.get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        dbus_obj.connect_to_signal('NameOwnerChanged', self._name_owner_changed_cb)

    def _load_all_proxies(self):
        for service_name, klass in self.im_proxy_classes.iteritems():
            try:
                proxy = klass(self._bus)
            except UnknownServiceException, exc:
                print "Error creating proxy: %r" % exc
                continue
            self.im_proxies[service_name] = proxy

    def _name_owner_changed_cb(self, service, old, new):
        if old:
            # service disappeared
            if service in self.im_proxies:
                del self.im_proxies[service]
        else:
            # service appeared
            klass = self.im_proxy_classes.get(service)
            if klass:
                proxy = klass(self._bus)
                proxy.save_status()
                self.im_proxies[service] = proxy

    def _call_proxy_method(self, name, *args):
        for proxy in self.im_proxies.values():
            try:
                getattr(proxy, name)(*args)
            except Exception, exc:
                print "Error while calling method %r on %r: %r" % (name, proxy,
                                                                   proxy.interface_name)

    def save_status(self):
        self._call_proxy_method("save_status")

    def restore_status(self):
        self._call_proxy_method("restore_status")

    def set_status(self, message):
        self._call_proxy_method("set_status", message)

    def get_status(self):
        self._call_proxy_method("get_status")

    def set_status_async(self, message):
        if self._timeout:
            gobject.source_remove(self._timeout)
        self._timeout = gobject.timeout_add(0, self._set_status_now,
                                            message)
    def _set_status_now(self, message):
        self.set_status(message)
        self._timeout = None
        return False

if __name__ == "__main__":
    import sys

    message = sys.argv[-1]
    bus = dbus.SessionBus()
    manager = ImStatusManager(bus)
    print "saved state: ", manager.save_status()
    print "current: ", manager.get_status()
    manager.set_status(message)
    print "new: ", manager.get_status()
