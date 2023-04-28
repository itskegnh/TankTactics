import httpx
from io import BytesIO
from PIL import Image, ImageDraw

class TankGrid:
    def __init__(self, width, height, cellsize):
        self.width = width
        self.height = height
        self.cellsize = cellsize
        self.outline_width = self.cellsize // 25

        self.tanks = {}
    
    def _create_grid(self, width, height):
        image = Image.new('RGB', (width*self.cellsize, height*self.cellsize), (255, 255, 255))
        draw = ImageDraw.Draw(image)

        for x in range(width):
            for y in range(height):
                draw.rectangle((x*self.cellsize, y*self.cellsize, (x+1)*self.cellsize, (y+1)*self.cellsize), outline=(45, 45, 45), width=self.outline_width)
        
        return image
    
    def create_image(self):
        image = self._create_grid(self.width, self.height)

        for tank in self.tanks:
            x, y = tank
            image.paste(self.tanks[tank], (x*self.cellsize+self.outline_width, y*self.cellsize+self.outline_width))
        
        return image

class Tank:
    def __init__(self, tank_grid, user):
        self.user = user
        self.tank_grid = tank_grid
        
        # get image
        response = httpx.get(user.avatar.url)
        self.image = Image.open(BytesIO(response.content))
        self.image = self.image.resize(
            (tank_grid.cellsize-tank_grid.outline_width*2+1, 
             tank_grid.cellsize-tank_grid.outline_width*2+1)
        )
        self.image = self.image.convert('RGB')

        self.x, self.y = None, None

        self.action_points = 0
        self.is_dead = False

    def _place(self, x, y):
        
        # check if there is a tank already there
        if (x, y) in self.tank_grid.tanks:
            raise IndexError('Tank already exists at that location')
        
        # check if we have a location already
        if self.x is not None and self.y is not None:
            del self.tank_grid.tanks[(self.x, self.y)]
        
        # place tank
        self.tank_grid.tanks[(x, y)] = self.image
        

    def move(self, direction):
        try:
            if direction == 0:
                self._place(self.x+1, self.y)
            elif direction == 1:
                self._place(self.x, self.y+1)
            elif direction == 2:
                self._place(self.x-1, self.y)
            elif direction == 3:
                self._place(self.x, self.y-1)
        except IndexError: ...
    
    def kill(self):
        self.is_dead = True
        self.image = self.image.convert('L')

            





