############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
import threading
from collections import deque 
from utils import * 

LOCK_VIDEO2 = threading.Lock()
LOCK_AUDIO2 = threading.Lock()

AUDIO2_BUFFER = {"start":0,
                "end":0,
                "data":[]}

VIDEO2_BUFFER = {"start":0,
                "end":0,
                "data":[]}

AS2 = time.time()
VS2 = time.time()
LOG_COLOR2 = "purple"

def init_audio2_cache(audio2_cache_size):
    global AUDIO2_BUFFER
    AUDIO2_BUFFER = {"start":-audio2_cache_size,
                    "end":0,
                    "data":deque([-1]*audio2_cache_size,
                                maxlen=audio2_cache_size)}
    printc(f"init the audio2 cache with size {audio2_cache_size} ..",LOG_COLOR2)

def init_video2_cache(video2_cache_size):
    global VIDEO2_BUFFER
    VIDEO2_BUFFER = {"start":-video2_cache_size,
                    "end":0,
                    "data":deque([-1]*video2_cache_size,
                                maxlen=video2_cache_size)}
    printc(f"init the video2 cache with size {video2_cache_size} ..",LOG_COLOR2)
    

def push_audio2_cache(frame):
    global AUDIO2_BUFFER,AS2
    LOCK_AUDIO2.acquire()
    AUDIO2_BUFFER['start'] += len(frame)
    AUDIO2_BUFFER['end'] += len(frame)
    for p in frame:
        AUDIO2_BUFFER["data"].append(p)
    LOCK_AUDIO2.release()
    if (time.time()-AS2)>1:
        AS2 = time.time()
        printc("push_audio2_cache, start:%s, end:%s"%(point2hour(AUDIO2_BUFFER['start']),
                                                     point2hour(AUDIO2_BUFFER['end'])),LOG_COLOR2)
    
def push_video2_cache(frame):
    global VIDEO2_BUFFER,VS2
    LOCK_VIDEO2.acquire()
    VIDEO2_BUFFER['start'] += 1
    VIDEO2_BUFFER['end'] += 1
    VIDEO2_BUFFER["data"].append(frame)
    LOCK_VIDEO2.release()
    if (time.time()-VS2)>1:
        VS2 = time.time()
        printc("push_video2_cache, start:%s, end:%s"%(point2hour(VIDEO2_BUFFER['start'],mode="video2"),
                                                     point2hour(VIDEO2_BUFFER['end'],mode="video2")),LOG_COLOR2)

def read_audio2_cache(start,end):
    global AUDIO2_BUFFER
    LOCK_AUDIO2.acquire()
    tmp = list(AUDIO2_BUFFER["data"])[start-AUDIO2_BUFFER['start']:end-AUDIO2_BUFFER['start']]
    LOCK_AUDIO2.release()
    return tmp

def read_video2_cache(start,end):
    global VIDEO2_BUFFER
    LOCK_VIDEO2.acquire()
    tmp = list(VIDEO2_BUFFER["data"])[start-VIDEO2_BUFFER['start']:end-VIDEO2_BUFFER['start']]
    LOCK_VIDEO2.release()
    return tmp

def get_audio2_latest():
    global AUDIO2_BUFFER
    LOCK_AUDIO2.acquire()
    tmp = AUDIO2_BUFFER['end']
    LOCK_AUDIO2.release()
    return tmp

def get_video2_latest():
    global VIDEO2_BUFFER
    LOCK_VIDEO2.acquire()
    tmp = VIDEO2_BUFFER['end']
    LOCK_VIDEO2.release()
    return tmp

