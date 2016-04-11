from packer.packer import Packer
from collections import deque


class TightPacker(Packer):
    def __init__(self, padding):
        self.padding = padding
        self.padding2 = padding*2
        self.free_rects = []
        self.w = 0
        self.h = 0
        self.free_flag = False  # x direction

    def pack(self, tiles):
        queue = deque(tiles)

        first = queue.popleft()
        first.x = 0
        first.y = 0

        self.w, self.h = first.size()

        while len(queue) > 0:
            tile = queue.popleft()

            found_x, found_y = self.get_free_area(tiles, tile)

            # If nothing found, find edge areas
            if found_x < 0 or found_y < 0:
                found_x, found_y, width, height = self.get_free_vert_edge_area(tiles, tile)
                found_x2, found_y2, width2, height2 = self.get_free_horz_edge_area(tiles, tile)

                vert = True
                if width2*height2 > width*height:
                    found_x, found_y = found_x2, found_y2
                    width, height = width2, height2
                    vert = False

                if found_x >= 0 or found_y >= 0 or width*height > 0:
                    if vert:
                        self.w += tile.width + self.padding2 - width
                    else:
                        self.h += tile.height + self.padding2 - height

            # If nothing found, enlarge area
            if found_x < 0 or found_y < 0:
                if self.free_flag:  # y direction
                    self.h += tile.height + self.padding2
                else:
                    self.w += tile.width + self.padding2
                self.free_flag = not self.free_flag

            found_x, found_y = self.get_free_area(tiles, tile)

            if found_x < 0 or found_y < 0:
                raise RuntimeError('Enlarging packing area failed. Software is bugged.')

            tile.x = found_x
            tile.y = found_y

    # Utils
    def get_tile_at(self, tiles, pos):
        for tile in tiles:
            if tile.is_set():
                if tile.x <= pos[0] < tile.x + tile.width + self.padding2:
                    if tile.y <= pos[1] < tile.y + tile.height + self.padding2:
                        return tile
        return None

    def get_free_area(self, tiles, tile):
        for y in range(0, self.h):
            x = 0
            while x < self.w:
                tmp = self.get_tile_at(tiles, (x, y))
                if tmp:
                    x = tmp.x + tmp.width + self.padding2
                else:
                    not_found = True
                    for y2 in range(y, y + tile.height + self.padding2):
                        for x2 in range(x, x + tile.width + self.padding2):
                            if self.get_tile_at(tiles, (x2, y2)):
                                not_found = False
                                x += 1
                                break
                        if not not_found:
                            break
                    if not_found:
                        return x, y
        return -1, -1

    # Vertical
    def get_free_vert_edge_area(self, tiles, tile):
        width = 0
        height = 0
        found_x = -1
        found_y = -1

        paddD = 0
        for y in range(0, self.h):
            if not self.get_tile_at(tiles, (self.w - 1, y)):
                paddD += 1
                if paddD > self.padding2:
                    x2, y2, width2, height2 = self.check_vert_tile_fit(y, tiles, tile)
                    if width2*height2 > width*height:
                        found_x = x2
                        found_y = y2
                        width, height = width2, height2
                else:
                    paddD = 0

        return found_x, found_y, width, height

    def check_vert_tile_fit(self, y, tiles, tile):
        height = 0
        min_width = 0
        found_x = -1
        found_y = y
        for y2 in range(y, y + tile.height + self.padding2):
            if height >= tile.height + self.padding2 or \
                            y2 >= self.h or \
                    self.get_tile_at(tiles, (self.w - 1, y2)):
                break
            else:
                width = 0
                f_x2 = -1
                for x2 in range(self.w - 1, self.w - tile.width - self.padding2 - 1, -1):
                    if width >= tile.width + self.padding2 or \
                                    x2 < 0 or \
                            self.get_tile_at(tiles, (x2, y2)):
                        break
                    else:
                        width += 1
                        f_x2 = x2
                if width < min_width:
                    min_width = width
                    found_x = f_x2

                height += 1

        if height >= tile.height + self.padding2:
            return found_x, found_y, min_width, height
        else:
            return -1, -1, 0, 0

    # Horizontal
    def get_free_horz_edge_area(self, tiles, tile):
        width = 0
        height = 0
        found_x = -1
        found_y = -1

        paddD = 0
        for x in range(0, self.w):
            if not self.get_tile_at(tiles, (x, self.h - 1)):
                paddD += 1
                if paddD > self.padding2:
                    x2, y2, width2, height2 = self.check_horz_tile_fit(x, tiles, tile)
                    if width2*height2 > width*height:
                        found_x = x2
                        found_y = y2
                        width, height = width2, height2
                else:
                    paddD = 0

        return found_x, found_y, width, height

    def check_horz_tile_fit(self, x, tiles, tile):
        min_height = 0
        width = 0
        found_x = x
        found_y = -1
        for x2 in range(x, x + tile.width + self.padding2):
            if min_height >= tile.width + self.padding2 or \
                            x2 >= self.w or \
                    self.get_tile_at(tiles, (x2, self.h - 1)):
                break
            else:
                height = 0
                f_y2 = -1
                for y2 in range(self.h - 1, self.h - tile.height - self.padding2 - 1, -1):
                    if height >= tile.height + self.padding2 or \
                                    y2 < 0 or \
                            self.get_tile_at(tiles, (x2, y2)):
                        break
                    else:
                        height += 1
                        f_y2 = y2
                if height < min_height:
                    min_height = height
                    found_y = f_y2

                width += 1

        if width >= tile.width + self.padding2:
            return found_x, found_y, width , min_height
        else:
            return -1, -1, 0, 0