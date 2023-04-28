import httpx, asyncio
from io import BytesIO
from PIL import Image, ImageDraw

class TankGrid:
    def __init__(self, width, height, cellsize):
        self.width = width
        self.height = height
        self.cellsize = cellsize
        self.outline_width = self.cellsize // 25

        self.tanks = {}
    
    async def _create_grid(self, width, height):
        image = Image.new('RGB', (width*self.cellsize, height*self.cellsize), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        for x in range(width):
            for y in range(height):
                draw.rectangle((x*self.cellsize, y*self.cellsize, (x+1)*self.cellsize, (y+1)*self.cellsize), outline=(45, 45, 45), width=self.outline_width)
        
        return image
    
    async def create_image(self):
        image = await self._create_grid(self.width, self.height)

        for tank in self.tanks:
            x, y = tank
            image.paste(self.tanks[tank].image, (x*self.cellsize+self.outline_width, y*self.cellsize+self.outline_width))
        
        return image
    
    async def create_tank_image(self, tank):
        for pos, _tank in self.tanks.items():
            if _tank.user.id == tank.user.id: break
        else:
            raise ValueError('Tank not found')
        
        x, y = pos
        
        image = await self._create_grid(tank.range*2+1, tank.range*2+1)
        
        for _x in range(x-tank.range, x+tank.range+1):
            for _y in range(y-tank.range, y+tank.range+1):
                if (_x, _y) in self.tanks:
                    image.paste(self.tanks[(_x, _y)].image, ((_x-x+tank.range)*self.cellsize+self.outline_width, (_y-y+tank.range)*self.cellsize+self.outline_width))
                
        # draw range
        draw = ImageDraw.Draw(image)
        draw.rectangle((self.cellsize, self.cellsize, (tank.range*2)*self.cellsize, (tank.range*2)*self.cellsize), outline=(255, 0, 0), width=self.outline_width)

        # draw black over cells not in bounds
        for virtual_x in range(tank.range*2+1):
            for virtual_y in range(tank.range*2+1):
                # convert local (virtual) coordinates to global coordinates
                real_x, real_y = virtual_x + x-tank.range, virtual_y + y-tank.range
                if real_x < 0 or real_y < 0 or real_x >= self.width or real_y >= self.height:
                    draw.rectangle((virtual_x*self.cellsize, virtual_y*self.cellsize, (virtual_x+1)*self.cellsize, (virtual_y+1)*self.cellsize), fill=(0, 0, 0))

        return image



class Tank:
    def __init__(self, tank_grid, user):
        self.user = user
        self.tank_grid = tank_grid
        
        # get image
        self.image = None

        self.x, self.y = None, None

        self.action_points = 0
        self.is_dead = False
        self.range = 2
    
    async def _fetch_avatar(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.user.avatar.url)
            self.image = Image.open(BytesIO(response.content))
            self.image = self.image.resize(
                (self.tank_grid.cellsize-self.tank_grid.outline_width*2+1, 
                self.tank_grid.cellsize-self.tank_grid.outline_width*2+1)
            )
            self.image = self.image.convert('RGB')

    async def _place(self, x, y):
        
        # check if there is a tank already there
        if (x, y) in self.tank_grid.tanks:
            raise IndexError('Tank already exists at that location')
        
        # check if we have a location already
        if self.x is not None and self.y is not None:
            del self.tank_grid.tanks[(self.x, self.y)]
        
        # place tank
        self.tank_grid.tanks[(x, y)] = self

        self.x, self.y = x, y
        

    async def move(self, direction):
        try:
            if direction == 0:
                await self._place(self.x+1, self.y)
            elif direction == 1:
                await self._place(self.x, self.y+1)
            elif direction == 2:
                await self._place(self.x-1, self.y)
            elif direction == 3:
                await self._place(self.x, self.y-1)
        except IndexError: ...
    
    def can_move(self, direction):
        # check bounds and players
        if direction == 0:
            if self.x+1 >= self.tank_grid.width:
                return False
            if (self.x+1, self.y) in self.tank_grid.tanks:
                return False
        elif direction == 1:
            if self.y+1 >= self.tank_grid.height:
                return False
            if (self.x, self.y+1) in self.tank_grid.tanks:
                return False
        elif direction == 2:
            if self.x-1 < 0:
                return False
            if (self.x-1, self.y) in self.tank_grid.tanks:
                return False
        elif direction == 3:
            if self.y-1 < 0:
                return False
            if (self.x, self.y-1) in self.tank_grid.tanks:
                return False
        return True
    
    async def kill(self):
        self.is_dead = True
        self.image = self.image.convert('L')

            





