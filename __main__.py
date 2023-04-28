import disnake, json, pickle
from disnake.ext import commands
import tank
from io import BytesIO

bot = commands.InteractionBot(test_guilds=[791818283867045941])

class TankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tankgrid = tank.TankGrid(15, 10, 256)

bot.add_cog(TankCog(bot))

with open('secrets.json') as f:
    secrets = json.load(f)

bot.run(secrets['TOKEN'])