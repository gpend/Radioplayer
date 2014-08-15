import urllib2, BeautifulSoup
import json
import time
import HTMLParser

STATIONS={}

class MetaRadio(type):
    def __init__(cls, name, bases, dct):
        super(MetaRadio, cls).__init__(name, bases, dct)
        if name != "Radio":
            STATIONS[name] = cls

class Radio(object):
    __metaclass__ = MetaRadio
    advising_cache_time = False

    def next_update_timestamp(self):
        return None

    def now_playing(self):
        return ("", "", "")

class FIP(Radio):
    live_url = "http://mp3.live.tv-radio.com/fip/all/fiphautdebit.mp3"
    advising_cache_time = True

    def __init__(self):
        super(FIP, self).__init__()
        self._cache_expires = None

    def next_update_timestamp(self):
        return self._cache_expires

    def now_playing(self):
        now = int(round(time.time()))
        url =  "http://fipradio.fr/sites/default/files/import_si/si_titre_antenne/FIP_player_current.json?_=%s" % now
        data = urllib2.urlopen(url).read()
        json_data = json.loads(data)
        song = json_data['current']['song']
        self._cache_expires = song['endTime']
        artist = song['interpreteMorceau'].title()
        album = song['titreAlbum'].title()
        title = song['titre'].title()
        return (artist, album, title)

class FranceInter(Radio):
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

class LeMouv(Radio):
    live_url = "http://mp3.live.tv-radio.com/lemouv/all/lemouvhautdebit.mp3"
    advising_cache_time = True

    def __init__(self):
        super(LeMouv, self).__init__()
        self._cache_expires = None

    def next_update_timestamp(self):
        return self._cache_expires

    def now_playing(self):
        now = int(round(time.time()))
        url =  "http://www.lemouv.com/sites/default/files/direct.json?_=%s" % now
        data = urllib2.urlopen(url).read()
        json_data = json.loads(data)
        self._cache_expires = int(json_data["validite"])
        if (self._cache_expires - now) > 400:
            self._cache_expires = now + 300
        soup = BeautifulSoup.BeautifulSoup(json_data["html"])
        try:
            span =  soup.findAll("span", attrs={"class":"direct-antenne"})[0]
            artist = span.findAll("span", attrs={"class": "artiste"})[0].text
            title = span.findAll("span", attrs={"class": "titre"})[0].text
        except:
            return ("", "", "")
        else:
            return (artist, "", title)

class KCSM(Radio):
    live_url = "http://ice7.securenetsystems.net/KCSM2"

    def now_playing(self):
        url = 'http://kcsm.org/playlist'
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(url).read())
        rows = soup('table', {'class': 'listbackground'})[0].findAll('tr')
        artist = rows[0].find('a',{'class':'artist_title'}).text
        title = rows[0].findAll('td')[-1].text
        album = rows[1].find('a').text
        return (artist, album, title)

class Radio3(Radio):
    live_url = 'http://195.10.10.224/rtve/radio3.mp3'

class TripleJ(Radio):
    live_url = 'http://shoutmedia.abc.net.au:10426'

    def now_playing(self):
        now = int(round(time.time()) / 3e4)
        url =  "http://www.abc.net.au/triplej/feeds/playout/triplej_sydney_playout.xml?_=%s" % now
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(url).read())
        artist = ''
        album = ''
        title = ''
        parser = HTMLParser.HTMLParser()
        for item in soup('item'):
            if item('playing')[0].text == u'now':
                artist = parser.unescape(item('artistname')[0].text)
                album = parser.unescape(item('albumname')[0].text)
                title = parser.unescape(item('title')[0].text)
                break
        return (artist, album, title)
