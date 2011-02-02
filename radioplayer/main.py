import optparse
import os, sys
import ConfigParser

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

    (options, args) = parser.parse_args(args)

    if args:
        cfgfile = args[0]
    else:
        cfgfile = os.path.expanduser("~/.config/radioplayer.cfg")

    config = ConfigParser.RawConfigParser()
    if os.path.exists(cfgfile):
        config.read(cfgfile)

    from radioplayer.notifier import Notifier
    notifier = Notifier(options.interval, options.station, options.audiosink, options.output, config)
    notifier.run()
