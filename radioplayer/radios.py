
import urllib2, BeautifulSoup


class FipRadio:
    live_url = "http://mp3.live.tv-radio.com/fip/all/fiphautdebit.mp3"

    def artist_song(self):
        data = urllib2.urlopen("http://sites.radiofrance.fr/chaines/fip/endirect/").read()
        soup = BeautifulSoup.BeautifulSoup(data)
        encours = soup.findAll("td", attrs={"class":"blanc11"})[-5]
        artiste = encours.contents[0]
        name = artiste.contents[0].contents[0].strip().title()
        title = artiste.contents[1].replace('|', '').strip().title()
        return (name, title)

class FranceInterRadio:
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

    def artist_song(self):
        # TODO
        return ("", "")

STATIONS={"FIP": FipRadio, "FranceInter": FranceInterRadio}
