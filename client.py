import sys
import os
import time

import requests
from io import BytesIO
from PIL import Image

import traceback
import logging

libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "lib")
if os.path.exists(libdir):
  sys.path.append(libdir)

from waveshare_epd import epd5in0

from config import SERVER_HOST, COURTROOM_CODE, POLL_INTERVAL_SECONDS

API_BASE_URL = f"{SERVER_HOST}/api"
STATE_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "last_schedule_url.txt")

def fetch_courtroom(code):
  url = f"{API_BASE_URL}/Courtroom/{code}"
  
  try:
    response = requests.get(url, timeout=5)
  except requests.exceptions.RequestException as e:
    logging.info(f"Request failed: {e}")
    return None

  body = response.json()
  if not body.get("success"):
    logging.info(f"API error: {body.get('error')}")
    return None

  return body["data"]["courtroom"]

def fetch_image(url):
  try:
    response = requests.get(url, timeout=10)
  except requests.exceptions.RequestException as e:
    logging.info(f"Image request failed: {e}")
    return None

  if response.status_code != 200:
    logging.info(f"Unexpected status code for image request: {response.status_code}")
    return None

  return Image.open(BytesIO(response.content))

def get_last_schedule_url():
  if not os.path.exists(STATE_FILE):
    return None
  with open(STATE_FILE, "r") as f:
    content = f.read().strip()
  return content if content else None

def set_last_schedule_url(url):
  with open(STATE_FILE, "w") as f:
    f.write(url)

def display_clear(epd):
  logging.info("clearing...")
  epd.Clear()

def display_image(epd, image):
  rotated = image.rotate(270, expand=True)
  resized = rotated.resize((epd.width, epd.height)).convert("1")
  logging.info("drawing image...")
  epd.display(epd.getbuffer(resized))

def poll(epd):
  courtroom = fetch_courtroom(COURTROOM_CODE)
  if courtroom is None:
    return
  
  last_url = get_last_schedule_url()
  current_url = courtroom.get("currentScheduleUrl")
  if current_url == last_url:
    return
  
  logging.info("initializing...")
  epd.init()

  if not current_url:
    set_last_schedule_url("")
    display_clear(epd)
  else:
    set_last_schedule_url(current_url)
    image = fetch_image(f"{SERVER_HOST}{current_url}")
    if image:
      display_image(epd, image)
    else:
      display_clear(epd)

  logging.info("goto sleep...")
  epd.sleep()

logging.basicConfig(level=logging.DEBUG)

try:
  epd = epd5in0.EPD()
  
  while True:
    poll(epd)
    logging.info(f"next poll after {POLL_INTERVAL_SECONDS} seconds")
    time.sleep(POLL_INTERVAL_SECONDS)

except IOError as e:
  logging.info(e)

except KeyboardInterrupt:
  logging.info("ctrl + c:")
  epd5in0.epdconfig.module_exit(cleanup=True)
  exit()
