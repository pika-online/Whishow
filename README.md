
# Whishow
![avatar](img/img1.png)


#### Whistream（微流）是基于Whisper语音识别的的在线字幕生成工具，支持rtsp/rtmp/mp4等视频流在线语音识别

## 1. whishow介绍
#### whishow（微秀）是python实现的在线音视频流播放器，支持rtsp/rtmp/mp4等流式输入，也是whistream的前端。python实现原理如下：

(1) SPROCESS.run() 的三个子线程负责：缓存流数据，处理音频缓存生成二级缓存，处理视频缓存生成二级缓存
```python
def run(self,video_dst_frame_size=[-1,-1]):
    ps = threading.Thread(target=self.stream.read,args=(video_dst_frame_size,))
    pa = threading.Thread(target=self.process_audio,args=())
    pu = threading.Thread(target=self.process_video,args=())
    ps.start()
    pa.start()
    pu.start()

```
(2) PLAY.run()对上述二级缓存进行在线播放
```python
def run(self,spc:SPROCESS):
    ps = threading.Thread(target=spc.run,args=())
    pa = threading.Thread(target=self.listen_audio,args=())
    pv = threading.Thread(target=self.listen_video,args=())
    ps.start()
    pa.start()
    pv.start()
```
exe下载地址：https://github.com/coolEphemeroptera/Whishow/releases

#### whistream将在whishow基础上引入whisper进行在线语音识别生成视频字幕


## 2. 使用

python：

    python whishow.py <视频路径>
    例1：python whishow.py ./test.mp4
    例2：python whishow.py rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp

命令行：

    ./whishow.exe <视频路径>

显示如下：
![avatar](img/img2.gif)

## 3. 联系我们
605686962@qq.com
coolEphemeroptera@gmail.com


