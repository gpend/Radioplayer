import optparse
import os, sys
import ConfigParser

from gi.repository import GLib

def main(args=None):
    if not args:
        args = sys.argv[1:]

    parser = optparse.OptionParser()
    parser.add_option("-i", "--interval", dest="interval", default=60, type=int,
                      help="scraping interval in seconds")
    parser.add_option("-o", "--output",
                      dest="output", default="",
                      help="output filename. Should be a path to a mp3 file")
    parser.add_option("-s", "--station",
                      dest="station", default="FIP",
                      help="Radio to tune to.")
    parser.add_option("-a", "--audio-sink",
                      dest="audiosink", default="autoaudiosink",
                      help="audio sink to use")
    parser.add_option("-n", "--no-scrobble", action="store_true", default=False,
                      dest="noscrobble",
                      help="disable scrobbling")
    parser.add_option("-l", "--list-stations", action="store_true", default=False,
                      dest="list_stations",
                      help="display the list of radio stations")
    parser.add_option("-x", "--headless", action="store_true", default=False,
                      dest="headless",
                      help="disable desktop notifications")

    (options, args) = parser.parse_args(args)

    if options.list_stations:
        from radioplayer.radios import STATIONS
        print "Supported radio stations:"
        stations = STATIONS.keys()
        stations.sort()
        for name in stations:
            print "- %s" % name
        return 0

    if args:
        cfgfile = args[0]
    else:
        cfgfile = os.path.expanduser("~/.config/radioplayer.cfg")

    config = ConfigParser.RawConfigParser()
    if os.path.exists(cfgfile):
        config.read(cfgfile)

    GLib.set_prgname("RadioPlayer")
    GLib.setenv("PA_PROP_MEDIA_ROLE", "music", True)
    GLib.setenv("PA_PROP_MEDIA_ICON_NAME", "audio-x-mp3", True)

    from radioplayer.notifier import Notifier
    notifier = Notifier(options, config)
    notifier.run()
