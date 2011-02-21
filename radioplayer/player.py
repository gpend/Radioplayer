
import pygst
pygst.require('0.10')
import gst

import mmkeys

class Player:

    def __init__(self, url, audiosink="autoaudiosink", output_location=None):
        self.keys = mmkeys.MmKeys()
        self.keys.connect("mm-playpause", self.playpause_cb)
        self.keys.connect("mm-stop", self.stop)
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

    def start(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

    def stop(self, *args):
        self.pipeline.set_state(gst.STATE_NULL)

    def playpause_cb(self, key, bar):
        result, state, pending = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            new_state = gst.STATE_PAUSED
        else:
            new_state = gst.STATE_PLAYING
        self.pipeline.set_state(new_state)
