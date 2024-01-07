"""
@file test_gimbal_rotation.py
@Description: This is a test script for using the SIYI SDK Python implementation to set/get gimbal rotation
@Author: Mohamed Abdelkader
@Contact: mohamedashraf123@gmail.com
All rights reserved 2022
"""

from time import sleep
import sys
import os
from pynput.keyboard import Key, Listener
import threading

current = os.path.dirname(os.path.realpath(__file__))
parent_directory = os.path.dirname(current)
  
sys.path.append(parent_directory)

from siyi_sdk import SIYISDK

class SIYIControl:
    def __init__(self, _server_ip="192.168.144.25", _port=37260):
        
        self.zoom = 1
        self.yaw = 0
        self.pitch = 0
        self.init_flag = False


        self.cam = SIYISDK(server_ip=_server_ip, port=_port)
        if not self.cam.connect():
            print("No connection ")
            exit(1)
        print("Current motion mode: ", self.cam._motionMode_msg.mode)
        self.cam.requestFollowMode()

        _list_thread = threading.Thread(target=self.listener_tread,
                                                args=())
        
        _list_thread.start()
        sleep(1)
     
        print("Attitude (yaw,pitch,roll) eg:", self.cam.getAttitude())
        sleep(1)
        if not self.init_flag:
            att = self.cam.getAttitude()
            yaw = att[0]
            pitch = att[1]
            self.cam.setRotation(yaw,pitch)
            self.init_flag = True


    def keybord_control(self, key):
        print('\nYou Entered {0}'.format(key))
        print("type:", type(key))

        try:
            if key.char == "n" or key.char == "C": 
                print('You Pressed N Key! Center')       
                yaw = 0
                pitch = 0
                self.cam.setRotation(yaw,pitch)
                self.cam.requestCenterGimbal()

            if key.char == "e" or key.char == "E": 
                    print('You Pressed E Key! Zoom+')
                    self.zoom += 1
                    if self.zoom > 30:
                        self.zoom = 30
                    self.cam.set_zoom(self.zoom)

            if key.char == "q" or key.char == "Q": 
                print('You Pressed Q Key! Zoom-')
                self.zoom -= 1
                if self.zoom < 1:
                        self.zoom = 1
                self.cam.set_zoom(self.zoom)

            if key.char == "w" or key.char == "W": 
                print('UP')
                self.pitch += 2.0
                self.cam.setRotation(self.yaw,self.pitch)
            if key.char == "s" or key.char == "S": 
                print('Down')
                self.pitch -= 2.0
                self.cam.setRotation(self.yaw,self.pitch)
            if key.char == "d" or key.char == "D": 
                print('Right')
                self.yaw -= 2.0
                self.cam.setRotation(self.yaw,self.pitch)
            if key.char == "a" or key.char == "A": 
                print('Left')
                self.yaw += 2.0
                self.cam.setRotation(self.yaw,self.pitch)

            if key.char == "1": 
                print('FPV mode')
                self.cam.requestFPVMode()
                sleep(2)
                print("Current motion mode: ", self.cam._motionMode_msg.mode)
            if key.char == "2": 
                print('Lock mode')
                self.cam.requestLockMode()
                sleep(2)
                print("Current motion mode: ", self.cam._motionMode_msg.mode)
            if key.char == "3": 
                print('Follow mode')
                self.cam.requestFollowMode()
                sleep(2)
                print("Current motion mode: ", self.cam._motionMode_msg.mode)
            if key.char == "p" or key.char == "P": 
                print('Pick')
                self.cam.requestPhoto()
        except:
            pass

        if key == Key.delete:
            # Stop listener
            return False

    def listener_tread(self):
        with Listener(on_press = self.keybord_control) as listener:   
            listener.join()    

    def set_offset(self, yaw_off, pitch_offset, power):
        att = self.cam.getAttitude()
        self.yaw = att[0] + (yaw_off * power)
        self.pitch = att[1] + (pitch_offset * power)
        
        print("set offset", self.yaw, self.pitch)
        self.cam.setRotation(int(self.yaw), int(self.pitch))
        