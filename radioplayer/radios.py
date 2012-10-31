import urllib2, BeautifulSoup
import json
import time

class Radio(object):

    def __init__(self, notifier):
        self.notifier = notifier

    def now_playing(self):
        return ("", "", "")

class FipRadio(Radio):
    live_url = "http://mp3.live.tv-radio.com/fip/all/fiphautdebit.mp3"

    def now_playing(self):
        now = int(round(time.time() * 1000))
        url =  "http://fipradio.fr/sites/default/files/direct-large.json?_=%s" % now
        data = urllib2.urlopen(url).read()
        json_data = json.loads(data)
        soup = BeautifulSoup.BeautifulSoup(json_data["html"])
        div =  soup.findAll("div", attrs={"class":"direct-item direct-distance-0 current"})[0]
        artist = div.findAll("div", attrs={"class": "artiste"})[0].text
        album = div.findAll("div", attrs={"class": "album"})[0].text
        title = div.findAll("div", attrs={"class": "titre"})[0].text
        return (artist, album, title)

class FranceInterRadio(Radio):
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

class LeMouvRadio(Radio):
    live_url = "http://mp3.live.tv-radio.com/lemouv/all/lemouvhautdebit.mp3"

class KcsmRadio(Radio):
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

STATIONS={"FIP": FipRadio,
          "FranceInter": FranceInterRadio,
          "LeMouv": LeMouvRadio,
          "KCSM": KcsmRadio,
          }
