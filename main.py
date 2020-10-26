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



font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
redBigFont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
bigFont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 15)


''' Font Options
DejaVuSans-Bold.ttf      DejaVuSansMono.ttf  DejaVuSerif-Bold.ttf
DejaVuSansMono-Bold.ttf  DejaVuSans.ttf      DejaVuSerif.ttf
'''

'''
Lazy person code copying
sudo nano /usr/lib/systemd/system/eink.service
sudo systemctl start eink.service
sudo systemctl daemon-reload
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
    jsonResponse = response.json()
    return  jsonResponse

  except HTTPError as http_err:
    print(f'HTTP error occurred: {http_err}')
  except Exception as err:
    print(f'Other error occurred: {err}')

def getWeather():
    try: 
      n = noaa.NOAA()
      res = n.get_forecasts(locations[0], locations[1], False)
      res1day = res[0]["detailedForecast"]
      #display on InkyPHAT
      # Take string of text and wrap it at 38 chars
      txt = textwrap.fill(res1day, 36)

      # Get size of text
      w, h = draw.multiline_textsize(txt, font)
      print(w,h)

      # Center Center the text
      x = (inky_display.WIDTH / 2) - (w / 2)
      y = (inky_display.HEIGHT / 2) - (h / 2)

      # Draw a backgrund rect the size of the display
      draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), (inky_display.WHITE))

      # Draw multiline text on scren
      draw.multiline_text((x,0), txt, inky_display.BLACK, font)
      inky_display.set_image(img.rotate(180))
      inky_display.show()

    except HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')

def getCovid():
    # Draw a backgrund rect the size of the display
    draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), (inky_display.WHITE))
    jsonResponse = fetchFeed(f'https://api.covidtracking.com/v1/states/{locations[2]}/daily.json')
    todayCovid = jsonResponse[0]["hospitalizedCurrently"]
    yesterdayCovid = jsonResponse[1]["hospitalizedCurrently"]
    currentlyHospitalized = "Hospitalized: " +  str(todayCovid)
    hospitalizationChange = str(todayCovid - yesterdayCovid) + " new hospitalizations"
    newCases = str(jsonResponse[0]["positiveIncrease"]) + " new cases"
    covidUpdate = datetime.now().strftime('%a %b %d %-I:%M %p')
    draw.text((0,0), "CO Covid Update", inky_display.BLACK, bigFont)
    draw.text((0,20), currentlyHospitalized, inky_display.BLACK, bigFont)
    draw.text((0,40), hospitalizationChange, inky_display.RED, bigFont)
    draw.text((0,60), newCases, inky_display.RED, bigFont)
    draw.text((0,88), covidUpdate, inky_display.BLACK, font)
    

    inky_display.set_image(img.rotate(180))
    inky_display.show()




def getCurrentConditions(): 
    # Draw a backgrund rect the size of the display
    draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), (inky_display.WHITE))

 
    # AQI
    aqiResponse = fetchFeed('https://io.adafruit.com/api/v2/drkpxl/feeds/pollution.aqi')
    printAqi = "Current AQI: " + aqiResponse["last_value"]
    draw.text((0,0), printAqi, inky_display.BLACK, bigFont)

    # Current Temp 
    tempResponse = fetchFeed('https://io.adafruit.com/api/v2/drkpxl/feeds/temp')
    printTemp = "Current Temp: " + tempResponse["last_value"] + " °F"
    draw.text((0,20), printTemp, inky_display.BLACK, bigFont)

    # Current Humidity 
    humResponse = fetchFeed('https://io.adafruit.com/api/v2/drkpxl/feeds/humidity')
    printHum = "Current Humidity: " + humResponse["last_value"] + " %"
    draw.text((0,40), printHum, inky_display.BLACK, bigFont)

    # Feed Last Update
    lastUpdate = aqiResponse["updated_at"]
    draw.text((0,88), lastUpdate, inky_display.BLACK, font)
  
    # Draw
    inky_display.set_image(img.rotate(180))
    inky_display.show()




def getHackerNews():
    topics = fetchFeed('https://hacker-news.firebaseio.com/v0/topstories.json')
    toptopics = [topics[0], topics[1], topics[2]]
    topic = ""

    for x in toptopics:
        r = fetchFeed('https://hacker-news.firebaseio.com/v0/item/' + str(x) + '.json')
        topic = (r['title'])
        score =  str(r['score']) + " pts"
    
        # Take string of text and wrap it at 38 chars
        txt = textwrap.fill(topic, 24)

        # Get size of text
        w, h = draw.multiline_textsize(txt, bigFont)
        
        # Center Center the text
        x = (inky_display.WIDTH / 2) - (w / 2)
        y = (inky_display.HEIGHT / 2) - (h / 2)

        # Draw a backgrund rect the size of the display
        draw.rectangle((0, 0, inky_display.WIDTH, inky_display.HEIGHT), (inky_display.BLACK))

        # Draw multiline text on scren
        draw.multiline_text((x,y), txt, inky_display.WHITE, bigFont)
        draw.text((0,0), score, inky_display.RED, redBigFont)
        inky_display.set_image(img.rotate(180))
        inky_display.show()
        time.sleep(60)


while True:
    locations = getLocation()
    getHackerNews()
    getCurrentConditions()
    time.sleep(120)
    getCovid()
    time.sleep(120)
    getWeather()
    time.sleep(120)

  

