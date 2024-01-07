import cv2

import numpy as np
import os
from time import sleep, time
import threading
from collections import defaultdict
from multiprocessing import Process, Queue
import queue
from scipy.spatial import distance as dist

from siyi_control import SIYIControl

track_history = list()
queue_from_cam = Queue(maxsize=10)
tracker_roi = None

bbox_ROI = (0, 0, 0, 0)
bbox_old = (0, 0, 0, 0)
# Our ROI, defined by two points
state = 0
# Our ROI, defined by two points
p1, p2 = (0, 0), (0, 0)
click_point = (0, 0)

drawing = False  # True while ROI is actively being drawn by mouse
show_drawing = False  # True while ROI is drawn but is pending use or cancel

class VideoCapture:
  def __init__(self, name):
    # os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]="video_codec;hevc"
    self.cap = cv2.VideoCapture(name, cv2.CAP_FFMPEG, [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY ])
    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)

    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
        ret, frame = self.cap.read()

        # frame = cv2.resize(frame, None, fx=1, fy=1)
        if not ret:
            break
        if not self.q.empty():
            try:
                self.q.get_nowait()   # discard previous (unprocessed) frame
            except queue.Empty:
                pass
        self.q.put(frame)
          
  def read(self):
    return self.q.get()

def draw_border(img, pt1, pt2, color, thickness, r, d):
    x1,y1 = pt1
    x2,y2 = pt2

    # Top left
    cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
    cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)

    # Top right
    cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
    cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
    cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)

    # Bottom left
    cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
    cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)

    # Bottom right
    cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
    cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
    cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)

def norm_2d_points(pts):
        """
        Эта функция, norm_2d_points, предназначена для нормализации координат 2D точек. Она принимает на вход массив pts из четырех 2D точек.
        """
        # sort the points based on their x-coordinates
        xSorted = pts[np.argsort(pts[:, 0]), :]
        # grab the left-most and right-most points from the sorted
        # x-roodinate points
        leftMost = xSorted[:2, :]
        rightMost = xSorted[2:, :]

        leftMost = leftMost[np.argsort(leftMost[:, 1]), :]
        (tl, bl) = leftMost

        D = dist.cdist(tl[np.newaxis], rightMost, "euclidean")[0]
        (br, tr) = rightMost[np.argsort(D)[::-1], :]
        # return the coordinates in top-left, top-right,
        # bottom-right, and bottom-left order
        return np.array([tl,br], dtype="int16").flatten().tolist()

# Called every time a mouse event happen
def on_mouse(event, x, y, flags, userdata):
    global p1, p2, drawing, show_drawing, bbox_ROI
    if event == cv2.EVENT_LBUTTONDOWN:
        # Left click down (select first point)
        drawing = True
        show_drawing = True
        p1 = x, y
        p2 = x, y
    elif event == cv2.EVENT_MOUSEMOVE:
        # Drag to second point
        if drawing:
            p2 = x, y
    elif event == cv2.EVENT_LBUTTONUP:
        # Left click up (select second point)
        drawing = False
        p2 = x, y
    p3 = (p1[0], p2[1])
    p4 = (p2[0], p1[1])
    
    pts = np.array([p1, p2, p3, p4])
    xyx1y1= norm_2d_points(pts)
    w = int(xyx1y1[2] - xyx1y1[0])
    h = int(xyx1y1[3] - xyx1y1[1])
    bbox_ROI = (int(xyx1y1[0]), int(xyx1y1[1]), w, h)

def draw_center(frame, track_point, color=(255, 255, 255), _thickness=1):
    h, w, _ = frame.shape
    dy, dx = int(h / 2), int(w / 2)
    cv2.line(frame, (dx, 0), (dx, h), color=color, thickness=_thickness)
    cv2.line(frame, (0, dy), (w, dy), color=color, thickness=_thickness)

    if len(track_point) > 0:
        points = track_point[-1]
        print("points", points)
        cv2.line(frame, (dx, dy), points, color=color, thickness=_thickness)

def tracking_camera(frame, track_point, control, power=0.03):
    """
    Расчет смещения от трекинга
    """
    if len(track_point) == 0:
        print("len(track_point) == 0. EXIT")
        return
    h, w, _ = frame.shape
    dy, dx = int(h / 2), int(w / 2)
    points = track_point[-1]
    # Calculate diff
    offset = (dx-points[0], dy-points[1])
    print("offset", offset)
    control.set_offset(yaw_off=offset[0], pitch_offset=offset[1],power=power)


if __name__ == "__main__":
    dt = time()
    old_dt = dt
    currnt_time = time()    
    timer = 0
    is_bisy = False
    
    RTSP_URL = "rtsp://192.168.144.25:8554/main.264"
    siyi_cap = VideoCapture(RTSP_URL)
    siyi_control = SIYIControl()

    cv2.namedWindow("output", cv2.WINDOW_NORMAL)
    # Register the mouse callback
    cv2.setMouseCallback('output', on_mouse)

    while True:
        # Read opencv
        frame = siyi_cap.read()
      
        # If a ROI is selected, draw it
        if show_drawing:
            # Fix p2 to be always within the frame
            p2 = (
                0 if p2[0] < 0 else (p2[0] if p2[0] < frame.shape[1] else frame.shape[1]),
                0 if p2[1] < 0 else (p2[1] if p2[1] < frame.shape[0] else frame.shape[0])
            )
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2)

        if tracker_roi:
            ret_ot, bbox = tracker_roi.update(frame)
            if bbox_old != bbox:
                bbox_old = bbox
                # print("track", bbox)
            # Рисование ограничивающего прямоугольника
            if ret_ot:
                p1_ot = (int(bbox[0]), int(bbox[1]))
                p2_ot = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))               
                draw_border(frame, p1_ot, p2_ot, (255,170,0), 2, 10, 10)

                # draw line
                (x, y, x2, y2) = (p1_ot[0], p1_ot[1], p2_ot[0], p2_ot[1])

                center_x = int((x + x2) / 2)
                center_y = int((y + y2) / 2)
                track_history.append((int(center_x), int(center_y)))  # x, y center point
                if len(track_history) > 10:  # retain 90 tracks for 90 frames
                    track_history.pop(0)
                points = np.hstack(track_history).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [points], isClosed=False, color=(255, 255, 255), thickness=3)
                
                # draw line
                # draw_center(frame, track_history)
                # Set traking
                tracking_camera(frame, track_history, siyi_control)

            else:
                cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
        
        cv2.imshow("output", frame)

        pressed = cv2.waitKey(1)
        if pressed in [13, 32]:
            # Pressed Enter or Space to use ROI
            if tracker_roi:
                tracker_roi = None
            tracker_roi = cv2.TrackerCSRT.create()
            drawing = False
            show_drawing = False
            print("bbox", bbox_ROI)
            ret = tracker_roi.init(frame, bbox_ROI)
            track_history.clear()

            # here do something with ROI points values (p1 and p2)
        elif pressed in [ord('c'), ord('C'), 27]:
            # Pressed C or Esc to cancel ROI
            drawing = False
            show_drawing = False
            track_history.clear()
            if tracker_roi:
                tracker_roi = None
        elif pressed in [27]:
            # Pressed Esc to cancel ROI
            drawing = False
            show_drawing = False
            break
    
    cv2.destroyAllWindows()
    siyi_cap.cap.release()