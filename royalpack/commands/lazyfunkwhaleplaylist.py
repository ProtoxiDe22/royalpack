import aiohttp
import urllib.parse
import royalnet.commands as rc
from .lazyplay import LazyplayCommand


class LazyfunkwhaleplaylistCommand(LazyplayCommand):
    name: str = "lazyfunkwhaleplaylist"

    aliases = ["lfwp", "lfwplaylist", "lazyfunkwhalep"]

    description: str = "Cerca una playlist su RoyalWhale e aggiungila (lazy) alla coda della chat vocale."

    syntax = "{ricerca}"

    def get_embed_color(self):
        return 0x009FE3

    async def get_urls(self, args):
        search = urllib.parse.quote(args.joined(require_at_least=1))
        async with aiohttp.ClientSession() as session:
            async with session.get(self.config["Funkwhale"]["instance_url"] +
                                   f"/api/v1/playlists/?q={search}&ordering=-creation_date&playable=true") as response:
                j = await response.json()
            if len(j["results"]) < 1:
                raise rc.UserError("Nessuna playlist trovata con il nome richiesto.")
            playlist = j["results"][0]
            playlist_id = playlist["id"]
            async with session.get(self.config["Funkwhale"]["instance_url"] +
                                   f"/api/v1/playlists/{playlist_id}/tracks") as response:
                j = await response.json()
        return list(map(lambda t: f'{self.config["Funkwhale"]["instance_url"]}{t["track"]["listen_url"]}', j["results"]))
