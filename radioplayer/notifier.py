# -*- coding: utf-8 -*-

import sys
import time
import urllib2
import httplib
import socket
from gi.repository import GLib, Gio

from radioplayer import player, radios, pylast, imstatus, desktop_notify, lirc_input, denon

try:
    from radioplayer import growl_notify
except ImportError:
    growl_notify = None

class Notifier:

    def __init__(self, options, config):
        self.loop = GLib.MainLoop()
        self.interval = options.interval
        self.station_name = options.station
        self.audiosink = options.audiosink
        self.output_path = options.output
        self.disable_scrobble = options.noscrobble
        self.disable_imstatus = options.noimstatus
        self.headless = options.headless
        self.config = config

        self.timeout_id = 0
        self.suspended = False

        self.station = radios.STATIONS[self.station_name]()
        self.current_status = None
        if not self.headless:
            self.notification = desktop_notify.Notification("RadioPlayer")
        elif growl_notify:
            try:
                self.notification = growl_notify.Notification("RadioPlayer", config)
            except Exception, exc:
                self.notification = None
        else:
            self.notification = None

        self.login()
        self.start_player()

        self.input_provider = lirc_input.InputProvider(config, self)
        self.input_provider.start()

        if not self.disable_imstatus:
            self.im_manager = imstatus.ImStatusManager(self.headless)
            self.im_manager.save_status()

        self.denon_remote = denon.DenonRemote(config)

    def handle_input(self, code):
        if code.startswith("key_"):
            idx = int(code[4:])
            stations = radios.STATIONS.keys()
            stations.sort()
            self.station_name = stations[idx-1]
            print self.station_name
            self.station = radios.STATIONS[self.station_name]()
            self.player.set_url(self.station.live_url)
            self.update()
        elif code in ("pause", "play"):
            self.player.toggle_play()
        elif code == "stop":
            self.player.stop()
        elif code == "increment_volume":
            self.player.increment_volume()
        elif code == "decrement_volume":
            self.player.decrement_volume()
        elif code == "mute":
            self.player.toggle_mute()
        elif code == "power":
            self.player.toggle_play()
            if self.denon_remote.enabled:
               self.denon_remote.toggle_power()
        else:
            print "Unhandled input: %s" % code

    def _player_suspended(self, player):
        self.suspended = True
        if not self.notification:
            return
        self.notification.clear_actions()
        self.notification.add_action("resume", "Resume playback", self._resume_playback_cb)
        self.notification.icon_name = "media-playback-stop-symbolic"
        self.notification.show()

    def _player_resumed(self, player):
        self.suspended = False
        if not self.notification:
            return
        self.notification.clear_actions()
        self.notification.add_action("suspend", "Suspend playback", self._suspend_playback_cb)
        self.notification.icon_name = "media-playback-start-symbolic"
        self.notification.show()

    def _resume_playback_cb(self, notification, action):
        self.player.start()

    def _suspend_playback_cb(self, notification, action):
        self.player.stop()

    def start_player(self):
        if self.interval:
            self.player = player.Player(self.station.live_url, self.audiosink,
                                        self.output_path, self.headless)
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

    def _retrieve_song_infos(self, current_status):
        artist_name, album_title, track_name = current_status
        artist_nice_name = artist_name
        track_nice_name = track_name
        duration = 0
        mbid = ""
        if self.lastfm and artist_name and track_name:
            search_results = self.lastfm.search_for_track(artist_name, track_name)
            page = self._execute_with_pylast(getattr(search_results, "get_next_page"))
            if page and len(page) > 0:
                track = page[0]
                if not album_title:
                    album = track.get_album()
                    if album:
                        album_title = album.title
                duration = self._execute_with_pylast(track.get_duration)
                if duration:
                    duration = int(duration / 1000.)
                else:
                    duration = 0
                mbid = self._execute_with_pylast(track.get_mbid) or ""
                artist_nice_name = track.artist.name
                track_nice_name = track.title

        return (artist_nice_name, album_title, track_nice_name, duration, mbid)

    def _execute_with_pylast(self, function, *args, **kwargs):
        try:
            result = function(*args, **kwargs)
        except Exception, exc:
            # Something went wrong, try 2 more times and die.
            attempts = 2
            while attempts > 0:
                try:
                    result = function(*args, **kwargs)
                except Exception, exc:
                    attempts -= 1
                    continue
                else:
                    break
            if not attempts:
                print "Call to %r failed..." % function
                result = None
        return result

    def scrobble_update_now_playing(self, current):
        if self.disable_scrobble:
            return
        if not current:
            return
        artist_nice_name, album_title, track_nice_name, duration, mbid = self._retrieve_song_infos(current)
        if self.lastfm:
            self._execute_with_pylast(getattr(self.lastfm, "update_now_playing"), artist_nice_name, track_nice_name,
                                      album=album_title, duration=duration, mbid=mbid)

    def scrobble_song(self, current_status):
        if self.disable_scrobble:
            return
        if not current_status:
            return
        artist_nice_name, album_title, track_nice_name, duration, mbid = self._retrieve_song_infos(current_status)
        now = int(time.time())
        if self.lastfm and '' not in (artist_nice_name, track_nice_name):
            self._execute_with_pylast(getattr(self.lastfm, "scrobble"), artist_nice_name, track_nice_name,
                                      now, album_title, album_artist=None, track_number=None, duration=duration,
                                      stream_id=None, context=None, mbid=mbid)

        if self.librefm:
            source = pylast.SCROBBLE_SOURCE_NON_PERSONALIZED_BROADCAST
            mode = pylast.SCROBBLE_MODE_PLAYED
            scrobble_args = (artist_nice_name, track_nice_name,
                             now, source, mode, duration, album_title,)
            scrobble_kwargs = dict(mbid=mbid)
            scrobbler = self.librefm.get_scrobbler("tst", "1.0")
            self._execute_with_pylast(getattr(scrobbler, "scrobble"), *scrobble_args, **scrobble_kwargs)

    def stop(self):
        if self.notification:
            self.notification.close()
        if self.player:
            self.player.stop(notify=False)
        if not self.disable_imstatus:
            self.im_manager.restore_status()
        self.loop.quit()

    def status(self, name, album, title):
        status = u"♫ %s - %s ♫" % (name, title)
        if self.notification:
            self.notification.update(self.station_name, status)
            if not self.notification.actions:
                self.notification.add_action("suspend", "Suspend playback", self._suspend_playback_cb)
            self.notification.icon_name = "media-playback-start-symbolic"
            self.notification.show()
        GLib.setenv("PA_PROP_MEDIA_ARTIST", name, True)
        GLib.setenv("PA_PROP_MEDIA_TITLE", title, True)
        return "%s: %s" % (self.station_name, status)

    def update(self):
        if self.suspended:
            return True
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
            if self.station.advising_cache_time:
                if self.timeout_id:
                    GLib.source_remove(self.timeout_id)
                    self.timeout_id = 0
                delta = self.station.next_update_timestamp() - time.time()
                if delta <= 0:
                    delta = 5
                self.timeout_id = GLib.timeout_add_seconds(int(delta), self.update)

            message = self.status(*current)
            print message
            if not self.disable_imstatus:
                self.im_manager.set_status_async(message)
            if self.current_status:
                self.scrobble_song(self.current_status)
            self.scrobble_update_now_playing(current)
            self.player.ping_gnome()
        elif self.station.advising_cache_time:
            if self.timeout_id:
                GLib.source_remove(self.timeout_id)
                self.timeout_id = 0
            delta = 5
            self.timeout_id = GLib.timeout_add_seconds(int(delta), self.update)

        self.current_status = current

        return not self.station.advising_cache_time

    def run(self):
        self.update()
        if self.interval and not self.timeout_id:
            self.timeout_id = GLib.timeout_add_seconds(self.interval, self.update)
        try:
            self.loop.run()
        except KeyboardInterrupt:
            self.stop()
