############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
import cv2 
import pyaudio
from queue import Queue
from PIL import Image,ImageDraw,ImageFont
from .utils import *

current_dir_path = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = f"{current_dir_path}/NotoSansCJKsc-Regular.ttf"

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

    def init_state(self,
                   start:int=0,
                   chunk_size:int=1,
                   video_frame_shift=20,
                   audio_fps:int=16000,
                   video_fps:int=30,
                   Q_audio_play:Queue=None,
                   Q_video_play:Queue=None,
                   asr_results:list=[],
                   font_file:str=""):
        """
        start: Select the start play time (Seconds)
        chunk_size: The size of each block read on the buffer
        video_frame_shift: If processing per frame is too slow, this parameter can be reduced to improve fps (ms)
        audio_fps: Audio frame per second, offered by whishow.STREAM
        video_fps: Video frame per second, offered by whishow.STREAM
        Q_audio_play: Audio input queue, offered by whishow.STREAM
        Q_Video_play: Video input queue, offered by whishow.STREAM
        asr_results: Will play a role in title generation, format:[[start_second,end_second,asr_content],...]
        font_file: ttf files are used to display asr fonts
        """

        self.running = True
        self.AUDIO_FPS = audio_fps
        self.VIDEO_FPS = video_fps
        self.video_frame_shift = video_frame_shift
        self.Q_audio_play = Q_audio_play
        self.Q_video_play = Q_video_play
        self.asr_results = asr_results
        self.seek_a = int(start * self.AUDIO_FPS)
        self.seek_v = int(start * self.VIDEO_FPS)
        self.step_a = int(chunk_size * self.AUDIO_FPS)
        self.step_v = int(chunk_size * self.VIDEO_FPS)
        self.init_audio_driver()
        self.init_video_driver()
        self.fid = 0
        self.aid = 0
        self.vid = 0
        self.font_file = FONT_FILE if not font_file else font_file

    def init_audio_driver(self):
        self.audio_driver = pyaudio.PyAudio()
        self.audio_stream =self.audio_driver.open(format=pyaudio.paInt16,
                                                    channels=1,
                                                    rate=self.AUDIO_FPS,
                                                    output=True,
                                                    )
        
    def init_video_driver(self):
        self.win_name = "Whishow Player (ESC for exit)"


    def rewrite_video_frame(self,frame,text='[add ASR content here]',side=0.2):
        h,w,c = frame.shape
        W,H = [640,320]
        bg = np.zeros([int(H*(1+side*2)),W,c],dtype="uint8")
        H_,W_,C_= bg.shape
        s1 = (H_-h)//2
        s2 = s1+h
        t1 = (W_-w)//2
        t2 = t1 + w
        bg[s1:s2,t1:t2] = frame
        img = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        font_size = 15
        font = ImageFont.truetype(self.font_file, font_size, encoding="utf-8")
        left, top, right, bottom = draw.textbbox((0, 0), text, font)
        text_x = (W_ - (right-left)) / 2
        text_y = s2+ ( H_-s2 -(bottom-top)) / 2
        draw.text((text_x,text_y), text, (255,255,255), font=font)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)

    def search_subtitle(self,seek):
        text = ""
        for i in range(self.asr_index,len(self.asr_results)):
            s,e,t = self.asr_results[i]
            if s<=seek<=e:
                text = t
                self.asr_index = i 
                break
        return text
    
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
        self.P("Stop to play audio ..")

    def listen_video(self):
        while self.running:
            with self.vlock:
                if len(self.video_data):
                    s = time.time()
                    seek_asr = self.seek_v/self.VIDEO_FPS
                    for frame in self.video_data:
                        seek_asr += 1/self.VIDEO_FPS
                        text = self.search_subtitle(seek_asr)
                        # frame 处理
                        frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8),cv2.IMREAD_COLOR)
                        frame = self.rewrite_video_frame(frame,text)
                        #
                        cv2.imshow(self.win_name, frame)
                        key = cv2.waitKey(self.video_frame_shift)
                        
                        
                    self.P(f"listen_video -> frame[{self.vid}] -> cost:{time.time()-s}")
                    self.video_data = []
                    self.vid += 1
            time.sleep(0.001)
        self.P("Stop to play video ..")

    

    def run(self,show_subtitle=False):
        """
        show_suntitle: Whether to generate subtitles for the video. If yes, the video will be played after the recognition result appears
        """
        
        pa = threading.Thread(target=self.listen_audio,args=())
        pv = threading.Thread(target=self.listen_video,args=())
        pa.start()
        pv.start()
        self.asr_index = 0
        while 1:
            time.sleep(0.1)
            if not self.running:
                break
            if show_subtitle and not self.asr_results:continue
            if self.Q_audio_play.qsize()>=self.step_a and self.Q_video_play.qsize()>=self.step_v and\
               self.fid==self.aid==self.vid:
                
                # 播放
                chunk_a = [self.Q_audio_play.get() for _ in range(self.step_a)]
                chunk_v = [self.Q_video_play.get() for _ in range(self.step_v)]
                chunk_a = np.array(chunk_a,dtype="int16")
                # chunk_v = np.array(chunk_v,dtype="uint8")

                self.audio_data = chunk_a
                self.video_data = chunk_v
                self.P("Send the %s block data .."%self.fid)

                self.seek_a+=self.step_a
                self.seek_v+=self.step_v
                self.fid += 1
                self.P("seek(play):%s "%(format_timestamp(self.seek_v/self.VIDEO_FPS)))
            # time.sleep(0.01)
        pa.join()
        pv.join()
        self.P("========== PLAY END ==================")
        




if __name__ == "__main__":
    from whishow.stream import STREAM

    url = "rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp"
    
    # init the stream reader, named stm.
    stm = STREAM()
    stm.init_state(url=url,
                  cache_size=10*60)
    ply = PLAY()
    ply.init_state(start=0,
                    step=1,
                    audio_fps=stm.AUDIO_FPS,
                    video_fps=stm.VIDEO_FPS,
                    Q_audio_play=stm.Q_audio_play,
                    Q_video_play=stm.Q_video_play,
                    asr_results=[])

    # esc退出播放
    def engine():
        global stm,ply
        import keyboard
        while 1:
            if keyboard.is_pressed('esc'):
                print("exit ..")
                break
            time.sleep(0.1)
        stm.running = False
        ply.running = False

    def stream():
        global stm 
        stm.read(is_play=True,is_asr=False)

    def play():
        global ply
        ply.run(show_subtitle=False)

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=stream,args=())
    p2 = threading.Thread(target=play,args=())
    p0.start()
    p1.start()
    p2.start()
