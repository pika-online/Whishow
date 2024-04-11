from utils import * 
from stream import STREAM
import cv2 
from PIL import Image, ImageDraw, ImageFont
import multiprocessing as mp
import queue 

class SPROCESS():
    def __init__(self) -> None:
        self.pcolor = "blue"

    def P(self,text):
        printc("%s: %s"%(self.__class__.__name__,text),self.pcolor)

    def init_state(self,url,cache_size,step=1):
        self.running = True
        self.stream = STREAM()
        self.stream.init_state(url=url,cache_size=cache_size)
        self.AUDIO_FPS = self.stream.AUDIO_FPS
        self.VIDEO_FPS = self.stream.VIDEO_FPS
        self.QA = queue.Queue(cache_size*self.AUDIO_FPS)
        self.QV = queue.Queue(cache_size*self.VIDEO_FPS)
        self.seek_a = 0
        self.step_a = step*self.AUDIO_FPS
        self.seek_v = 0
        self.step_v = step*self.VIDEO_FPS
        
        self.P("Finished to init the state ..")

            
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
        font = ImageFont.truetype("./NotoSansCJKsc-Regular.ttf", font_size, encoding="utf-8")
        left, top, right, bottom = draw.textbbox((0, 0), text, font)
        text_x = (W_ - (right-left)) / 2
        text_y = s2+ ( H_-s2 -(bottom-top)) / 2
        draw.text((text_x,text_y), text, (255,255,255), font=font)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    
    def process_audio(self):
        while not self.stream.stream_end:
            if not self.running:
                self.stream.running = False
                break

            if self.stream.QA.qsize()>=self.step_a:
                for _ in range(self.step_a):
                    self.QA.put(self.stream.QA.get())
                self.seek_a += self.step_a
                self.P("Process(AUDIO):%s, QSize:%s"%(format_timestamp(self.seek_a/self.AUDIO_FPS),self.QA.qsize()))

            time.sleep(0.1)

    def process_video(self):
        while not self.stream.stream_end:
            if not self.running:
                self.stream.running = False
                break

            if self.stream.QV.qsize()>=self.step_v:
                for _ in range(self.step_v):
                    frame = self.stream.QV.get()
                    frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8),cv2.IMREAD_COLOR)
                    frame = self.rewrite_video_frame(frame)
                    self.QV.put(frame)
                self.seek_v += self.step_v
                self.P("Process(VIDEO):%s, QSize:%s"%(format_timestamp(self.seek_v/self.VIDEO_FPS),self.QV.qsize()))

            time.sleep(0.1)

    def run(self,video_dst_frame_size=[-1,-1]):
        ps = threading.Thread(target=self.stream.read,args=(video_dst_frame_size,))
        pa = threading.Thread(target=self.process_audio,args=())
        pu = threading.Thread(target=self.process_video,args=())
        ps.start()
        pa.start()
        pu.start()



if __name__ == "__main__":

    url = "rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp"
    url = "test.mp4"
    spc = SPROCESS()
    spc.init_state(url=url,cache_size=10*60,step=1)
    spc.run()
