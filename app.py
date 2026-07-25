### Author: Raj Rijhwani aka Camopants
### Description: BarAssist - Displays helpful orientation assistance for drinkers
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

# v2
# Fixing not minimising on cancel
# Fixing not redisplaying on re-invocation

# v3
# Sub 0 - change from minimisation to full termination on exit
# Sub 1 - confirmation display on open

# v4
# Sub 0 - modifying for marquee display

import app
import os
import sys
import settings

from app_components import Notification, clear_background
from events.input import BUTTON_TYPES, Buttons

from system.eventbus import eventbus

from system.scheduler.events import RequestStopAppEvent

VERSION = "4.0"
BUT_CANX  = BUTTON_TYPES["CANCEL"]
BUT_CONF  = BUTTON_TYPES["CONFIRM"]
#BUT_RIGHT = BUTTON_TYPES["RIGHT"]
#BUT_LEFT  = BUTTON_TYPES["LEFT"]
BUT_UP    = BUTTON_TYPES["UP"]
BUT_DOWN  = BUTTON_TYPES["DOWN"]

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
        super().__init__()
        self.notification = None
        self.__run_state = 0

        self.__buttons = Buttons(self)
        self.__last_button = None
        self.__debounce = [] # button debounce array
        self.__exit_prompt = False
        self.__exit_display = False

        self.__last_image = None
        self.image_exists = False
        self.__image_files_list = []
        self.__image_count = 0
        self.__image_index = 0
        self.__timer = 0
        self.__images_loaded = False
        self.__asset_files = None
        self.__app_name = "camopants_select_avatar"
        print(self.__asset_files)


    def update(self, delta):

        def read_settings():
            s = settings.get(self.__app_name)
            # Generate defaults here
            c = False
            if s==None:
                print(f'Settings for "{self.__app_name}" empty; creating defaults')
                s = {}
            if not 'speed' in s:
                s['speed'] = 50
            if c:
                write_settings(s)
            return s

        def write_settings(s=None):
            if s==None:
                print(f'settings not provided for "{self.__app_name}"')
                return False
            print('Settings write and save')
            settings.set(self.__app_name, s)
            try:
                settings.save()
            except:
                print(f'settings not saved for "{self.__app_name}"')
                return False
            print(f'settings saved for "{self.__app_name}"')
            return True

        def process_button(oButton):
            if self.__buttons.get(oButton):
                if oButton in self.__debounce:
                    pass
                else:
                    print(f'{oButton} pressed')
                    self.__debounce.append(oButton)
                    return True
            else:
                if oButton in self.__debounce:
                    print(f'{oButton} released')
                    self.__debounce.remove(oButton)
            return False


        #print(f'update() ({self.__run_state})')
        if self.__run_state==0:
            return

        # Get settings
        if self.__run_state==1:
            print(f'collect settings ({self.__run_state})')
            self.__settings = read_settings()
            self.__speed = self.__settings['speed']
            print(f'settings: {self.__settings}')
            self.__run_state += 1
            return

        elif self.__run_state==2 and self.__asset_files==None:
            print(f'enumerate avatar files ({self.__run_state})')
            self.__asset_files = tuple(sorted(os.listdir(IMAGE_DIR)))
            self.__run_state += 1
            print(f'file: {self.__asset_files}')
            return

        elif self.__run_state==3:
            print(f'reconcile settings and available files ({self.__run_state})')
            self.__display_array = self.__settings.get('show')
            self.__display_array = [] if self.__display_array==None else [i for i in set(self.__display_array).intersection(set(self.__asset_files))]
            self.__run_state += 2 if self.__display_array==[] else 1
            print(f'reconciled ({self.__run_state})')
            return

        elif self.__run_state==4:
            self.__timer = (self.__timer + 1) % self.__speed
            if self.__timer==0:
                d = self.__image_files_list if self.__display_array==[] else self.__display_array
                self.__image_index = (self.__image_index + 1) % len(d)

        elif self.__run_state==5:
            pass


        if process_button(BUT_CANX):
            if self.__run_state==5:
                self.__run_state = 4
                self.__image_index = 0
                self.__timer = 0
            else:
                self.__exit_prompt = not self.__exit_prompt
                if self.__exit_prompt:
                    print("CANX pressed - exit?")
                else:
                    print("CANX pressed - revert")

        #if self.__buttons.get(BUT_CONF) and self.__exit_prompt:
        if self.__buttons.get(BUT_CONF) and self.__exit_prompt:
            print("CONFIRM pressed - exit confirmed")
            eventbus.emit(RequestStopAppEvent(self))
            return

        if not self.__images_loaded:
            return

        if self.__image_count>0:

            # multi-function
            if process_button(BUT_CONF):
                if self.__run_state==4:
                    self.__run_state = 5
                    self.__image_index = 0
                    print("CONFIRM pressed - enter selection mode")
                    self.__last_image = None
                elif self.__run_state==5:
                    f = self.__image_files_list[self.__last_image]
                    if f in self.__display_array:
                        print(f'CONFIRM pressed - {f} deselected')
                        self.__display_array.remove(f)
                    else:
                        print(f'CONFIRM pressed - {f} selected')
                        self.__display_array.append(f)
                    print(f'{self.__display_array}')
                    self.__settings['show'] = self.__display_array
                    write_settings(self.__settings)
                    self.__last_image = None

            # image select up

            if process_button(BUT_UP):
                if self.__run_state==4:
                    print("UP pressed - speed up")
                    if self.__speed>5:
                        self.__speed /= 2
                        if self.__speed<5:
                            self.__speed = 5
                elif self.__run_state==5:
                    print("UP pressed - change image")
                    self.__image_index = (self.__image_index - 1) % self.__image_count

            # image select down
            if process_button(BUT_DOWN):
                if self.__run_state==4:
                    pass # decrease the cycle rate
                    print("DOWN pressed - slow down")
                    if self.__speed<200:
                        self.__speed *= 2
                        if self.__speed>200:
                            self.__speed = 200
                elif self.__run_state==5:
                    print("DOWN pressed - change image")
                    self.__image_index = (self.__image_index + 1) % self.__image_count

            if self.notification:
                self.notification.update(delta)

    def draw(self, ctx):

        def panel_display(ctx, bg, fg, text_array, fs=24):
            ctx.rgb(*bg).rectangle(-120, -120, 240, 240).fill().text('')
            ctx.font_size = fs
            s = int(ctx.font_size*5/4)
            print(f'font: {ctx.font_size}; step: {s}')
            y = int(-((len(text_array)-1)*s/2))
            for t in text_array:
                if t:
                    ctx.move_to(-100, y).rgb(*fg).text(t)
                y += s

        #print(f'draw() ({self.__run_state})')

        ctx.save()

        if self.__run_state==0:
            print(f'loading notice ({self.__run_state})')
            self.__exit_display = True
            bg = (0, 0.027, 0.188)
            fg = (0.973,0.883, 0)
            l = ['Avatar files loading']
            panel_display(ctx, bg, fg, l, fs=24)
            self.__last_image = None
            self.__run_state += 1
            print(f'notice displayed ({self.__run_state})')

        elif self.__run_state<4:
            pass

        elif self.__exit_prompt:
            #if not self.__exit_display:
            if not self.__last_image==None:
                print('exit prompt')
                self.__exit_display = True
                bg = (1.0, 0, 0)
                fg = (0, 0, 0)
                l = ['[CANCEL] pressed']
                l.append('')
                l.append('[CANCEL] to ignore')
                l.append('[CONFIRM] to exit')
                panel_display(ctx, bg, fg, l, fs=24)
                self.__last_image = None

        else:
            #self.__exit_display = False

            if not self.__images_loaded:
                bg = (0, 0, 0)
                fg = (1.0, 0.5, 0)
                l = ['Loading...']
                panel_display(ctx, bg, fg, l, 24)
                self.__last_image = None
                print('Image loading starts')

                for f in self.__asset_files:
                    print(f'Trying {f}')
                    if is_image_file(IMAGE_DIR + '/' + f):
                        self.__image_files_list.append(f)
                        self.__image_count += 1
                self.__images_loaded = True

            if self.__image_count>0:

                # has a new image been selected? If not, we ignore
                if self.__last_image==self.__image_index:
                    return

                # get the image file name, construct the path, and display it
                self.__last_image=self.__image_index + 0
                if self.__run_state==4 and self.__display_array!=[]:
                    i = self.__display_array[self.__last_image]
                else:
                    i = self.__image_files_list[self.__last_image]
                print(f'Displaying {i}')
                f = IMAGE_DIR + '/' + i
                print('Clear background')
                clear_background(ctx)
                print('Draw image')
                ctx.image(f, -120, -120, 240, 240)
                if self.__run_state==5:
                    if i in self.__display_array:
                        print('do tick')
                        t = ASSET_BASE + '/' + 'tick-circle-64x64.png'
                        tx = 16
                        ctx.image(t, tx, tx, tx+64, tx+64)
                    else:
                        print('no tick')

            else:
                bg = (0, 0.027, 0.188)
                fg = (0.973,0.883, 0)
                l = ['No avatars found']
                panel_display(ctx, bg, fg, l)
                self.__last_image = -1

        ctx.restore()

        if self.notification:
            print('Notification draw')
            self.notification.draw(ctx)

__app_export__ = DisplayAvatar