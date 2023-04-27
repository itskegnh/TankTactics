import disnake, json, os
from disnake.ext import commands

bot = commands.InteractionBot(test_guilds=[791818283867045941])

@bot.slash_command(name='ping')
async def _ping(inter : disnake.ApplicationCommandInteraction):
    await inter.response.send_message('Pong!')

with open('secrets.json') as f:
    secrets = json.load(f)

bot.run(secrets['TOKEN'])
