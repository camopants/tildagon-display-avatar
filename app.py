### Author: Raj Rijhwani aka Camopants
### Description: Displays helpful orientation assistance for drinkers
### Category: Wearables
### License: MIT
"""
Application to display an avatar from a selection of image files.
"""

# v1
# Construction, and basic operations
# - scan the asset directory for images; construct the list
# - display image
# - monitor buttons for UP/DOWN selection

import app
import os
import sys
import settings

from app_components import Notification, clear_background
from events.input import BUTTON_TYPES, Buttons

BUT_X = BUTTON_TYPES["CANCEL"]
BUT_U = BUTTON_TYPES["UP"]
BUT_D = BUTTON_TYPES["DOWN"]

if sys.implementation.name == "micropython":
    apps = os.listdir("/apps")
    path = ""
    for a in apps:
        if a == "camopants_tildagon_display_avatar":
            path = "/apps/" + a
    ASSET_BASE = path + "/assets/"
else:
    ASSET_BASE = "apps/avatar/assets/"
IMAGE_DIR = ASSET_BASE + "/avatars/"

IMAGE_SIGS = {
        b'\xff\xd8': 'jpeg',
        b'\x89PNG\r\n\x1a\n': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        b'BM': 'bmp',
        b'RIFF': 'webp_riff'  # need extra check
    }


def is_file(path):
    try:
        return (os.stat(path)[0] & 0x4000) == 0
    except OSError:
        return False


def is_image_file(path):
    print(f'checking {path}')
    if not is_file(path):
        print(f'{path} is not a file')
        return False
    with open(path, 'rb') as f:
        head = f.read(12)
    for s, name in IMAGE_SIGS.items():
        if head.startswith(s):
            if name == 'webp_riff':
                # check bytes 8..11 == b'WEBP'
                if head[8:12] != b'WEBP':
                    continue
            print(f'{path} is a {name}')
            return True
        print(f'{path} is not a {name}')
    return False


class DisplayAvatar(app.App):

    def __init__(self):
        self.notification = None
        self.__buttons = Buttons(self)
        self.__last_button = None
        self.__debounce = [] # button debounce array

        self.__last_image = None
        self.image_exists = False
        self.__image_files_list = []
        self.__image_count = 0
        self.__image_index = 0
        asset_files = os.listdir(IMAGE_DIR)
        for f in asset_files:
            if is_image_file(IMAGE_DIR + '/' + f):
                self.__image_files_list.append(f)
                self.__image_count += 1


    def update(self, delta):
        if self.__image_count>0:

            if self.__buttons.get(BUT_U):
                if BUT_U in self.__debounce:
                    pass
                else:
                    self.__image_index = (self.__image_index - 1) % self.__image_count
                    self.__debounce.append(BUT_U)
            else:
                if BUT_U in self.__debounce:
                    self.__debounce.remove(BUT_U)

            if self.__buttons.get(BUT_D):
                if BUT_D in self.__debounce:
                    pass
                else:
                    self.__image_index = (self.__image_index + 1) % self.__image_count
                    self.__debounce.append(BUT_D)
            else:
                if BUT_D in self.__debounce:
                    self.__debounce.remove(BUT_D)

            if self.notification:
                self.notification.update(delta)

    def draw(self, ctx):
        if self.__image_count>0:
            if self.__last_image==self.__image_index:
                return
            f = self.__image_files_list[self.__image_index]
            print(f'Displaying {f}')
            f = IMAGE_DIR + '/' + f
            clear_background(ctx)
            ctx.image(f, -120, -120, 240, 240)
            self.__last_image=self.__image_index
        else:
            ctx.save()
            ctx.rgb(255, 127, 0).rectangle(-120, -120, 240, 240).fill()
            ctx.font_size = 32
            ctx.rgb(0, 0, 0).move_to(-80, int(ctx.font_size/2)).text("No avatars found")
            ctx.restore()

        if self.notification:
            self.notification.draw(ctx)

__app_export__ = DisplayAvatar