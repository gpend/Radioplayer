
from gi.repository import Gst, Gio, GLib

class Player:

    def __init__(self, url, audiosink="autoaudiosink", output_location=None,
                 paused_or_stopped_cb=None):
        self._paused_or_stopped_cb = paused_or_stopped_cb
        self._app_name = "radioplayer"

        Gst.init([])

        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.proxy = Gio.DBusProxy.new_sync(bus, 0, None, "org.gnome.SettingsDaemon",
                                            "/org/gnome/SettingsDaemon/MediaKeys",
                                            "org.gnome.SettingsDaemon.MediaKeys", None)

        self.ping_gnome()

        def on_signal(proxy, sender_name, signal_name, parameters):
            if signal_name == "MediaPlayerKeyPressed":
                self._key_pressed(*parameters)

        self.proxy.connect("g-signal", on_signal)

        if not output_location:
            self.pipeline = Gst.ElementFactory.make("playbin2", "playbin")
            self.pipeline.props.uri = url
            if audiosink != "autoaudiosink":
                self.pipeline.props.audio_sink = Gst.ElementFactory.make(audiosink, "audiosink")
        else:
            self.pipeline = Gst.parse_launch("souphttpsrc location=%s "
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
        if not message:
            return
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            print "Restarting..."
            self.stop()
            self.start()

    def _key_pressed(self, app, key):
        if app != self._app_name:
            return
        if key == "Play":
            self.toggle_play()
        elif key == "Stop":
            self.stop()

    def ping_gnome(self):
        variant_args = GLib.Variant("(su)", (self._app_name, 0))
        result  = self.proxy.call_sync("GrabMediaPlayerKeys", variant_args, 0, -1, None)

    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self, *args, **kwargs):
        notify = kwargs.get("notify", True)
        self.pipeline.set_state(Gst.State.NULL)
        if notify and self._paused_or_stopped_cb:
            self._paused_or_stopped_cb()

    def toggle_play(self):
        result, state, pending = self.pipeline.get_state(0)
        if state == Gst.State.PLAYING:
            new_state = Gst.State.PAUSED
            if self._paused_or_stopped_cb:
                self._paused_or_stopped_cb()
        else:
            new_state = Gst.State.PLAYING
        self.pipeline.set_state(new_state)
