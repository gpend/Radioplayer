import gi

try:
    gi.require_version('Gst', '1.0')
except:
    gi.require_version('Gst', '0.10')
    PLAYBIN = "playbin2"
    DECODEBIN = "decodebin2"
else:
    PLAYBIN = "playbin"
    DECODEBIN = "decodebin"

from gi.repository import Gst, Gio, GLib, GObject

class Player(GObject.GObject):
    __gsignals__ = { 'suspended': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ()),
                     'resumed': (GObject.SIGNAL_RUN_FIRST, GObject.TYPE_NONE, ())
    }

    def __init__(self, url, audiosink="autoaudiosink", output_location=None, headless=False):
        super(Player, self).__init__()
        GObject.threads_init()
        self._app_name = "radioplayer"
        self._notify = False
        self._url = url
        self._audiosink = audiosink
        self._output_location = output_location
        self._headless = headless

        Gst.init([])
        self._configure_pipeline()

        if headless:
            return

        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.proxy = Gio.DBusProxy.new_sync(bus, 0, None, "org.gnome.SettingsDaemon",
                                            "/org/gnome/SettingsDaemon/MediaKeys",
                                            "org.gnome.SettingsDaemon.MediaKeys", None)

        self.ping_gnome()

        def on_signal(proxy, sender_name, signal_name, parameters):
            if signal_name == "MediaPlayerKeyPressed":
                self._key_pressed(*parameters)

        self.proxy.connect("g-signal", on_signal)

    def _configure_pipeline(self):
        if not self._output_location:
            self.pipeline = Gst.ElementFactory.make(PLAYBIN, "playbin")
            self.pipeline.props.uri = self._url
            self.pipeline.props.audio_sink = Gst.ElementFactory.make(self._audiosink, "audiosink")
        else:
            self.pipeline = Gst.parse_launch("souphttpsrc name=src location=%s "
                                             "! tee name=t queue t. ! %s "
                                             "! %s name=audiosink t. ! queue "
                                             "! filesink location=%s" % (self._url, DECODEBIN,
                                                                         self._audiosink,
                                                                         self._output_location))
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_gst_message)

    def set_url(self, url):
        self._url = url
        self.pipeline.set_state(Gst.State.NULL)
        if not self._output_location:
            self.pipeline.props.uri = self._url
        else:
            src = self.pipeline.get_child_by_name("src")
            src.props.location = self._url

        self.start()

    def update_volume(self, delta):
        value = self.pipeline.props.volume + delta
        # Clamp between 0 and 1.
        self.pipeline.props.volume = max(min(value, 1.), 0.)

    def increment_volume(self):
        self.update_volume(0.05)

    def decrement_volume(self):
        self.update_volume(float(-0.05))

    def toggle_mute(self):
        self.pipeline.props.mute = not self.pipeline.props.mute

    def do_suspended(self):
        pass

    def do_resumed(self):
        pass

    def _on_gst_message(self, bus, message):
        if not message:
            return
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            print "Restarting..."
            self.pipeline.set_state(Gst.State.NULL)
            self.pipeline = None
            self._configure_pipeline()
            self.start()
        elif t == Gst.MessageType.STATE_CHANGED and message.src.name == PLAYBIN:
            old_state, new_state, pending_state = message.parse_state_changed()
            if new_state == Gst.State.PLAYING:
                self.emit("resumed")
            elif old_state == Gst.State.PLAYING and new_state == Gst.State.PAUSED:
                self.emit("suspended")
                self.pipeline.set_state(Gst.State.NULL)
        elif t == Gst.MessageType.BUFFERING:
            percent = message.parse_buffering()
            state = self.pipeline.get_state(0)[1]
            if state == Gst.State.PLAYING and percent < 100:
                self.pipeline.set_state(Gst.State.PAUSED)
            elif state == Gst.State.PAUSED and percent == 100:
                self.pipeline.set_state(Gst.State.PLAYING)

    def _key_pressed(self, app, key):
        if app != self._app_name:
            return
        if key == "Play":
            self.toggle_play()
        elif key == "Stop":
            self.stop()
        elif key == "Next":
            # Too bad we don't have access to the Mute key...
            self.toggle_mute()

    def ping_gnome(self):
        if self._headless:
            return
        variant_args = GLib.Variant("(su)", (self._app_name, 0))
        try:
            result  = self.proxy.call_sync("GrabMediaPlayerKeys", variant_args, 0, -1, None)
        except:
            pass

    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self, *args, **kwargs):
        self._notify = kwargs.get("notify", True)
        # FIXME: Setting to NULL directly we don't get the state-change messages on the bus.
        # So set to PAUSED and later on to NULL if we come from PLAYING in the message handler.
        self.pipeline.set_state(Gst.State.PAUSED)

    def toggle_play(self):
        result, state, pending = self.pipeline.get_state(0)
        if state == Gst.State.PLAYING:
            new_state = Gst.State.PAUSED
        else:
            new_state = Gst.State.PLAYING
        self.pipeline.set_state(new_state)
