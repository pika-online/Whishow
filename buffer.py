############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
import threading
from collections import deque 
from utils import * 

LOCK_VIDEO = threading.Lock()
LOCK_AUDIO = threading.Lock()

AUDIO_BUFFER = {"start":0,
                "end":0,
                "data":[]}

VIDEO_BUFFER = {"start":0,
                "end":0,
                "data":[]}

AS = time.time()
VS = time.time()
LOG_COLOR = "red"

def init_audio_cache(audio_cache_size):
    global AUDIO_BUFFER
    AUDIO_BUFFER = {"start":-audio_cache_size,
                    "end":0,
                    "data":deque([-1]*audio_cache_size,
                                maxlen=audio_cache_size)}
    printc(f"init the audio cache with size {audio_cache_size} ..",LOG_COLOR)

def init_video_cache(video_cache_size):
    global VIDEO_BUFFER
    VIDEO_BUFFER = {"start":-video_cache_size,
                    "end":0,
                    "data":deque([-1]*video_cache_size,
                                maxlen=video_cache_size)}
    printc(f"init the video cache with size {video_cache_size} ..",LOG_COLOR)
    

def push_audio_cache(frame):
    global AUDIO_BUFFER,AS
    LOCK_AUDIO.acquire()
    AUDIO_BUFFER['start'] += len(frame)
    AUDIO_BUFFER['end'] += len(frame)
    for p in frame:
        AUDIO_BUFFER["data"].append(p)
    LOCK_AUDIO.release()
    if (time.time()-AS)>1:
        AS = time.time()
        printc(f"push_audio_cache, start:{AUDIO_BUFFER['start']}, end:{AUDIO_BUFFER['end']}",LOG_COLOR)
    
def push_video_cache(frame):
    global VIDEO_BUFFER,VS
    LOCK_VIDEO.acquire()
    VIDEO_BUFFER['start'] += 1
    VIDEO_BUFFER['end'] += 1
    VIDEO_BUFFER["data"].append(frame)
    LOCK_VIDEO.release()
    if (time.time()-VS)>1:
        VS = time.time()
        printc(f"push_audio_cache, start:{VIDEO_BUFFER['start']}, end:{VIDEO_BUFFER['end']}",LOG_COLOR)

def read_audio_cache(start,end):
    global AUDIO_BUFFER
    LOCK_AUDIO.acquire()
    tmp = list(AUDIO_BUFFER["data"])[start-AUDIO_BUFFER['start']:end-AUDIO_BUFFER['start']]
    LOCK_AUDIO.release()
    return tmp

def read_video_cache(start,end):
    global VIDEO_BUFFER
    LOCK_VIDEO.acquire()
    tmp = list(VIDEO_BUFFER["data"])[start-VIDEO_BUFFER['start']:end-VIDEO_BUFFER['start']]
    LOCK_VIDEO.release()
    return tmp

def get_audio_latest():
    global AUDIO_BUFFER
    LOCK_AUDIO.acquire()
    tmp = AUDIO_BUFFER['end']
    LOCK_AUDIO.release()
    return tmp

def get_video_latest():
    global VIDEO_BUFFER
    LOCK_VIDEO.acquire()
    tmp = VIDEO_BUFFER['end']
    LOCK_VIDEO.release()
    return tmp

