############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
from utils import * 
from buffer import * 
from stream import * 
import cv2 
import pyaudio
from pydub.playback import play

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
                                            output=True)
        
    def init_video_driver(self):
        self.win_name = "frame"
        self.frame_wait = 30
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
                        frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
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
            if self.seek_a+self.step_a<=get_audio_latest() and \
                self.seek_v+self.step_v<=get_video_latest() and\
                self.fid==self.aid==self.vid:
                chunk_a = read_audio_cache(self.seek_a,self.seek_a+self.step_a)
                chunk_v = read_video_cache(self.seek_v,self.seek_v+self.step_v)
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
    ply = PLAY()
    url = sys.argv[1]

    # 读取视频流和音频流
    def process1():
        global stm
        stm.init_cache(2*60)
        stm.read(url)

    # 播放视频
    def process2():
        global ply
        ply.init_state(0,1)
        ply.run()

    # esc退出播放
    def engine():
        global ply
        import keyboard
        while 1:
            if keyboard.is_pressed('esc'):
                break
            time.sleep(0.01)
        stm.running = False
        ply.running = False

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=process1,args=())
    p2 = threading.Thread(target=process2,args=())

    p0.start()
    p1.start()
    p2.start()
    pass 