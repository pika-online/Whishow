# Whishow
![avatar](img/img1.png)

#### Whistream（微流）是基于Whisper语音识别的的在线字幕生成工具，支持rtsp/rtmp/mp4等视频流在线语音识别

## 1. whishow介绍
#### whishow（微秀）是在线音视频流播放python实现，支持rtsp/rtmp/mp4等输入，也是whistream的前端。基本实现原理如下：

  1. 线程1： 使用pyav和opencv在线读取音视频帧（参考stream.py）
  2. 音视频帧会进行缓存到buffer（参考buffer.py）
  3. 线程2： 使用pyaudio和opencv 并行播放buffer上的视频帧和音频波点 （参考whishow.py）

exe下载地址：



## 2. 使用

python：

    python whishow.py <视频路径>
    例1：python whishow.py ./test.mp4
    例2：python whishow.py rtmp://mobliestream.c3tv.com:554/live/goodtv.sdp

命令行：

    ./whishow.exe <视频路径>

显示如下：
![avatar](img/img2.png)

## 3. 联系我们
605686962@qq.com
coolEphemeroptera@gmail.com


