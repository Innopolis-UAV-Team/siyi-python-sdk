# siyi-python-sdk
Python implementation of SIYI SDK for communication with ZR10 and A8 Mini cameras

* Camera webpage: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/overview/
* Documentation: http://en.siyi.biz/en/Gimbal%20Camera/ZR10/download/

Repo based on this repo: https://github.com/mzahana/siyi_sdk.git

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/yTnAmtcHlzc/0.jpg)](https://www.youtube.com/watch?v=yTnAmtcHlzc)


# Setup
* Clone this package
    ```bash
    git clone git@github.com:Innopolis-UAV-Team/siyi-python-sdk.git
    ```
* Connect the camera to PC or onboard computer using the ethernet cable that comes with it. The current implementation uses UDP communication.
* Power on the camera
* Do the PC wired network configuration. Make sure to assign a manual IP address to your computer
  * For example, IP `192.168.144.12`
  * Gateway `192.168.144.25`
  * Netmask `255.255.255.0`
* Done. 

# Usage
* Check the scripts in the `siyi_sdk/examples` directory to learn how to use the SDK

* To import this module in your code, copy the `siyi_sdk.py` `siyi_message.py` `utility.py` `crc16_python.py` scripts in your code directory, and import as follows, and then follow the test examples
    ```python
    from siyi_sdk import SIYISDK
    ```
* Example: To run the `test_gimbal_rotation.py` run,
    ```bash
    cd siyi_sdk/tests
    python3 test_gimbal_rotation.py
    ```
# Video Streaming
## Requirements
* OpenCV `sudo apt-get install python3-opencv -y`
* imutils `pip install imutils`
* Gstreamer `https://gstreamer.freedesktop.org/documentation/installing/index.html?gi-language=c`
    
    Ubuntu:
    ```bash
    sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio -y
    ```
- Deepstream (only for Nvidia Jetson boards)
    (https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html#jetson-setup)
- For RTMP streaming
    ```bash
    sudo apt install ffmpeg -y
    pip install ffmpeg-python
    ```

## Examples
* An example of how to auto tracjing with Yolov8 and CV2 tracket to0, see `examples/ml_object_tracker.py`
* An example of how to auto tracjing with CV2 tracket, see `examples/object_tracker.py`
* An example of gimbal contol, see `examples/gimbal_control.py`

# Tools
* To run a nginx-rtmp server from a docker container 
```bash
docker run -d -p 1935:1935 --name nginx-rtmp tiangolo/nginx-rtmp
```
[Reference](https://hub.docker.com/r/tiangolo/nginx-rtmp/)

* To play an rtmp stream, you can use the following command in a terminal (you will need to install mpv `sudo apt install mpv`)
```bash
mpv   --msg-color=yes   --msg-module=yes   --keepaspect=yes   --no-correct-pts   --untimed   --vd-lavc-threads=1   --cache=no   --cache-pause=no   --demuxer-lavf-o-add="fflags=+nobuffer+fastseek+flush_packets"   --demuxer-lavf-probe-info=nostreams   --demuxer-lavf-analyzeduration=0.1   --demuxer-max-bytes=500MiB   --demuxer-readahead-secs=0.1     --interpolation=no   --hr-seek-framedrop=no   --video-sync=display-resample   --temporal-dither=yes   --framedrop=decoder+vo     --deband=no   --dither=no     --hwdec=auto-copy   --hwdec-codecs=all     --video-latency-hacks=yes   --profile=low-latency   --linear-downscaling=no   --correct-downscaling=yes   --sigmoid-upscaling=yes   --scale=ewa_hanning   --scale-radius=3.2383154841662362   --cscale=ewa_lanczossoft   --dscale=mitchell     --fs   --osc=no   --osd-duration=450   --border=no   --no-pause   --no-resume-playback   --keep-open=no   --network-timeout=0 --stream-lavf-o=reconnect_streamed=1   rtmp://127.0.0.1/live/webcam
```
**OR you can use VLC, but you may notice high latency!**
