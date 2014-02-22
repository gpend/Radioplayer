
# http://pythonhosted.org/gntp/
import gntp.notifier

import uuid

class Notification:

    def __init__(self, app_name, config, closed_cb=None):
        self.app_name = app_name
        self.config = config
        self.actions = []
        self.summary = ""
        self.body = ""
        self.icon_name = ""
        self.id = uuid.uuid4().urn
        self.noteType = "Now playing"
        hostname = config.get("growl", "hostname")
        self.growl = gntp.notifier.GrowlNotifier(app_name, hostname=hostname,
                                                 password=config.get("growl", "password"),
                                                 notifications=[self.noteType,])
        try:
            self.growl.register()
        except Exception, exc:
            print "Failed to connect to Growl service at %s: %s" % (hostname, str(exc))

    def show(self):
        self.growl.notify(noteType=self.noteType, title=self.summary, description=self.body,
                          identifier=self.id, sticky=True)

    def close(self):
        pass

    def update(self, summary, body):
        self.summary = summary.encode("utf-8")
        self.body = body.encode("utf-8")

    def add_action(self, name, label, callback):
        pass

    def clear_actions(self):
        pass
