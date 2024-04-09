from buffer import *
from buffer2 import *
from stream import *
import cv2 
from PIL import Image, ImageDraw, ImageFont


class SPROCESS():
    def __init__(self) -> None:
        self.audio_data = []
        self.video_data = []
        self.lock = threading.Lock()
        self.pcolor = ""
        pass

    def P(self,text):
        printc("%s: %s"%(self.__class__.__name__,text),self.pcolor)

    def init_state(self,cache_size,asr=False,step=1):
        self.audio_dst_fps = AUDIO_FPS
        self.video_dst_fps = VIDEO_FPS
        self.audio_cache_size = cache_size*self.audio_dst_fps
        self.video_cache_size = cache_size*self.video_dst_fps
        self.seek_a = 0
        self.seek_v = 0
        self.step_a = int(step * AUDIO_FPS)
        self.step_v = int(step * VIDEO_FPS)
        self.asr = asr # 添加字幕功能
        self.running = True
        
        self.aid = 0
        self.vid = 0
        init_audio2_cache(self.audio_cache_size)
        init_video2_cache(self.video_cache_size)
        self.P("Finished to init the cache ..")
    
    def terminate(self):
        with self.lock:
            return self.running


    def rewrite_video_frame(self,frame,text='[add ASR content here]',side=0.2):
        h,w,c = frame.shape
        W,H = VIDEO_FRAME_SIZE
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
        # font = ImageFont.truetype("msjh.ttc", font_size, encoding="utf-8")
        font = ImageFont.truetype("./NotoSansCJKsc-Regular.ttf", font_size, encoding="utf-8")
        
        left, top, right, bottom = draw.textbbox((0, 0), text, font)
        # text_width, text_height = draw.textsize(text)
        text_x = (W_ - (right-left)) / 2
        text_y = s2+ ( H_-s2 -(bottom-top)) / 2

        draw.text((text_x,text_y), text, (255,255,255), font=font)
        return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)


    def run(self,cache_size,asr=False,step=1):
        self.init_state(cache_size,asr=asr,step=step)

        while self.running:
            if self.seek_a+self.step_a <= get_audio_latest():
                if self.asr and not is_asr_results_empty():continue
                chunk_a = read_audio_cache(self.seek_a,self.seek_a+self.step_a)
                push_audio2_cache(chunk_a)
                self.seek_a += self.step_a
                self.aid += 1

            if self.seek_v+self.step_v <= get_video_latest():
                if self.asr and not is_asr_results_empty():continue
                chunk_v = read_video_cache(self.seek_v,self.seek_v+self.step_v)
                seek_ = self.seek_v/VIDEO_FPS
                for frame in chunk_v:
                    frame = cv2.imdecode(np.frombuffer(frame, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if self.asr:
                        text = seek_in_asr_result(seek_)
                        frame = self.rewrite_video_frame(frame,text=text)
                    push_video2_cache(frame)
                    seek_ += (1/VIDEO_FPS)
                self.seek_v += self.step_v
                self.vid += 1
            
            time.sleep(0.1)



if __name__ == "__main__":
    

    stm = STREAM()
    spc = SPROCESS()
    # esc退出播放
    def engine():
        global stm,spc
        import keyboard
        while 1:
            if keyboard.is_pressed('esc'):
                print("EXIT ..")
                break
            time.sleep(0.01)

        stm.running = False
        spc.running = False

    # 读取视频流和音频流
    def process1():
        global stm
        stm.read(url = "test.mp4",
                video_dst_frame_size=[-1,-1],
                cache_size=10*60)

    # 处理帧
    def process2():
        global spc
        while not check_stream():time.sleep(1)
        spc.run(cache_size=2*60,asr=False,step=1)

    p0 = threading.Thread(target=engine,args=())
    p1 = threading.Thread(target=process1,args=())
    p2 = threading.Thread(target=process2,args=())

    p0.start()
    p1.start()
    p2.start()

