from time import sleep
import sys
import os
from pynput.keyboard import Key, Listener
import threading

current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

zoom = 1
yaw = 0
pitch = 0
init_flag = False

def keybord_control(key):
    global cam, zoom, yaw, pitch
    print('\nYou Entered {0}'.format(key))
    print("type:", type(key))

    try:
        if key.char == "n" or key.char == "C": 
            print('You Pressed N Key! Center')       
            yaw = 0
            pitch = 0
            cam.setRotation(yaw,pitch)
            cam.requestCenterGimbal()

        if key.char == "e" or key.char == "E": 
                print('You Pressed E Key! Zoom+')
                zoom += 1
                if zoom > 30:
                    zoom = 30
                cam.set_zoom(zoom)

        if key.char == "q" or key.char == "Q": 
            print('You Pressed Q Key! Zoom-')
            zoom -= 1
            if zoom < 1:
                    zoom = 1
            cam.set_zoom(zoom)

        if key.char == "w" or key.char == "W": 
            print('UP')
            pitch += 2.0
            cam.setRotation(yaw,pitch)
        if key.char == "s" or key.char == "S": 
            print('Down')
            pitch -= 2.0
            cam.setRotation(yaw,pitch)
        if key.char == "d" or key.char == "D": 
            print('Right')
            yaw -= 2.0
            cam.setRotation(yaw,pitch)
        if key.char == "a" or key.char == "A": 
            print('Left')
            yaw += 2.0
            cam.setRotation(yaw,pitch)

        if key.char == "1": 
            print('FPV mode')
            cam.requestFPVMode()
            sleep(2)
            print("Current motion mode: ", cam._motionMode_msg.mode)
        if key.char == "2": 
            print('Lock mode')
            cam.requestLockMode()
            sleep(2)
            print("Current motion mode: ", cam._motionMode_msg.mode)
        if key.char == "3": 
            print('Follow mode')
            cam.requestFollowMode()
            sleep(2)
            print("Current motion mode: ", cam._motionMode_msg.mode)
        if key.char == "p" or key.char == "P": 
            print('Pick')
            cam.requestPhoto()
    except:
         pass

    if key == Key.delete:
        # Stop listener
        return False

def listener_tread():
    with Listener(on_press = keybord_control) as listener:   
        listener.join()    

if __name__ == "__main__":
    cam = SIYISDK(server_ip="192.168.144.25", port=37260)
    if not cam.connect():
        print("No connection ")
        exit(1)
    print("Current motion mode: ", cam._motionMode_msg.mode)
    cam.requestFollowMode()

    _list_thread = threading.Thread(target=listener_tread,
                                            args=())
    
    _list_thread.start()
    sleep(1)
    while True:
        print("Attitude (yaw,pitch,roll) eg:", cam.getAttitude())
        sleep(1)
        if not init_flag:
            att = cam.getAttitude()
            yaw = att[0]
            pitch = att[1]
            cam.setRotation(yaw,pitch)
            init_flag = True
