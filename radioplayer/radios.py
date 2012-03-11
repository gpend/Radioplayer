
from gi.repository import WebKit, GLib

class FipRadio:
    live_url = "http://mp3.live.tv-radio.com/fip/all/fiphautdebit.mp3"

    def __init__(self):
        self._artist_song = ("", "")
        self.web_view = WebKit.WebView()
        self.web_view.connect("load-finished", self._load_finished_cb)
        self.web_view.load_uri("http://www.fipradio.fr/")

    def _inspect_data(self):
        dom_document = self.web_view.get_dom_document()
        elts = dom_document.get_elements_by_class_name("direct-item direct-distance-0 current")
        elt = elts.item(0)
        artiste_elt = elt.get_elements_by_class_name("artiste").item(0)
        artiste = artiste_elt.get_inner_text().title()
        titre_elt = elt.get_elements_by_class_name("titre").item(0)
        titre = titre_elt.get_inner_text().title()
        self._artist_song = (artiste, titre)
        return True

    def _load_finished_cb(self, view, frame):
        self._inspect_data()
        GLib.timeout_add_seconds(30, self._inspect_data)

    def artist_song(self):
        return self._artist_song

class FranceInterRadio:
    live_url = "http://mp3.live.tv-radio.com/franceinter/all/franceinterhautdebit.mp3"

    def artist_song(self):
        # TODO
        return ("", "")

class LeMouvRadio:
    live_url = "http://mp3.live.tv-radio.com/lemouv/all/lemouvhautdebit.mp3"

    def artist_song(self):
        return ("", "")

STATIONS={"FIP": FipRadio, "FranceInter": FranceInterRadio, "LeMouv": LeMouvRadio}
