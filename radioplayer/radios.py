import urllib2, BeautifulSoup
import json
import time

class Radio(object):

    def __init__(self, notifier):
        self.notifier = notifier

    def artist_song(self):
        return ("", "")

class FipRadio(Radio):
    live_url = "http://mp3.live.tv-radio.com/fip/all/fiphautdebit.mp3"

    def artist_song(self):
        now = int(round(time.time() * 1000))
        url =  "http://fipradio.fr/sites/default/files/direct-large.json?_=%s" % now
        data = urllib2.urlopen(url).read()
        json_data = json.loads(data)
        soup = BeautifulSoup.BeautifulSoup(json_data["html"])
        div =  soup.findAll("div", attrs={"class":"direct-item direct-distance-0 current"})[0]
        artist = div.findAll("div", attrs={"class": "artiste"})[0].text
        title = div.findAll("div", attrs={"class": "titre"})[0].text
        return (artist, title)

class FranceInterRadio(Radio):
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

class LeMouvRadio(Radio):
    live_url = "http://mp3.live.tv-radio.com/lemouv/all/lemouvhautdebit.mp3"

STATIONS={"FIP": FipRadio, "FranceInter": FranceInterRadio, "LeMouv": LeMouvRadio}
