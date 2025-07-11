
import time
import json
from . import consts

def now():
  return int(time.time() * 1000)
  
def get_video_info(video_id):
  with open('videos.json') as f:
    videos = json.load(f)
    for video in videos:
      if video['id']['videoId'] == video_id:
        return video
    return None

def get_video_url(video_id):
  return f'https://www.youtube.com/watch?v={video_id}'

def dumpj(data, filename):
  with open(filename, 'w') as f:
    f.write(json.dumps(data, indent=2))

def is_true(value: str) -> bool:
  return value.lower() in ['true', '1', 'y', 'yes', 'on' ]

def cost(input_tokens, output_tokens):
  return input_tokens * consts.COST_INPUT_TOKENS_1K / 1000 + output_tokens * consts.COST_OUTPUT_TOKENS_1K / 1000
