
# Whishow
![avatar](img/img1.png)


#### Whistream（微流）是基于Whisper语音识别的的在线字幕生成工具，支持rtsp/rtmp/mp4等视频流在线语音识别

## 1. whishow介绍
#### whishow（微秀）是在线音视频流播放python实现，支持rtsp/rtmp/mp4等输入，也是whistream的前端。python实现原理如下：

```python
if __name__ == "__main__":

    stm = STREAM()
    spc = SPROCESS()
    ply = PLAY()
    # url = sys.argv[1]
    url = "test.mp4"

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
        stm.read(url = "test.mp4",
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


