#!/usr/bin/env python3
import os
import json
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core import consts
from core import utils
from core.config import Config
from legacy.agents.load_faiss import LoaderFAISS
from data_pipeline.metadata_enhancer import MetadataEnhancer

def main():

  # init
  config = Config(consts.CONFIG_PATH)
  loader = LoaderFAISS(config)
  enhancer = MetadataEnhancer()

  # print config
  print(f'[loader] embeddings model = {config.embeddings_model()}')
  print(f'[loader] splitter size/overlap = {config.split_chunk_size()}/{config.split_chunk_overlap()}')
  utils.dumpj({
    'embeddings_model': config.embeddings_model(),
    'split_chunk_size': config.split_chunk_size(),
    'split_chunk_overlap': config.split_chunk_overlap(),
  }, 'db_config.json')

  # track loaded
  loaded = []
  if os.path.exists(config.db_persist_directory()) and os.path.exists('loaded.json'):
    loaded = json.load(open('loaded.json'))

  # iterate on captions files
  subset_only=False
  all_files = [f for f in os.listdir('captions') if 'cleaned' in f and f not in loaded and (not subset_only or f.startswith('_'))]
  all_files.sort()

  # load
  index = 0
  for filename in all_files:
    
    # init
    index += 1
    video_id = filename.split('.')[0]

    # find title
    metadata = {
      'title': 'Unknown',
      'description': 'Unknown',
      'url': utils.get_video_url(video_id),
      'source': video_id,
      'video_id': video_id,
      'has_captions': True,  # We know this has captions since we're loading from captions folder
    }
    video = utils.get_video_info(video_id)
    if video is not None:
      metadata['title'] = video['snippet']['title']
      metadata['description'] = video['snippet']['description']
      metadata['published_at'] = video['snippet'].get('publishedAt', '')
      metadata['channel_id'] = video['snippet'].get('channelId', '')
      metadata['channel_title'] = video['snippet'].get('channelTitle', '')
      # Get duration from contentDetails if available
      if 'contentDetails' in video and 'duration' in video['contentDetails']:
        duration_str = video['contentDetails']['duration']
        # Parse ISO 8601 duration (PT10M23S) to seconds
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
          hours = int(match.group(1) or 0)
          minutes = int(match.group(2) or 0) 
          seconds = int(match.group(3) or 0)
          metadata['duration'] = hours * 3600 + minutes * 60 + seconds

    # load
    try:
    
      # read content
      with open(f'captions/{filename}') as f:
        content = f.read()
      
      # enhance metadata with content for quality scoring
      metadata['content'] = content
      enhanced_metadata = enhancer.enhance_metadata(metadata)
      # Remove content from metadata after enhancement (we don't want to store it twice)
      enhanced_metadata.pop('content', None)
      
      # do it
      print(f'[loader][{index}/{len(all_files)}] adding {video_id} to database...')
      print(f'  Category: {enhanced_metadata.get("category", "unknown")}')
      print(f'  Quality: {enhanced_metadata.get("quality_score", "unknown")}')
      loader.add_text(content, enhanced_metadata)
    
      # update index
      loaded.append(filename)
      json.dump(loaded, open('loaded.json', 'w'), indent=2)
    
    except Exception as e:
      print(f'[loader] error adding {video_id} to database: {e}')
      continue

if __name__ == '__main__':
  main()