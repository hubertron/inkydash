#!/usr/bin/python3

from inky import InkyPHAT
from PIL import ImageFont, ImageDraw, Image
import textwrap
import requests
import time
from datetime import datetime
import yaml
from noaa_sdk import noaa
import requests
from requests.exceptions import HTTPError
import json
import logging
import os
import sys

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info("""Status Dashboard for InkyPhat eInk display. Displays Weather, Covid-19 info, PiHole stats, Air Pollution from my personal station and top Hacker News stories. 
Press Ctrl+C to exit!
""")



font = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
redBigFont = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
bigFont = ImageFont.truetype(
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 15)


''' Font Options
DejaVuSans-Bold.ttf      DejaVuSansMono.ttf  DejaVuSerif-Bold.ttf
DejaVuSansMono-Bold.ttf  DejaVuSans.ttf      DejaVuSerif.ttf
'''

'''
Lazy person code copying
sudo nano /usr/lib/systemd/system/eink.service
sudo systemctl start eink.service
sudo systemctl daemon-reload
journalctl -f
'''

# Display Setup
inky_display = InkyPHAT('red')

inky_display.set_border(inky_display.RED)

img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
draw = ImageDraw.Draw(img)


res1day = ""


def getLocation():
    # absolute to run as cron. PiTA
    with open('/home/pi/inkydash/location.yaml') as f:
        location = yaml.load(f, Loader=yaml.FullLoader)
        zipcode = location[0]["zip"]
        country = location[0]["country"]
        state = location[0]["state"]
        return zipcode, country, state


def fetchFeed(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        if 'application/json' in response.headers['content-type']:
          jsonResponse = response.json()
          return jsonResponse
        elif 'text/plain' in response.headers['content-type']:
          textResponse = response.text
          return textResponse
        else: 
          logging.warning("Unknown format in jquery assume json")
          jsonResponse = response.json()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        logging.warning(f'HTTP error occurred: {http_err}')

    except Exception as err:
        print(f'Other error occurred: {err}')
        logging.warning(f'Other error occurred: {err}')

def getWeather():
    try:
        n = noaa.NOAA()
        res = n.get_forecasts(locations[0], locations[1], False)
        res1day = res[0]["detailedForecast"]
        # display on InkyPHAT
        # Take string of text and wrap it at 38 chars
        txt = textwrap.fill(res1day, 36)

        # Get size of text
        w, h = draw.multiline_textsize(txt, font)
        print(w, h)

        # Center Center the text
        x = (inky_display.WIDTH / 2) - (w / 2)
        y = (inky_display.HEIGHT / 2) - (h / 2)

        # Draw a backgrund rect the size of the display
        draw.rectangle((0, 0, inky_display.WIDTH,
                        inky_display.HEIGHT), (inky_display.WHITE))

        # Draw multiline text on scren
        draw.multiline_text((x, 0), txt, inky_display.BLACK, font)
        inky_display.set_image(img.rotate(180))
        inky_display.show()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
        logging.warning(f'HTTP error occurred: {http_err}')

    except Exception as err:
        print(f'Other error occurred: {err}')
        logging.warning(f'Other error occurred: {err}')


def getCovid():
    # Draw a backgrund rect the size of the display
    draw.rectangle((0, 0, inky_display.WIDTH,
                    inky_display.HEIGHT), (inky_display.WHITE))
    jsonResponse = fetchFeed(f'https://api.covidtracking.com/v1/states/{locations[2]}/daily.json')
    todayCovid = jsonResponse[0]["hospitalizedCurrently"]
    yesterdayCovid = jsonResponse[1]["hospitalizedCurrently"]
    currentlyHospitalized = "Hospitalized: " + str(todayCovid)
    hospitalizationChange = str(
        todayCovid - yesterdayCovid) + " new hospitalizations"
    newCases = str(jsonResponse[0]["positiveIncrease"]) + " new cases"
    covidUpdate = datetime.now().strftime('%a %b %d %-I:%M %p')
    draw.text((0, 0), "CO Covid Update", inky_display.BLACK, bigFont)
    draw.text((0, 20), currentlyHospitalized, inky_display.BLACK, bigFont)
    draw.text((0, 40), hospitalizationChange, inky_display.RED, bigFont)
    draw.text((0, 60), newCases, inky_display.RED, bigFont)
    draw.text((0, 88), covidUpdate, inky_display.BLACK, font)

    inky_display.set_image(img.rotate(180))
    inky_display.show()


def getCurrentConditions():
    # Draw a backgrund rect the size of the display
    draw.rectangle((0, 0, inky_display.WIDTH,
                    inky_display.HEIGHT), (inky_display.WHITE))

    # AQI
    aqiResponse = fetchFeed(
        'https://io.adafruit.com/api/v2/drkpxl/feeds/pollution.aqi')
    printAqi = "Current AQI: " + aqiResponse["last_value"]
    draw.text((0, 0), printAqi, inky_display.BLACK, bigFont)

    # Current Temp
    tempResponse = fetchFeed(
        'https://io.adafruit.com/api/v2/drkpxl/feeds/temp')
    printTemp = "Current Temp: " + tempResponse["last_value"] + " °F"
    draw.text((0, 20), printTemp, inky_display.BLACK, bigFont)

    # Current Humidity
    humResponse = fetchFeed(
        'https://io.adafruit.com/api/v2/drkpxl/feeds/humidity')
    printHum = "Current Humidity: " + humResponse["last_value"] + " %"
    draw.text((0, 40), printHum, inky_display.BLACK, bigFont)

    # Feed Last Update
    lastUpdate = aqiResponse["updated_at"]
    draw.text((0, 88), lastUpdate, inky_display.BLACK, font)

    # Draw
    inky_display.set_image(img.rotate(180))
    inky_display.show()


def getHackerNews():
  topics = fetchFeed('https://hacker-news.firebaseio.com/v0/topstories.json')
  toptopics = [topics[0], topics[1], topics[2]]
  topic = ""

  for x in toptopics:
    r = fetchFeed(
        'https://hacker-news.firebaseio.com/v0/item/' + str(x) + '.json')
    topic = (r['title'])
    score = str(r['score']) + " pts"

    # Take string of text and wrap it at 38 chars
    txt = textwrap.fill(topic, 24)

    # Get size of text
    w, h = draw.multiline_textsize(txt, bigFont)

    # Center Center the text
    x = (inky_display.WIDTH / 2) - (w / 2)
    y = (inky_display.HEIGHT / 2) - (h / 2)

    # Draw a backgrund rect the size of the display
    draw.rectangle((0, 0, inky_display.WIDTH,
                    inky_display.HEIGHT), (inky_display.BLACK))

    # Draw multiline text on scren
    draw.multiline_text((x, y), txt, inky_display.WHITE, bigFont)
    draw.text((0, 0), score, inky_display.RED, redBigFont)
    inky_display.set_image(img.rotate(180))
    inky_display.show()
    time.sleep(60)


def getPihole():
  
  # Draw a backgrund rect the size of the display
    draw.rectangle((0, 0, inky_display.WIDTH,
                          inky_display.HEIGHT), 
                          (inky_display.BLACK))

    piholeResponse = fetchFeed('http://pi.hole/admin/api.php')
    printPercentBlockedToday = "PiHoled: " + str(round(piholeResponse["ads_percentage_today"])) + " %"
    printClientsSeen = "Total Clients: " + str(piholeResponse["clients_ever_seen"])
    printQueriesToday = "Queries Today: " + str(piholeResponse["dns_queries_today"])
    printStatus = "PiHole Status: " + piholeResponse['status']
    draw.text((0, 0), printStatus, inky_display.WHITE, bigFont)
    draw.text((0, 20), printQueriesToday, inky_display.WHITE, bigFont)
    draw.text((0, 40), printPercentBlockedToday, inky_display.RED, bigFont)
    draw.text((0, 60), printClientsSeen, inky_display.WHITE, bigFont)

    # Get Public IP, both work.
    #ipResponse = fetchFeed('https://api.ipify.org?format=json')
    ipResponse = fetchFeed('https://icanhazip.com')
    
    printIpResonse = "Public IP: " + ipResponse
    draw.text((0, 80), printIpResonse, inky_display.WHITE, bigFont)
    # Draw
    inky_display.set_image(img.rotate(180))
    inky_display.show()
    time.sleep(120)

while True:
  try:
    # Setup the Most Basic Logging
    locations = getLocation()
    getPihole()
    getHackerNews()
    getCurrentConditions()
    time.sleep(120)
    getCovid()
    time.sleep(120)
    getWeather()
    time.sleep(120)
  except (KeyboardInterrupt, SystemExit):
    print('\nkeyboardinterrupt found!')
    sys.exit(0)
    print('\n...Program Stopped Manually!')
    raise
