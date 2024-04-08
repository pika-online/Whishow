############################################
# Author: Ephemeroptera
# Date: 2024-04-08
# Where: NanJing
############################################
import av
from utils import * 
from buffer import * 
import cv2 
import soxr 

AUDIO_FPS = 16000
VIDEO_FPS = 30


class STREAM():
    def __init__(self) -> None:
        self.pcolor = "yellow"

    def P(self,text):
        printc("%s: %s"%(self.__class__.__name__,text),self.pcolor)

    def init_cache(self,cache_size):
        self.running = True
        self.audio_dst_fps = AUDIO_FPS
        self.video_dst_fps = VIDEO_FPS
        self.audio_cache_size = cache_size*self.audio_dst_fps
        self.video_cache_size = cache_size*self.video_dst_fps
        self.video_dst_frame_size = [640,320]
        self.at = self.wt = -1
        self.start_record = False
        init_audio_cache(self.audio_cache_size)
        init_video_cache(self.video_cache_size)
        
    def modify_video_size(self,video_src_frame_size):
        def finetune(size):
            return [min(size[0],self.video_dst_frame_size[0]),min(size[1],self.video_dst_frame_size[1])]

        video_dst_frame_size = video_src_frame_size.copy()
        f = [video_src_frame_size[0]/self.video_dst_frame_size[0],video_src_frame_size[1]/self.video_dst_frame_size[1]]
        if f[0]<1 and f[1]<1:
            id = np.argmax(f)
            k = 1/f[id]
            video_dst_frame_size = [int(video_src_frame_size[0]*k),int(video_src_frame_size[1]*k)]
            video_dst_frame_size = finetune(video_dst_frame_size)
        
        if f[0]>1 or f[1]>1:
            id = np.argmax(f)
            k = 1/f[id]
            video_dst_frame_size = [int(video_src_frame_size[0]*k),int(video_src_frame_size[1]*k)]
            video_dst_frame_size = finetune(video_dst_frame_size)

        self.P(f"the the video src size is {video_src_frame_size}")
        self.P(f"the the video dst size is:{video_dst_frame_size} under the target size:{self.video_dst_frame_size}")
        return video_dst_frame_size


    def read(self,url,video_dst_frame_size=[-1,-1]):

        if video_dst_frame_size != [-1,-1]:self.video_dst_frame_size = video_dst_frame_size
        # 打开RTSP流
        container = av.open(url)

        # 查找视频流和音频流
        video_stream = container.streams.video[0]
        audio_stream = container.streams.audio[0]

        # 获取音频流的采样率
        self.P("=================================================")
        info_audio = {}
        info_audio['audio_sample_rate'] = audio_stream.rate
        info_audio['audio_channels'] = audio_stream.channels
        info_audio['audio_format'] = audio_stream.format.name
        for key in info_audio:self.P(f"{key}: {info_audio[key]}")
        print()

        info_video = {}
        info_video['video_width'] = video_stream.width
        info_video['video_height'] = video_stream.height
        info_video['video_pixel_format'] = video_stream.format.name
        info_video['video_codec_name'] = video_stream.codec.name
        info_video['video_sample_rate'] = video_stream.average_rate
        for key in info_video:self.P(f"{key}: {info_video[key]}")
        self.P("=================================================")
        print()

        video_src_frame_size = [info_video['video_width'],info_video['video_height']]
        video_frame_size = self.modify_video_size(video_src_frame_size)

        # # 将视频和音频流写入输出文件
        s = time.time()
        video_count = 0
        audio_count = 0
        for packet in container.demux():

            if not self.running:return

            if packet.stream.type == 'audio':
                for frame in packet.decode():
                    print("A:%.2f"%frame.time)
                    self.at = frame.time
                    if self.start_record:
                        frame = frame.to_ndarray()[0]
                        frame = soxr.resample(frame,in_rate=info_audio['audio_sample_rate'],out_rate=self.audio_dst_fps)
                        frame = audio_f2i(frame,16)
                        push_audio_cache(frame)
                        audio_count += 1       

            if packet.stream.type == 'video':
                for frame in packet.decode():
                    print("V:%.2f"%frame.time)
                    self.vt = frame.time
                    if self.start_record:
                        frame = frame.to_image()
                        frame = np.asarray(frame)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = cv2.resize(frame,video_frame_size,interpolation=cv2.INTER_CUBIC)
                        frame= cv2.imencode('.jpg', frame,[cv2.IMWRITE_JPEG_QUALITY, 90])[1]
                        push_video_cache(frame)
                        video_count += 1
            
            if self.at>0 :
                self.start_record = True

            if(time.time()-s>1):
                self.P("Aduio(FPS): %sK"%audio_count)
                self.P("Video(FPS): %s"%video_count)
                s = time.time()
                audio_count = 0
                video_count = 0
                print()

        # 关闭容器和输出文件
        container.close()


if __name__ == "__main__":

    stm = STREAM()
    stm.init_cache(2*60)
    # stm.read("rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp")
    stm.read("test1.mp4")
    pass 
