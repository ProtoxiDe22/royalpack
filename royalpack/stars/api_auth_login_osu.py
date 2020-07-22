import royalnet.utils as ru
import royalnet.backpack.tables as rbt
import royalnet.constellation.api as rca
import royalnet.constellation.api.apierrors as rcae
import itsdangerous
import aiohttp
import aiohttp.client_exceptions
import datetime
from ..types import oauth_refresh
from ..tables import Osu, FiorygiTransaction


class ApiAuthLoginOsuStar(rca.ApiStar):
    path = "/api/auth/login/osu/v1"

    parameters = {
        "get": {
            "code": "The code returned by the osu! API.",
            "state": "(Optional) The state payload generated by the osu! command to link a new account. "
                     "If missing, just login."
        }
    }

    auth = {
        "get": False,
    }

    tags = ["auth"]

    @property
    def client_id(self):
        return self.config['osu']['client_id']

    @property
    def client_secret(self):
        return self.config['osu']['client_secret']

    @property
    def base_url(self):
        return self.config['base_url']

    @property
    def secret_key(self):
        return self.config['secret_key']

    @rca.magic
    async def get(self, data: rca.ApiData) -> ru.JSON:
        """Login to Royalnet with your osu! account."""
        OsuT = self.alchemy.get(Osu)
        TokenT = self.alchemy.get(rbt.Token)

        code = data.str("code")
        state = data.str("state", optional=True)

        if state is not None:
            serializer = itsdangerous.URLSafeSerializer(self.config["secret_key"], salt="osu")
            uid = serializer.loads(state)
            user = await rbt.User.find(self.alchemy, data.session, uid)
        else:
            user = None

        try:
            t = await oauth_refresh(url="https://osu.ppy.sh/oauth/token",
                                    client_id=self.client_id,
                                    client_secret=self.client_secret,
                                    redirect_uri=f"{self.base_url}{self.path}",
                                    refresh_code=code)
        except aiohttp.client_exceptions.ClientResponseError:
            raise rca.ForbiddenError("osu! API returned an error in the OAuth token exchange")

        async with aiohttp.ClientSession(headers={"Authorization": f"Bearer {t['access_token']}"}) as session:
            async with session.get("https://osu.ppy.sh/api/v2/me/") as response:
                m = await response.json()

        if user is not None:
            osu = OsuT(
                user=user,
                access_token=t["access_token"],
                refresh_token=t["refresh_token"],
                expiration_date=datetime.datetime.now() + datetime.timedelta(seconds=t["expires_in"]),
                osu_id=m["id"],
                username=m["username"]
            )

            data.session.add(osu)
        else:
            osu = await ru.asyncify(
                data.session.query(OsuT).filter_by(osu_id=m["id"]).all
            )
            if osu is None:
                raise rcae.ForbiddenError("Unknown osu! account")
            user = osu.user

        if self.config["osu"]["login"]["enabled"]:
            token: rbt.Token = TokenT.generate(alchemy=self.alchemy, user=user, expiration_delta=datetime.timedelta(days=7))
            data.session.add(token)
            await data.session_commit()

            return token.json()
        else:
            raise rcae.ForbiddenError("Account linked successfully; cannot use this account to generate a Royalnet"
                                      " login token, as osu! login is currently disabled on this Royalnet instance.")