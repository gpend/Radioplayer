# -*- coding: utf-8 -*-

import sys
import time
import urllib2
import httplib
import socket
from gi.repository import GLib, Gio

from radioplayer import player, radios, pylast, imstatus, desktop_notify

class Notifier:

    def __init__(self, interval, station, audiosink, output, noscrobble, config):
        self.loop = GLib.MainLoop()
        self.interval = interval
        self.station_name = station
        self.audiosink = audiosink
        self.output_path = output
        self.disable_scrobble = noscrobble
        self.config = config

        self.suspended = False

        self.station = radios.STATIONS[self.station_name](self)
        self.current_status = None
        self.notification = desktop_notify.Notification("RadioPlayer")

        self.login()
        self.start_player()

        self.bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.im_manager = imstatus.ImStatusManager(self.bus)
        self.im_manager.save_status()

    def _player_suspended(self, player):
        self.suspended = True
        self.notification.clear_actions()
        self.notification.add_action("resume", "Resume playback", self._default_action_cb)
        self.notification.icon_name = "media-playback-stop-symbolic"
        self.notification.show()

    def _player_resumed(self, player):
        self.suspended = False
        self.notification.clear_actions()
        self.notification.icon_name = "media-playback-start-symbolic"
        self.notification.show()

    def _default_action_cb(self, notification, action):
        self.player.start()

    def start_player(self):
        if self.interval:
            self.player = player.Player(self.station.live_url, self.audiosink,
                                        self.output_path)
            self.player.connect("suspended", self._player_suspended)
            self.player.connect("resumed", self._player_resumed)
            self.player.start()
        else:
            self.player = None

    def login(self):
        if self.disable_scrobble:
            return
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

    def scrobble_current(self, current_status):
        if self.disable_scrobble:
            return
        if not current_status:
            return
        artist_name, album_title, track_name = current_status
        now = int(time.time())
        artist_nice_name = artist_name
        track_nice_name = track_name
        duration = 0
        mbid = ""
        if self.lastfm:
            search_results = self.lastfm.search_for_track(artist_name, track_name)
            page = search_results.get_next_page()
            if len(page) > 0:
                track = page[0]
                if not album_title:
                    album = track.get_album()
                    if album:
                        album_title = album.title
                duration = int(track.get_duration() / 1000.)
                mbid = track.get_mbid() or ""
                try:
                    self.lastfm.scrobble(track.artist.name, track.title, now, album_title, album_artist=None, track_number=None, duration=duration, stream_id=None, context=None, mbid=mbid)
                except socket.error:
                    return
                except httplib.BadStatusLine:
                    sys.exit(-1)
                except pylast.WSError:
                    # FIXME: Deal properly with this one...
                    pass
                artist_nice_name = track.artist.name
                track_nice_name = track.title


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

    def status(self, name, album, title):
        status = u"♫ %s - %s ♫" % (name, title)
        self.notification.update(self.station_name, status)
        self.notification.icon_name = "media-playback-start-symbolic"
        self.notification.show()
        GLib.setenv("PA_PROP_MEDIA_ARTIST", name, True)
        GLib.setenv("PA_PROP_MEDIA_TITLE", title, True)
        return "%s: %s" % (self.station_name, status)

    def update(self):
        try:
            current = self.station.now_playing()
        except urllib2.URLError, exc:
            print str(exc)
            return True
        except Exception, exc:
            print exc
            return True

        if "" not in (current[0], current[2]) and (not self.current_status or \
                                  (current != self.current_status)):
            message = self.status(*current)
            print message
            self.im_manager.set_status_async(message)
            try:
                self.scrobble_current(current)
            except Exception, exc:
                # Something went wrong, try 2 more times and die.
                attempts = 2
                while attempts > 0:
                    try:
                        self.scrobble_current(current)
                    except Exception, exc:
                        attempts -= 1
                        continue
                    else:
                        break
                if not attempts:
                    print "Scrobble failed..."
            self.player.ping_gnome()
        self.current_status = current
        return True

    def run(self):
        self.update()
        if self.interval:
            self.timeout_id = GLib.timeout_add_seconds(self.interval, self.update)
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.stop()
