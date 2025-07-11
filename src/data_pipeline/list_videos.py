#!/usr/bin/env python3
import os
import sys
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from data_pipeline.downloader import Downloader
from googleapiclient.discovery import build

# Load .env file if it exists
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

def get_channel_info(api_key, channel_id):
  print(f'[youtube] Getting channel info for {channel_id}...')
  youtube = build('youtube', 'v3', developerKey=api_key)
  request = youtube.channels().list(
    part="id,snippet",
    id=channel_id
  )
  response = request.execute()
  if 'items' not in response or len(response['items']) == 0:
    return None
  return response['items'][0]

def get_videos(api_key, channel_id):
  
  videos = []
  next_page_token = None
  youtube = build('youtube', 'v3', developerKey=api_key)

  while True:
    request = youtube.search().list(
      part="id,snippet",
      channelId=channel_id,
      maxResults=50,  # Can retrieve a maximum of 50 videos per request
      pageToken=next_page_token,
      type="video"
    )
    response = request.execute()

    for item in response['items']:
      id = item['id']['videoId']
      title = item['snippet']['title']
      videos.append(item)

    next_page_token = response.get('nextPageToken')
    if not next_page_token:
      break

  return videos

if __name__ == '__main__':
  
  # check args
  if len(sys.argv) < 2 or 'GOOGLE_API_KEY' not in os.environ:
    sys.stderr.write('Usage: GOOGLE_API_KEY=XXXX python list_videos.py <example video id or url>')
    sys.exit(1)
  
  # get channel id
  downloader = Downloader()
  info = downloader.get_info(sys.argv[1])
  if info is None or 'channel_id' not in info:
    sys.stderr.write('[youtube] video info not found')
    sys.exit(1)
  channel_id = info['channel_id']
  print(f'[youtube] channel ID: {channel_id}')

  # get channel info
  channel_info = get_channel_info(os.environ['GOOGLE_API_KEY'], channel_id)
  with open('channel_info.json', 'w') as outfile:
    json.dump(channel_info, outfile, indent=2)

  # get videos
  videos = get_videos(os.environ['GOOGLE_API_KEY'], channel_id)
  with open('videos.json', 'w') as outfile:
    json.dump(videos, outfile, indent=2)
