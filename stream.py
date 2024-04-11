############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
import av
from utils import * 
import cv2 
import soxr 
from collections import deque
import queue

class STREAM():
    def __init__(self) -> None:
        self.pcolor = "yellow"

    def P(self,text):
        printc("%s: %s"%(self.__class__.__name__,text),self.pcolor)

    def init_state(self,url,cache_size):
        self.running = True
        self.start_start = False
        self.stream_end = False
        self.AUDIO_FPS = 16000
        self.VIDEO_FPS = 30
        self.init_container(url)
        self.QA = queue.Queue(cache_size*self.AUDIO_FPS)
        self.QV = queue.Queue(cache_size*self.VIDEO_FPS)
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
        print()

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
        START_STREAM = True
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


    def read(self,video_dst_frame_size=[-1,-1]):

        video_src_frame_size = [self.info_video['video_width'],self.info_video['video_height']]
        if video_dst_frame_size != [-1,-1]:
            video_mdf_frame_size = self.modify_video_size(video_src_frame_size,video_dst_frame_size)
        else:
            video_mdf_frame_size = self.modify_video_size(video_src_frame_size,[640,320])

        # # 将视频和音频流写入输出文件
        s = time.time()
        video_count = 0
        audio_count = 0
        pcount = 0
        at = 0
        wt = 0
        for packet in self.container.demux():

            if not self.running:return

            if packet.stream.type == 'audio':
                for frame in packet.decode():
                    at = frame.time
                    if self.start_start:
                        frame = frame.to_ndarray()[0]
                        frame = soxr.resample(frame,in_rate=self.info_audio['audio_sample_rate'],out_rate=self.AUDIO_FPS)
                        frame = audio_f2i(frame,16)
                        for p in frame:
                            self.QA.put(p)
                        # self.P(self.QA.qsize())
                        audio_count += 1       

            if packet.stream.type == 'video':
                for frame in packet.decode():
                    wt = frame.time
                    if self.start_start:
                        frame = frame.to_image()
                        frame = np.asarray(frame)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = cv2.resize(frame,video_mdf_frame_size)
                        frame= cv2.imencode('.jpg', frame,[cv2.IMWRITE_JPEG_QUALITY, 90])[1]
                        self.QV.put(frame)
                        # self.P(self.QV.qsize())
                        video_count += 1
            pcount += 1

            if at>0 :
                self.start_start = True

            if(time.time()-s>1):
                self.P("SEEK(AUDIO):%s, SEEK(VIDEO):%s"%(format_timestamp(at),format_timestamp(wt)))
                self.P("Aduio(FPS):%sK, QSize:%s"%(audio_count,self.QA.qsize()))
                self.P("Video(FPS):%s, QSize:%s"%(video_count,self.QV.qsize()))
                s = time.time()
                audio_count = 0
                video_count = 0
                print()

        self.stream_end = True

        # 关闭容器和输出文件
        self.container.close()

if __name__ == "__main__":

    # url = "rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp"
    url = "test.mp4"
    stm = STREAM()
    stm.init_state(url=url,cache_size=10*60)
    stm.read(video_dst_frame_size=[-1,-1])
    pass 
