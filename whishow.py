############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
from utils import * 
from sprocess import *
import cv2 
import pyaudio
import multiprocessing as mp


class PLAY():
    def __init__(self) -> None:
        self.audio_data = []
        self.video_data = []
        self.alock = threading.Lock()
        self.vlock = threading.Lock()
        self.pcolor = "green"
        pass

    def P(self,text):
        printc("%s: %s"%(self.__class__.__name__,text),self.pcolor)

    def init_state(self,start=0,step=1,audio_fps=16000,video_fps=30):
        self.running = True
        self.AUDIO_FPS = audio_fps
        self.VIDEO_FPS = video_fps

        self.seek_a = int(start * self.AUDIO_FPS)
        self.seek_v = int(start * self.VIDEO_FPS)
        self.step_a = int(step * self.AUDIO_FPS)
        self.step_v = int(step * self.VIDEO_FPS)
        self.init_audio_driver()
        self.init_video_driver()
        self.fid = 0
        self.aid = 0
        self.vid = 0

    def init_audio_driver(self):
        self.audio_driver = pyaudio.PyAudio()
        self.audio_stream =self.audio_driver.open(format=pyaudio.paInt16,
                                                    channels=1,
                                                    rate=self.AUDIO_FPS,
                                                    output=True,
                                                    )
        
    def init_video_driver(self):
        self.win_name = "Whishow Player"
        self.frame_wait = 20

    def listen_audio(self):
        while self.running:
            with self.alock:
                if len(self.audio_data):
                    s = time.time()
                    self.audio_stream.write(self.audio_data.tobytes())
                    self.P(f"listen_audio -> frame[{self.aid}] -> cost:{time.time()-s}")
                    self.audio_data = []
                    self.aid += 1
            time.sleep(0.001)
            

    def listen_video(self):
        while self.running:
            with self.vlock:
                if len(self.video_data):
                    s = time.time()
                    for frame in self.video_data:
                        cv2.imshow(self.win_name, frame)
                        key = cv2.waitKey(self.frame_wait)
                        
                    self.P(f"listen_video -> frame[{self.vid}] -> cost:{time.time()-s}")
                    self.video_data = []
                    self.vid += 1
            time.sleep(0.001)

    

    def run(self,spc:SPROCESS):
        ps = threading.Thread(target=spc.run,args=())
        pa = threading.Thread(target=self.listen_audio,args=())
        pv = threading.Thread(target=self.listen_video,args=())
        ps.start()
        pa.start()
        pv.start()
        while 1:
            if not self.running:
                spc.running = False
                break

            if spc.QA.qsize()>=self.step_a and spc.QV.qsize()>=self.step_v and self.fid==self.aid==self.vid:
            #    self.fid==self.aid==self.vid:
                # 播放
                chunk_a = [spc.QA.get() for _ in range(self.step_a)]
                chunk_v = [spc.QV.get() for _ in range(self.step_v)]
                chunk_a = np.array(chunk_a,dtype="int16")
                chunk_v = np.array(chunk_v,dtype="uint8")

                self.audio_data = chunk_a
                self.video_data = chunk_v
                self.P("Send the %s block data .."%self.fid)

                self.seek_a+=self.step_a
                self.seek_v+=self.step_v
                self.fid += 1
                self.P("seek(play):%s "%(format_timestamp(self.seek_v/self.VIDEO_FPS)))
            time.sleep(0.01)
        self.P("========== PLAY END ==================")
        




if __name__ == "__main__":

    url = "rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp"
    url = "test.mp4"
    url = sys.argv[1]
    
    spc = SPROCESS()
    spc.init_state(url=url,cache_size=10*60,step=1)
    ply = PLAY()
    ply.init_state(step=1,audio_fps=spc.AUDIO_FPS,video_fps=spc.VIDEO_FPS)

    # esc退出播放
    def engine():
        global ply
        import keyboard
        while 1:
            if keyboard.is_pressed('esc'):
                print("exit ..")
                break
            time.sleep(0.1)
        spc.running = False
        ply.running = False

    def play():
        global ply,spc
        ply.run(spc)

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=play,args=())
    p0.start()
    p1.start()
