############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
from utils import * 
from buffer import * 
from buffer2 import * 
from stream_process import *
from stream import * 
import cv2 
import pyaudio
from PIL import Image, ImageDraw, ImageFont

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

    def init_state(self,start=0,step=1):
        self.running = True
        self.seek_a = int(start * AUDIO_FPS)
        self.seek_v = int(start * VIDEO_FPS)
        self.step_a = int(step * AUDIO_FPS)
        self.step_v = int(step * VIDEO_FPS)
        self.init_audio_driver()
        self.init_video_driver()
        self.fid = 0
        self.aid = 0
        self.vid = 0


    def init_audio_driver(self):
        self.audio_driver = pyaudio.PyAudio()
        self.audio_stream =self.audio_driver.open(format=pyaudio.paInt16,
                                                    channels=1,
                                                    rate=AUDIO_FPS,
                                                    output=True,
                                                    )
        
    def init_video_driver(self):
        self.win_name = "Whishow Player"
        self.frame_wait = 20
        pass


    def listen_audio(self):
        while self.running:
            with self.alock:
                if self.audio_data:
                    s = time.time()
                    self.audio_stream.write(self.audio_data)
                    self.P(f"listen_audio -> frame[{self.aid}] -> cost:{time.time()-s}")
                    self.audio_data = []
                    self.aid += 1
            time.sleep(0.001)
            

    def listen_video(self):
        while self.running:
            with self.vlock:
                if self.video_data:
                    s = time.time()
                    for frame in self.video_data:
                        cv2.imshow(self.win_name, frame)
                        key = cv2.waitKey(self.frame_wait)
                    self.P(f"listen_video -> frame[{self.vid}] -> cost:{time.time()-s}")
                    self.video_data = []
                    self.vid += 1
            time.sleep(0.001)

    

    def run(self):
        pa = threading.Thread(target=self.listen_audio,args=())
        pv = threading.Thread(target=self.listen_video,args=())
        pa.start()
        pv.start()
        while self.running:
            if self.seek_a+self.step_a<=get_audio2_latest() and \
                self.seek_v+self.step_v<=get_video2_latest() and\
                self.fid==self.aid==self.vid:
                chunk_a = read_audio2_cache(self.seek_a,self.seek_a+self.step_a)
                chunk_v = read_video2_cache(self.seek_v,self.seek_v+self.step_v)
                chunk_a = np.array(chunk_a,dtype="int16").tobytes()
                self.audio_data = chunk_a
                self.video_data = chunk_v
                self.P("Send the %s block data .."%self.fid)
                self.seek_a+=self.step_a
                self.seek_v+=self.step_v
                self.fid += 1
            time.sleep(0.001)
        self.P("========== PLAY END ==================")
        



if __name__ == "__main__":

    stm = STREAM()
    spc = SPROCESS()
    ply = PLAY()
    # url = sys.argv[1]
    url = "test.mp4"
    url = "rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp"

    # 线程1：esc退出播放
    def engine():
        global ply
        import keyboard
        while 1:
            if keyboard.is_pressed('esc'):
                break
            time.sleep(0.01)
        stm.running = False
        spc.running = False
        ply.running = False

    # 线程2：读取视频流和音频流 （保存一级cache）
    def process1():
        global stm
        stm.read(url = url,
                video_dst_frame_size=[-1,-1],
                cache_size=10*60)

    # 线程2：处理帧（保存二级cache）
    def process2():
        global spc
        while not check_stream():time.sleep(1)
        spc.run(cache_size=2*60,asr=False,step=1)

    # 播放视频 （播放二级cache）
    def process3():
        global ply
        while not check_stream():time.sleep(1)
        ply.init_state(start=0,step=1)
        ply.run()

    

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=process1,args=())
    p2 = threading.Thread(target=process2,args=())
    p3 = threading.Thread(target=process3,args=())

    p0.start()
    p1.start()
    p2.start()
    p3.start()
