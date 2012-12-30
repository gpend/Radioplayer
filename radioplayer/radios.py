import urllib2, BeautifulSoup
import json
import time

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
        url =  "http://fipradio.fr/sites/default/files/direct-large.json?_=%s" % now
        data = urllib2.urlopen(url).read()
        json_data = json.loads(data)
        self._cache_expires = int(json_data["validite"])
        soup = BeautifulSoup.BeautifulSoup(json_data["html"])
        div =  soup.findAll("div", attrs={"class":"direct-item direct-distance-0 current"})[0]
        artist = div.findAll("div", attrs={"class": "artiste"})[0].text
        album = div.findAll("div", attrs={"class": "album"})[0].text
        title = div.findAll("div", attrs={"class": "titre"})[0].text
        return (artist, album, title)

class FranceInter(Radio):
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

class LeMouv(Radio):
    live_url = "http://mp3.live.tv-radio.com/lemouv/all/lemouvhautdebit.mp3"

class KCSM(Radio):
    live_url = "http://sc1.abacast.com:8240"

    def now_playing(self):
        url = 'http://kcsm.org/playlist'
        soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(url).read())
        tr = soup('table', {'class': 'style54'})[1].tr('td')

        time = tr[1].div.string
        artist = tr[3].string.title()
        title = tr[4].span.string.title()
        album = tr[5].span.string.title()
        return (artist, album, title)
