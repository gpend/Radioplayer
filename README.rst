
A simple radio player implemented in Python.

Currently supports FIP, FranceInter, KCSM, LeMouv and TripleJ. To get
the full list:

  ::
  
    radioplayer -l

Dependencies:

- python-gi
- gstreamer
- gst-plugins-base
- gst-plugins-good

Optional dependencies:

- python-lirc
- python-gntp
- totem-pl-parser

Features:

- notifications of song with libnotify or via python-gntp over the
  network to a Growl daemon
- scrobbling to lastfm and/or librefm
- optionally dump the stream to a local file
- multimedia keys support (stop, playpause)
- headless mode, when dbus and/or X11 is not available
- limited support for Denon AVR amps, power off/on from remote control

To install:

- Use gen_pylast_md5sum.py to get your password hashes for libre.fm/last.fm
- Copy radioplayer.cfg.sample to ~/.config/radioplayer.cfg and edit accordingly
- Run either one of these commands:

  ::

     sudo python setup.py develop
     sudo python setup.py install
