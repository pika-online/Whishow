############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
import av
import cv2 
import soxr 
import queue
from .utils import *

class STREAM():
    def __init__(self) -> None:
        self.pcolor = "yellow"

    def P(self,text):
        printc("%s: %s"%(self.__class__.__name__,text),self.pcolor)

    def init_state(self,
                   url:str="",
                   cache_size:int=5*60,
                   video_frame_quality:int=90,
                   AUDIO_FPS:int = 16000,
                   VIDEO_FPS:int = 30):
        """
        url: the video address to play
        cache_size: the buffer size to build audio/video cache (seconds) 
        video_frame_quality: Lower picture quality means a smaller buffer
        """
        self.running = True
        self.start_start = False
        self.stream_end = False
        self.at = 0
        self.vt = 0
        self.video_frame_quality = video_frame_quality
        self.AUDIO_FPS = AUDIO_FPS
        self.VIDEO_FPS = VIDEO_FPS
        self.init_container(url)
        self.Q_audio_asr = queue.Queue(cache_size*self.AUDIO_FPS)
        self.Q_audio_play = queue.Queue(cache_size*self.AUDIO_FPS)
        self.Q_video_play = queue.Queue(cache_size*self.VIDEO_FPS)
        self.P("Finished to init the state ..")

    def init_container(self,url):
        global VIDEO_FPS,START_STREAM
        # 打开RTSP流
        self.container = av.open(url,buffer_size=32768*10)

        # 查找视频流和音频流
        video_stream = self.container.streams.video[0]
        audio_stream = self.container.streams.audio[0]

        # 获取音频流的采样率
        self.P("=================================================")
        self.info_audio = {}
        self.info_audio['audio_sample_rate'] = audio_stream.rate
        self.info_audio['audio_channels'] = audio_stream.channels
        self.info_audio['audio_format'] = audio_stream.format.name
        for key in self.info_audio:self.P(f"{key}: {self.info_audio[key]}")
        self.P("=================================================")
        self.info_video = {}
        self.info_video['video_width'] = video_stream.width
        self.info_video['video_height'] = video_stream.height
        self.info_video['video_pixel_format'] = video_stream.format.name
        self.info_video['video_codec_name'] = video_stream.codec.name
        if not video_stream.average_rate:
            self.info_video['video_sample_rate'] = 30
        else:
            self.info_video['video_sample_rate'] = video_stream.average_rate.as_integer_ratio()
            self.info_video['video_sample_rate'] = int(self.info_video['video_sample_rate'][0]/self.info_video['video_sample_rate'][1])
        for key in self.info_video:self.P(f"{key}: {self.info_video[key]}")
        self.P("=================================================")
        print()
        VIDEO_FPS = self.info_video['video_sample_rate']
        self.P("Finished to init the container ..")

    

    def modify_video_size(self,video_src_frame_size,video_dst_frame_size):
        def finetune(size):
            return [min(size[0],video_dst_frame_size[0]),min(size[1],video_dst_frame_size[1])]
        video_mdf_frame_size = video_src_frame_size.copy()
        f = [video_src_frame_size[0]/video_dst_frame_size[0],video_src_frame_size[1]/video_dst_frame_size[1]]
        if f[0]<1 and f[1]<1:
            id = np.argmax(f)
            k = 1/f[id]
            video_mdf_frame_size = [int(video_src_frame_size[0]*k),int(video_src_frame_size[1]*k)]
            video_mdf_frame_size = finetune(video_mdf_frame_size)
        if f[0]>1 or f[1]>1:
            id = np.argmax(f)
            k = 1/f[id]
            video_mdf_frame_size = [int(video_src_frame_size[0]*k),int(video_src_frame_size[1]*k)]
            video_mdf_frame_size = finetune(video_mdf_frame_size)
        self.P(f"the the video src size is {video_src_frame_size}")
        self.P(f"the the video dst size is:{video_mdf_frame_size} under the target size:{video_dst_frame_size}")
        return video_mdf_frame_size


    def read(self,video_dst_frame_size:list=[640,320],is_play:bool=False,is_asr:bool=False):
        """
        video_dst_frame_size: the image size you want, [-1,-1] will set [W,H] = [640,320] as default.
        is_play: build the streaming for player
        is_play: build the streaming for asr
        """

        # 调整画面大小
        video_src_frame_size = [self.info_video['video_width'],self.info_video['video_height']]
        video_mdf_frame_size = self.modify_video_size(video_src_frame_size,video_dst_frame_size)

        # # 将视频和音频流写入输出文件
        s = time.time()
        video_count = 0
        audio_count = 0
        pcount = 0
       

        for packet in self.container.demux():
            if not self.running:break
            if packet.stream.type == 'audio':
                for frame in packet.decode():
                    self.at = frame.time
                    if self.start_start:
                        audio_count += 1       
                        frame = frame.to_ndarray()[0]
                        frame = soxr.resample(frame,in_rate=self.info_audio['audio_sample_rate'],out_rate=self.AUDIO_FPS)
                        frame = audio_f2i(frame,16)
                        if is_play:
                            for p in frame:self.Q_audio_play.put(p)
                        if is_asr:
                            for p in frame:self.Q_audio_asr.put(p)
                        

            if packet.stream.type == 'video':
                for frame in packet.decode():
                    self.vt = frame.time
                    if self.start_start:
                        video_count += 1
                        frame = frame.to_image()
                        frame = np.asarray(frame)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = cv2.resize(frame,video_mdf_frame_size)
                        frame= cv2.imencode('.jpg', frame,[cv2.IMWRITE_JPEG_QUALITY, self.video_frame_quality])[1]
                        if is_play:
                            self.Q_video_play.put(frame)

            pcount += 1

            if self.at>0 :
                self.start_start = True

            if(time.time()-s>1):
                self.P("SEEK(AUDIO):%s, SEEK(VIDEO):%s"%(format_timestamp(self.at),format_timestamp(self.vt)))
                self.P("Aduio(FPS):%sK, play_qsize:%s, asr_qsize:%s"%(audio_count,self.Q_audio_play.qsize(),self.Q_audio_asr.qsize()))
                self.P("Video(FPS):%s, play_qsize:%s"%(video_count,self.Q_video_play.qsize()))
                s = time.time()
                audio_count = 0
                video_count = 0
                print()

        for _ in range(30*self.AUDIO_FPS):
            self.Q_audio_play.put(0)
            self.Q_audio_asr.put(0)
        self.stream_end = True

        # 关闭容器和输出文件
        self.container.close()
        self.P("Stop to read stream ..")
        

if __name__ == "__main__":

    pass
