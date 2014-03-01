
A simple radio player implemented in Python.

Currently supports FIP, FranceInter, KCSM, LeMouv and TripleJ.

Dependencies:

- python-gi
- gstreamer
- gst-plugins-base
- gst-plugins-good
- optional: python-lirc
- optional: python-gntp

Features:

- notifications of song with libnotify or via python-gntp over the
  network to a Growl daemon
- scrobbling to lastfm and/or librefm
- optionally dump the stream to a local file
- multimedia keys support (stop, playpause)
- IM message status update (pidgin, gajim, telepathy)
- headless mode, when dbus and/or X11 is not available

To install:

- Use gen_pylast_md5sum.py to get your password hashes for libre.fm/last.fm
- Copy radioplayer.cfg.sample to ~/.config/radioplayer.cfg and edit accordingly
- Run either one of these commands:

  ::

     sudo python setup.py develop
     sudo python setup.py install
