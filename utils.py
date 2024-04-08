import wave 
import numpy as np
import os 
import json 
import yaml 
import time 
import threading
import shutil 
import sys 

ENGINE = True 
MUTE_UTILS = threading.Lock()


def read_wavfile(path):
    with wave.open(path, 'r') as wav_file:
        params = wav_file.getparams()
        print(params)
        nchannels, sampwidth, framerate, nframes = params[:4]
        str_data = wav_file.readframes(nframes)
        wave_data = np.frombuffer(str_data, dtype=np.int16)
        if nchannels > 1:
            wave_data.shape = -1, nchannels
            wave_data = wave_data.T
        print("success to read wavfile:%s .."%path)
        return wave_data

def save_wavfile(path,wave_data):
    with wave.open(path, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(wave_data.tobytes())
    print("success to save wavfile:%s .."%path)


def cutting_wavfile(in_file,out_dir,chunk_sencond=30,sr=16000):
    os.system("rm -rf %s && mkdir -p %s"%(out_dir,out_dir))
    wave_data = read_wavfile(in_file)
    chunk_size = chunk_sencond*sr
    chunk_count = len(wave_data)//chunk_size
    last_chunk_size = len(wave_data)%chunk_size
    padding_size = chunk_size - last_chunk_size
    wave_data = np.pad(wave_data,((0,padding_size)),'constant').copy()
    print("chunk_size:%s, chunk_count:%s"%(chunk_size,chunk_count+1))
    for i in range(chunk_count+1):
        sub = wave_data[i*chunk_size:(i+1)*chunk_size].copy()
        path = "%s/S_%08d.wav"%(out_dir,i)
        save_wavfile(path,sub)
        # print("cutting wavfile:%s .."%path)
    pass


def printc(s, color="", ):
    if color == 'red':
        print("\033[31m" + s + "\033[0m")
    elif color == 'green':
        print("\033[32m" + s + "\033[0m")
    elif color == 'yellow':
        print("\033[33m" + s + "\033[0m")
    elif color == 'blue':
        print("\033[34m" + s + "\033[0m")
    elif color == 'purple':
        print("\033[35m" + s + "\033[0m")
    elif color == 'bbule':
        print("\033[36m" + s + "\033[0m")
    else:
        print(s)

def point2hour(point,mode="audio"):
    if mode=="audio":
        s = point//16000
        ms = (point%16000)/16000
    else:
        s = point//30
        ms = (point%30)/30
    h = s//3600
    m = (s-h*3600)//60
    s = s%60
    return "%02d:%02d:%02d,%03d"%(h,m,s,ms)

def json_io(file,mode="read",inp=""):
    if mode=='read':
        f = open(file, "rt",encoding="utf-8")
        data = json.load(f)
        f.close()
        return data
    else:
        s = json.dumps(inp,ensure_ascii=False)
        f = open(file, 'wt',encoding="utf-8")
        f.write(s)
        f.close()
        return True

def load_config(path=""):
    f = open(path, encoding='utf-8')
    cfg = yaml.full_load(f)
    return cfg


def CHECK_ENGINE():
    global ENGINE
    MUTE_UTILS.acquire()
    res = ENGINE
    MUTE_UTILS.release()
    return res

def OPEN_ENGINE():
    global ENGINE
    MUTE_UTILS.acquire()
    ENGINE = True
    MUTE_UTILS.release()

def CLOSE_ENGINE():
    global ENGINE
    MUTE_UTILS.acquire()
    ENGINE = False
    MUTE_UTILS.release()

def delete_non_empty_directory(directory_path):
    shutil.rmtree(directory_path)

def audio_f2i(data,width):
    return np.int16(data*(2**(width-1)))