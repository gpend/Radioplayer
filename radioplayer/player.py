
import pygst
pygst.require('0.10')
import gst
import dbus

class Player:

    def __init__(self, url, audiosink="autoaudiosink", output_location=None,
                 paused_or_stopped_cb=None):
        self._paused_or_stopped_cb = paused_or_stopped_cb
        self._app_name = "radioplayer"

        bus = dbus.SessionBus()
        remote_object = bus.get_object("org.gnome.SettingsDaemon", "/org/gnome/SettingsDaemon/MediaKeys")
        self.proxy = dbus.Interface(remote_object, "org.gnome.SettingsDaemon.MediaKeys")

        self.proxy.GrabMediaPlayerKeys(self._app_name, 0)

        bus.add_signal_receiver(self._key_pressed, signal_name="MediaPlayerKeyPressed",
                                dbus_interface="org.gnome.SettingsDaemon.MediaKeys")
        if not output_location:
            self.pipeline = gst.element_factory_make("playbin2")
            self.pipeline.props.uri = url
            if audiosink != "autoaudiosink":
                self.pipeline.props.audio_sink = gst.element_factory_make(audiosink)
        else:
            self.pipeline = gst.parse_launch("souphttpsrc location=%s "
                                             "! tee name=t queue t. ! decodebin2 "
                                             "! %s t. ! queue "
                                             "! filesink location=%s" % (url,
                                                                         audiosink,
                                                                         output_location))
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_gst_message)
        # TODO: send state notifications using signals

    def _on_gst_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            print "Restarting..."
            self.stop()
            self.start()

    def _key_pressed(self, app, key):
        if app != self._app_name:
            return
        if key == dbus.String(u"Play"):
            self.toggle_play()
        elif key == dbus.String(u"Stop"):
            self.stop()

    def ping_gnome(self):
        self.proxy.GrabMediaPlayerKeys(self._app_name, 0)

    def start(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

    def stop(self, *args, **kwargs):
        notify = kwargs.get("notify", True)
        self.pipeline.set_state(gst.STATE_NULL)
        if notify and self._paused_or_stopped_cb:
            self._paused_or_stopped_cb()

    def toggle_play(self):
        result, state, pending = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            new_state = gst.STATE_PAUSED
            if self._paused_or_stopped_cb:
                self._paused_or_stopped_cb()
        else:
            new_state = gst.STATE_PLAYING
        self.pipeline.set_state(new_state)
