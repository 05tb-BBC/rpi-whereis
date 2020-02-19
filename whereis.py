#!/usr/bin/env python

##
# whereis.py
##
# This script updates a Waveshare 2.13inch three-colour e-Paper HAT
# with status information taken from BBC Whereabouts.
#
# Author: Libby Miller <libby.miller@bbc.co.uk>
# Author: Henry Cooke <henry.cooke@bbc.co.uk>
#
##

import epd2in13b
# import time
# import Image
# import ImageDraw
import ImageFont
import json
from PIL import Image

COLORED = 1
UNCOLORED = 0

# Set the location of the config file
config_location = "/home/pi/.whereabouts/config.txt"

# Check for the requests library
try:
    import requests
except ImportError:
    exit("This script requires the requests module\n"
         "Install with: sudo pip install requests")


# Using BBC IRFS whereabouts system retrive the location for me
def get_location(user_number, auth_token):
    url = 'https://where.virt.ch.bbc.co.uk/api/1/users/%s/location.json?auth_token=%s' % (
        user_number,
        auth_token
    )
    res = requests.get(url)
    if(res.status_code == 200):
        json_data = json.loads(res.text)
        return json_data
    return {}


# Load the config file
def load_config():
    lines = []
    with open(config_location) as f:
        lines = f.read().splitlines()
    return {
        "caption": lines[0],
        "user_number": lines[1],
        "auth_token": lines[2],
        "old_ds": lines[3]
    }


# Save the config file
def save_config(ds):
    lines = []
    with open(config_location, 'r') as f:
        lines = f.readlines()

    lines[3] = ds+"\n"

    with open(config_location, 'w') as f:
        f.writelines(lines)


# R&D ID Card drawing algo
def id_card_draw(epd, frame_black, frame_red):
    im = Image.open('id-card.png')
    pix = im.load()

    for y in range(0, im.size[1]):
        for x in range(0, im.size[0]):
            pixel_colour = pix[x, y]
            if pixel_colour[0] >= 200 and pixel_colour[1] >= 200 and pixel_colour[2] >= 200:  # white
                epd.set_pixel(frame_black, x, y, UNCOLORED)

            elif pixel_colour[0] == 255 and pixel_colour[1] < 200 and pixel_colour[2] < 200:  # red
                epd.set_pixel(frame_red, x, y, COLORED)

            else:  # black
                epd.set_pixel(frame_black, x, y, COLORED)

    return frame_black, frame_red


def main():

    # Load the comfig from the given config location
    config = load_config()
    print(config)

    # Initialise the epd library for drawing the the display
    epd = epd2in13b.EPD()
    epd.init()

    # Set the screen rotation (On RPi Zero: 3 = usb up, 1 = usb down)
    epd.set_rotate(3)

    # clear the frame buffer
    frame_black = [0xFF] * (epd.width * epd.height / 8)
    frame_red = [0xFF] * (epd.width * epd.height / 8)

    # Default ds incase it is not set on the whereabouts system
    ds = "MCUK (Probably)"

    # Get the current location of me
    data = get_location(config["user_number"], config["auth_token"])
    print(data)

    # Set DS to the current location of me if it exists
    if(u'description' in data):
        print(data["description"])
        ds = data["description"]

    # Draw R&D ID Card
    frame_black, frame_red = id_card_draw(epd, frame_black, frame_red)

    # Check the length of the location and alter text size
    # if too long to fit on screen
    # Then draw the location text to the display
    if(len(ds) > len(config["caption"])):
        font1 = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Md.ttf', 13)
        epd.draw_string_at(frame_black, 60, 42, ds, font1, COLORED)
    else:
        font = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Md.ttf', 16)
        epd.draw_string_at(frame_black, 60, 42, ds, font, COLORED)

    # Only draw to the display if the old_ds (in config file)
    # is different to current ds
    if (config["old_ds"] != ds):
        epd.display_frame(frame_black, frame_red)

    # Save the config file with todays ds
    save_config(ds)


if __name__ == '__main__':
    main()
