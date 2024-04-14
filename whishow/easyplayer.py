import time 
import keyboard
import threading
from . import STREAM,PLAY

def player(url,video_dst_frame_size=[640,320]):
    print("ESC for exit ..")
    
    # init the stream reader, named stm.
    stm = STREAM()
    stm.init_state(url=url,
                    cache_size=10*60,
                    video_frame_quality=50)
    # init the whishow player, and connect the audio/video stream of stm.
    ply = PLAY()
    ply.init_state(chunk_size=1,
                video_frame_shift=15,
                audio_fps=stm.AUDIO_FPS,
                video_fps=stm.VIDEO_FPS,
                Q_audio_play=stm.Q_audio_play,
                Q_video_play=stm.Q_video_play,
                asr_results=[])

    # esc for exit
    def engine():
        while 1:
            if keyboard.is_pressed('esc'):
                print("exit ..")
                break
            time.sleep(0.1)
        stm.running = False
        ply.running = False

    # stream reader
    def stream():
        stm.read(video_dst_frame_size=video_dst_frame_size,
                is_play=True,
                is_asr=False)

    # stream palyer
    def play():
        ply.run()

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=stream,args=())
    p2 = threading.Thread(target=play,args=())

    p0.start()
    p1.start()
    p2.start()

    p0.join()
    p1.join()
    p2.join()

if __name__ == "__main__":

    player("rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp")