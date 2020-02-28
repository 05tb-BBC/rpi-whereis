#!/usr/bin/env python

##
# whereis.py
#
# This script updates a Waveshare 2.13inch three-colour e-Paper HAT
# with status information taken from BBC Whereabouts.
#
##

import epd2in13b
from PIL import Image, ImageFont
from datetime import datetime
import json
import os

try:
    import requests
except ImportError:
    exit("This script requires the requests module\n"
         "Install with: sudo pip install requests")

# Get the current path
PATH = os.path.dirname(__file__)
# Set location for on RD network or off RD network
LOCATION = 'RD'
# File path location for your ID card
ID_CARD_LOCATION = PATH+'/resources/id-card.png'

COLORED = 1
UNCOLORED = 0

# Initialise the epd library for drawing the the display
epd = epd2in13b.EPD()
epd.init()
# Set the screen rotation (On RPi Zero: 3 = usb up, 1 = usb down)
epd.set_rotate(3)
# clear the frame buffer
frame_black = [0xFF] * (epd.width * epd.height)
frame_red = [0xFF] * (epd.width * epd.height)


def get_location_data():
    if LOCATION != 'RD':
        with open('resources/example.json') as f:
            res = json.load(f)
            json_data = res['data']['whereabouts']
            json_data = sort_locations_by_date(json_data)
        return json_data
    else:
        res = requests.get('http://vm-94-205.rd.bbc.co.uk/getwhereabouts/user')
        if(res.status_code == 200):
            json_data = json.loads(res.text)['data']['whereabouts']
            json_data = sort_locations_by_date(json_data)
            return json_data
        return {}


def sort_locations_by_date(data):
    for day in data:
        day['date'] = datetime.strptime(day['date'], "%Y-%m-%d %H:%M:%S")
    data.sort(key=lambda i: i['date'])
    for day in data:
        day['date'] = datetime.strftime(day['date'], "%Y-%m-%d %H:%M:%S")
    return data


def get_today_location(data):
    ds = "unknown"
    for day in data:
        if day['date'].split(' ')[0] == datetime.now().strftime('%Y-%m-%d'):
            ds = day['locationAm']
    return ds


def get_week_locations(data):
    week_locations = []
    for day in data:
        week_locations.append(day['locationAm'])
    return week_locations


# R&D ID Card drawing algo
def draw_id_card(image_location):
    im = Image.open(image_location)
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


def draw_where_is_text():
    font = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Md.ttf', 18)
    where_is = 'Where is Todd?'
    epd.draw_string_at(frame_black, 8, 14, where_is, font, COLORED)


def draw_rectangle(x0, y0, x1, y1):
    epd.draw_filled_rectangle(frame_red, x0, y0, x1, y1, UNCOLORED)
    epd.draw_filled_rectangle(frame_black, x0, y0, x1, y1, UNCOLORED)
    epd.draw_rectangle(frame_black, x0, y0, x1, y1, COLORED)


def add_locations(x, y, location, font):
    w, h = font.getsize(location)
    y += h
    location = location.split(' ')
    for line in location:
        w1, h1 = font.getsize(line)
        epd.draw_string_at(frame_black, x, y, line, font, COLORED)
        y += h1


def update_todays_information(location):
    font = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Lt.ttf', 16)
    day = datetime.today().weekday()
    width = 36
    text_padding = 2
    x0 = day * width  # bottom left
    y0 = epd.height  # bottom left
    x1 = x0 + (epd.width - (4 * width))  # top right
    y1 = y0 - 65  # top right

    draw_rectangle(x0, y0, x1, y1)
    draw_today_day(x0+text_padding, y1+text_padding, day, font)
    add_locations(x0+text_padding, y1, location, font)


def draw_today_day(x, y, day, font):
    font = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Bd.ttf', 15)
    # day_text = datetime.today().strftime('%A')
    day_text = "Today"
    epd.draw_string_at(frame_black, x, y, day_text, font, COLORED)


def update_week_information(locations):
    font = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Lt.ttf', 9)
    day = datetime.today().weekday()
    width = 36
    text_padding = 2
    x0 = 0
    y0 = epd.height  # bottom left
    x1 = x0 + width
    y1 = y0 - 42

    for num in range(0, 5):
        if num != day:
            draw_rectangle(x0, y0, x1, y1)
            draw_week_days(x0+text_padding, y1+text_padding, num, font)
            add_locations(x0+text_padding, y1+text_padding, locations[num], font)
        if num == day:
            x1 += epd.width - (5*width)
        x0 = x1
        x1 += width


def draw_week_days(x, y, day, font):
    font = ImageFont.truetype('/usr/share/fonts/BBCReithSans_Bd.ttf', 10)
    day_text = ['Mon', 'Tues', 'Wed', 'Thur', 'Fri']
    epd.draw_string_at(frame_black, x, y, day_text[day], font, COLORED)


def main():
    # Get the location data
    data = get_location_data()
    todays_location = get_today_location(data)
    week_locations = get_week_locations(data)

    # Display onto the screen
    draw_id_card(ID_CARD_LOCATION)
    draw_where_is_text()
    update_week_information(week_locations)
    update_todays_information(todays_location)

    epd.display_frame(frame_black, frame_red)


if __name__ == '__main__':
    main()
