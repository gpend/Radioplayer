
import urllib2, BeautifulSoup
import json

class FipRadio:
    live_url = "http://mp3.live.tv-radio.com/fip/all/fiphautdebit.mp3"

    def artist_song(self):
        data = urllib2.urlopen("http://fipradio.fr/sites/default/files/direct-large.json").read()
        json_data = json.loads(data)
        soup = BeautifulSoup.BeautifulSoup(json_data["html"])
        div =  soup.findAll("div", attrs={"class":"direct-item direct-distance-0 current"})[0]
        artiste = div.findAll("div", attrs={"class": "artiste"})[0].text
        title = div.findAll("div", attrs={"class": "titre"})[0].text
        return (artiste, title)

class FranceInterRadio:
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

    def artist_song(self):
        # TODO
        return ("", "")

STATIONS={"FIP": FipRadio, "FranceInter": FranceInterRadio}
