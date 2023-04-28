import disnake, json, pickle, random, asyncio
from disnake.ext import commands
from disnake.interactions import MessageInteraction
from tank import *
from io import BytesIO

bot = commands.InteractionBot(test_guilds=[791818283867045941])


class TankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tankgrid = TankGrid(15, 10, 256)
        self.livepreview_msg = None
    
    async def _image_to_bytes(self, image):
        if image is None:
            return None
        _img = BytesIO()
        image.save(_img, 'png')
        _img.seek(0)

        return _img
    
    async def _updatemap(self):
        if self.livepreview_msg is None:
            return
        
        await self.livepreview_msg.edit(content='<a:loading:1086100481849430036> Updating Live Preview...')
        
        image = await self.tankgrid.create_image()
        image = await self._image_to_bytes(image)

        await self.livepreview_msg.edit(content='', embed=disnake.Embed.from_dict({
            'title': 'Tank Tactics - Live Map',
            'image': {
                'url': 'attachment://map.png',
            },
            'color': 0x2b2d31
        }),file=disnake.File(image, filename='map.png'))

    @commands.slash_command(
        name='livepreview', 
        description='Start a live preview of the tank grid.',
    )
    @commands.default_member_permissions(manage_guild=True)
    async def _livepreview(self, inter : disnake.ApplicationCommandInteraction):
        await inter.response.defer(with_message=True, ephemeral=True)

        msg = await inter.channel.send('<a:loading:1086100481849430036> Starting Live Preview...')
        self.livepreview_msg = msg

        await inter.followup.send('Live Preview Started!', ephemeral=True)

        await self._updatemap()

    @commands.slash_command(
        name='tank',
        description='Create a tank.',
    )
    async def _tank(self, inter : disnake.ApplicationCommandInteraction):
        await inter.response.defer(with_message=True, ephemeral=True)
        
        for pos, tank in self.tankgrid.tanks.items():
            if tank.user.id == inter.author.id: break
        else:
            tank = Tank(self.tankgrid, inter.author)
            await tank._fetch_avatar()
            while True:
                try:
                    await tank._place(random.randint(0, self.tankgrid.width-1), random.randint(0, self.tankgrid.height-1))
                    break
                except IndexError: ...
            asyncio.create_task(self._updatemap())
        
        async def get_map():
            image = await self.tankgrid.create_tank_image(tank)
            image = await self._image_to_bytes(image)
            file = disnake.File(image, filename='map.png')
            return file

        async def movement_view():
            view = disnake.ui.View(timeout=None)

            empty_button = lambda row=0: view.add_item(disnake.ui.Button(style=disnake.ButtonStyle.gray, emoji='<:nothing:1101337783328575569>', disabled=True, row=row))
            
            class MoveButton(disnake.ui.Button):
                def __init__(self, tank, direction, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.tank = tank
                    self.style = disnake.ButtonStyle.gray
                    self.direction = direction

                    if not self.tank.can_move(self.direction):
                        self.disabled = True

                async def callback(button_self, interaction : disnake.MessageInteraction):
                    # await interaction.response.defer()
                    await button_self.tank.move(button_self.direction)
                    # await self._updatemap()
                    asyncio.create_task(self._updatemap())
                    await interaction.response.edit_message(view=await movement_view(), file=await get_map())
            
            class ShootButton(disnake.ui.Button):
                def __init__(self, tank, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.tank = tank
                    self.row = 1
                    self.emoji = '<:bang:931340204051152926>'
                    self.style = disnake.ButtonStyle.gray

                    # if self.tank.can_shoot():
                    #     self.disabled = False

                async def callback(self, interaction : disnake.MessageInteraction):
                    await interaction.response.defer()
                    # self.tank.shoot()
                    # await self._updatemap()
            
            class UpgradeRange(disnake.ui.Button):
                def __init__(self, tank, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.tank = tank
                    self.row = 0
                    self.emoji = '<:earth:931340204332183602>'
                    self.style = disnake.ButtonStyle.gray

                    # if self.tank.can_shoot():
                    #     self.disabled = False
                
                async def callback(self, interaction: MessageInteraction):
                    self.tank.range += 1
                    await interaction.response.edit_message(view=await movement_view(), file=await get_map())

            class PurchaseHeart(disnake.ui.Button):
                def __init__(self, tank, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.tank = tank
                    self.row = 1
                    self.emoji = '<:heart:931356446887669760>'
                    self.style = disnake.ButtonStyle.gray

                    # if self.tank.can_shoot():
                    #     self.disabled = False
            
            class GiftItem(disnake.ui.Button):
                def __init__(self, tank, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.tank = tank
                    self.row = 2
                    self.emoji = '<:crate_epic:883811932157648917>'
                    self.style = disnake.ButtonStyle.gray

                    # if self.tank.can_shoot():
                    #     self.disabled = False

            
            empty_button()
            view.add_item(MoveButton(tank, 3, emoji='<:arrow_up:931340203992449064>', row=0))
            empty_button()
            empty_button()
            view.add_item(UpgradeRange(tank))

            view.add_item(MoveButton(tank, 2, emoji='<:arrow_left:931340204051169312>', row=1))
            view.add_item(ShootButton(tank))
            view.add_item(MoveButton(tank, 0, emoji='<:arrow_right:931340204021792868>', row=1))
            empty_button(1)
            view.add_item(PurchaseHeart(tank))

            empty_button(2)
            view.add_item(MoveButton(tank, 1, emoji='<:arrow_down:931340204025983066>', row=2))
            empty_button(2)
            empty_button(2)
            view.add_item(GiftItem(tank))


            return view
            

        

        # create the embed
        embed = disnake.Embed.from_dict({
            'author': {
                'name': f'{tank.user.display_name}\'s Tank',
                'icon_url': 'attachment://avatar.png',
            },
            'image': {
                'url': 'attachment://map.png',
            },
            'description': '<:heart:931356446887669760><:heart:931356446887669760><:heart:931356446887669760>\n<:dollar:931340204495745114> `1`',
            'color': 0x2b2d31,
        })

        view = await movement_view()



        gift = disnake.ui.Button(style=disnake.ButtonStyle.gray, emoji='<:crate_epic:883811932157648917>')
        buy_heart = disnake.ui.Button(style=disnake.ButtonStyle.gray, emoji='<:heart:931356446887669760>')
        upgrade_range = disnake.ui.Button(style=disnake.ButtonStyle.gray, emoji='<a:bang:931340204051152926>')

        await inter.followup.send(embed=embed, files=[disnake.File(await self._image_to_bytes(tank.image), filename='avatar.png'), await get_map()], view=view)

    @commands.slash_command(
        name='suicide',
        description='Commit suicide.'
    )
    async def _suicide(self, inter : disnake.ApplicationCommandInteraction):

        await inter.response.defer(with_message=True, ephemeral=True)

        for pos, tank in self.tankgrid.tanks.items():
            if tank.user.id == inter.author.id:
                break
        else:
            return await inter.followup.send('You do not have a tank. Use /tank.')
        
        tank.kill()

        asyncio.create_task(self._updatemap())






bot.add_cog(TankCog(bot))

with open('secrets.json') as f:
    secrets = json.load(f)

bot.run(secrets['TOKEN'])