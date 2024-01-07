"""
@file test_center_gimbal.py
@Description: This is a test script for using the SIYI SDK Python implementation to adjust zoom level
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

import sys
import os
from time import sleep
  
current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

def set_zoom(_cam, level):
    _cam.requestZoomHold()
    val = _cam.getZoomLevel()

    print("Init Zoom level: ", val, " goal:", level)

    if val > level:
        while val > level:
                _cam.requestZoomOut()
                sleep(0.1)
                val = _cam.getZoomLevel()
                print("Zoom level: ", val)
        _cam.requestZoomHold()
        return True
    else:    
        while val < level:
                _cam.requestZoomIn()
                sleep(0.1)
                val = _cam.getZoomLevel()
                print("Zoom level: ", val)
        _cam.requestZoomHold()
        return True
    
def main():
    cam = SIYISDK(server_ip="192.168.144.25", port=37260)

    if not cam.connect():
        print("No connection ")
        exit(1)
    val = cam.requestZoomOut()
    sleep(0.1)

    set_zoom(cam,4)
    # sleep(3)
    # set_zoom(cam,30)
    # sleep(1)
    # set_zoom(cam,1)

    
    cam.disconnect()

if __name__ == "__main__":
    main()