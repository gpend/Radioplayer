# -*- coding: utf-8 -*-

import sys
import time
import urllib2
import httplib
import socket
import gobject
import glib
import dbus
from dbus.mainloop.glib import DBusGMainLoop
DBusGMainLoop(set_as_default=True)

from radioplayer import player, radios, pylast, imstatus

import pynotify
pynotify.init("Radio")

class Notifier:

    def __init__(self, interval, station, audiosink, output, noscrobble, config):
        self.loop = gobject.MainLoop()
        self.interval = interval
        self.station_name = station
        self.audiosink = audiosink
        self.output_path = output
        self.disable_scrobble = noscrobble
        self.config = config

        self.suspended = False

        self.station = radios.STATIONS[self.station_name]()
        self.current_artist_song = None
        self.notification = pynotify.Notification(self.station_name, "foo")
        self.notification.set_timeout(pynotify.EXPIRES_DEFAULT)
        self.notification.connect("closed", self.closed_cb)

        self.login()
        self.start_player()

        self.bus = dbus.SessionBus()
        self.im_manager = imstatus.ImStatusManager(self.bus)
        self.im_manager.save_status()

    def player_paused_or_stopped(self):
        self.suspended = True
        self.notification.clear_actions()
        self.notification.add_action("resume", "Resume playback", self._default_action_cb)
        self.notification.props.icon_name = "media-playback-stop-symbolic"
        self.notification.show()

    def _default_action_cb(self, notification, action):
        self.player.start()

    def start_player(self):
        if self.interval:
            self.player = player.Player(self.station.live_url, self.audiosink,
                                        self.output_path, self.player_paused_or_stopped)
            self.player.start()
        else:
            self.player = None

    def login(self):
        if not self.interval:
            self.lastfm = self.librefm = None
            return

        lastfm_username = self.config.get("scrobbler-lastfm", "user")
        lastfm_pw_hash = self.config.get("scrobbler-lastfm", "password_hash")
        if lastfm_username and lastfm_pw_hash:
            self.lastfm = pylast.get_lastfm_network(api_key="623bbd684658a8eaaa4066037d3c1531",
                                                    api_secret="547e71d1582dfb73f6857444992fa629",
                                                    username=lastfm_username,
                                                    password_hash=lastfm_pw_hash)

        librefm_username = self.config.get("scrobbler-librefm", "user")
        librefm_pw_hash = self.config.get("scrobbler-librefm", "password_hash")
        if librefm_username and librefm_pw_hash:
            self.librefm = pylast.get_librefm_network(username=librefm_username,
                                                      password_hash=librefm_pw_hash)

    def scrobble_current(self, current_artist_song):
        if self.disable_scrobble:
            return
        if not current_artist_song:
            return
        artist_name, track_name = current_artist_song
        now = time.time()
        artist_nice_name = artist_name
        track_nice_name = track_name
        album_title = ""
        duration = 0
        mbid = ""
        if self.lastfm:
            search_results = self.lastfm.search_for_track(artist_name, track_name)
            try:
                page = search_results.get_next_page()
            except:
                page = []
            if len(page) > 0:
                track = page[0]
                try:
                    track.scrobble(now)
                    artist_nice_name = track.artist.name
                    track_nice_name = track.title
                    album = track.get_album()
                    if album:
                        album_title = album.title
                    else:
                        album_title = ""
                    duration = int(track.get_duration() / 1000.)
                    mbid = track.get_mbid() or ""
                except socket.error:
                    return
                except httplib.BadStatusLine:
                    sys.exit(-1)

        if self.librefm:
            source = pylast.SCROBBLE_SOURCE_NON_PERSONALIZED_BROADCAST
            mode = pylast.SCROBBLE_MODE_PLAYED
            scrobble_args = (artist_nice_name, track_nice_name,
                             now, source, mode, duration, album_title,)
            scrobble_kwargs = dict(mbid=mbid)
            try:
                self.librefm.get_scrobbler("tst", "1.0").scrobble(*scrobble_args,
                                                                  **scrobble_kwargs)
            except (socket.error,pylast.ScrobblingError), error:
                print error

    def stop(self):
        self.notification.close()
        if self.player:
            self.player.stop(notify=False)
        self.im_manager.restore_status()
        self.loop.quit()

    def closed_cb(self, reason):
        if self.suspended:
            self.notification.clear_actions()
            self.notification.props.icon_name = "media-playback-start-symbolic"
            self.suspended = False
            self.notification.show()
        elif not self.interval:
            self.notification.close()

    def status(self, name, title):
        status = "♫ %s - %s ♫" % (name, title)
        self.notification.update(self.station_name, status)
        self.notification.props.icon_name = "media-playback-start-symbolic"
        try:
            self.notification.show()
        except glib.GError, error:
            print error
        return "%s: %s" % (self.station_name, status)

    def update(self):
        try:
            current = self.station.artist_song()
        except urllib2.URLError, exc:
            print str(exc)
            return True
        except Exception, exc:
            print exc
            return True

        if "" not in current and (not self.current_artist_song or \
                                  (current != self.current_artist_song)):
            message = self.status(*current)
            print message
            self.im_manager.set_status_async(message)
            self.scrobble_current(current)
            self.player.ping_gnome()
        self.current_artist_song = current
        return True

    def run(self):
        self.update()
        if self.interval:
            self.timeout_id = gobject.timeout_add_seconds(self.interval,
                                                          self.update)
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.stop()
