
# Whishow
### A python based online video streaming player
<img src="img/img1.png" width="500" height="300">

## 1. Install

    pip install whishow

## 2. Usage
<img src="img/img2.gif" width="500" height="300">

demo 1: Simple play

    cmd:
        python -m whishow <video_path_or_url>
    e.g. 
        python -m  whishow rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp

demo 2: Multithreading based stream processing and frame playback in Python
```python
    from whishow import STREAM,PLAY
    import keyboard
    import threading

    # init the stream reader, named stm.
    stm = STREAM()
    stm.init_state(url=url,
                    cache_size=10*60)
    # init the whishow player, and connect the audio/video stream of stm.
    ply = PLAY()
    ply.init_state(start=0,
                    chunk_size=1,
                    video_frame_shift=20,
                    audio_fps=stm.AUDIO_FPS,
                    video_fps=stm.VIDEO_FPS,
                    Q_audio_play=stm.Q_audio_play,
                    Q_video_play=stm.Q_video_play,
                    asr_results=[])

    # thread-0: esc for exit
    def engine():
        while 1:
            if keyboard.is_pressed('esc'):
                print("exit ..")
                break
            time.sleep(0.1)
        stm.running = False
        ply.running = False

    # thread-1: stream reader
    def stream():
        stm.read(video_dst_frame_size=video_dst_frame_size,
                is_play=True,
                is_asr=False)

    # thread-2: stream palyer
    def play():
        ply.run(show_subtitle=False)

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=stream,args=())
    p2 = threading.Thread(target=play,args=())

    p0.start()
    p1.start()
    p2.start()

    p0.join()
    p1.join()
    p2.join()
```


## 3. Contact us
605686962@qq.com
coolEphemeroptera@gmail.com


