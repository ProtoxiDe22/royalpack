from typing import *
import discord
import royalnet.commands as rc


class PauseCommand(rc.Command):
    name: str = "pause"

    aliases = ["resume"]

    description: str = "Metti in pausa o riprendi la riproduzione di un file."

    async def run(self, args: rc.CommandArgs, data: rc.CommandData) -> None:
        if self.interface.name == "discord":
            message: discord.Message = data.message
            guild: discord.Guild = message.guild
            guild_id: Optional[int] = guild.id
        else:
            guild_id = None
        response: Dict[str, Any] = await self.interface.call_herald_event("discord", "discord_pause",
                                                                          guild_id=guild_id)

        if response["action"] == "paused":
            await data.reply("⏸ Riproduzione messa in pausa.")

        elif response["action"] == "resumed":
            await data.reply("▶️ Riproduzione ripresa!")
