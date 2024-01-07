import cv2
from ultralytics import YOLO
import numpy as np
import cv2
import os
from time import sleep, time
import threading
from collections import defaultdict
from multiprocessing import Process, Queue
from siyi_control import SIYIControl
from scipy.spatial import distance as dist

import queue

class Track_Object:
   def __init__(self) -> None:      
      self.xyxy = [0, 0, 0, 0]
      self._xywh = [0, 0, 0, 0]
      self.name = ""
      self.centerPoint = []
      self.class_id = -1
      self.track_id = -1

   def xywh(self):
      w = int(self.xyxy[2] - self.xyxy[0])
      h = int(self.xyxy[3] - self.xyxy[1])
      self._xywh = (int(self.xyxy[0]), int(self.xyxy[1]), w, h)
      return self._xywh
   
class VideoCapture:

  def __init__(self, name):
    
    self.cap = cv2.VideoCapture(name, cv2.CAP_FFMPEG, [cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY])
    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 10)

    self.q = queue.Queue()
    t = threading.Thread(target=self._reader)
    t.daemon = True
    t.start()

  # read frames as soon as they are available, keeping only most recent one
  def _reader(self):
    while True:
      ret, frame = self.cap.read()
      # frame = cv2.resize(frame, None, fx=0.6, fy=0.6)
      if not ret:
        break
      if not self.q.empty():
        try:
          self.q.get_nowait()   # discard previous (unprocessed) frame
        except queue.Empty:
          pass
      self.q.put(frame)
  def read(self):
    print("qsize", self.q.qsize())
    return self.q.get()
  


model = YOLO('yolov8m.pt')

ml_results = None
track_history_ml = defaultdict(lambda: [])
track_history = list()

is_click = False
selected_point = None
drawing = False  # True while ROI is actively being drawn by mouse
show_drawing = False  # True while ROI is drawn but is pending use or cancel
p1, p2 = (0, 0), (0, 0)
click_point = []
select_obj_point = None

bbox_ROI = (0, 0, 0, 0)
bbox_old = (0, 0, 0, 0)
# Our ROI, defined by two points
state = 0
tracker_roi = None

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
from operator import itemgetter

def return_nearest_obj(results, targetPose, trashhold=100):
    global model
    # Get array of all found objects
    detections = np.array(results[0].boxes.xyxy.cpu(), dtype="int") # Используйте xyxy вместо boxes
    classes = np.array(results[0].boxes.cls.cpu(), dtype="int")
    track_ids = np.array(results[0].boxes.id.cpu(), dtype="int")

    # Check if detec samething
    if len(detections) > 0:
        # Sort object detection by dist from center of image   
        distances = [np.sqrt((((x[0] + x[2])/2)-targetPose[0])**2 + (((x[1] + x[3])/2)-targetPose[1])**2) for x in detections]
        sorted_indices = np.argsort(distances)
        detections = detections[sorted_indices]
        # Сортировка detections по distances

        # Found nearest object
        nearest_detection = detections[0]
        dist = np.sqrt((targetPose[0] - ((nearest_detection[0] + nearest_detection[2])/2))**2 + (targetPose[1] - ((nearest_detection[1] + nearest_detection[3])/2))**2)
        if dist > trashhold:
            print(" dist > trashhold")
            return None

        # Coords of nearest object
        x1, y1, x2, y2 = nearest_detection[:4]

        # # ID and name of nearest object
        class_id = classes[sorted_indices][0]
        track_id = track_ids[sorted_indices][0]
        name_id = model.names[class_id]

        center_x = int((x1 + x2) / 2)
        center_y = int((y1 + y2) / 2)
        
        ml_obj = Track_Object()
        ml_obj.name = name_id
        ml_obj.centerPoint = (center_x, center_y)
        ml_obj.class_id = class_id
        ml_obj.track_id = track_id
        ml_obj.xyxy = nearest_detection[:4]

        return ml_obj
    else:
        print("Object nit found.")
        return None

# Called every time a mouse event happen
def on_mouse(event, x, y, flags, userdata):
    global click_point, is_click
    global p1, p2, drawing, show_drawing, bbox_ROI

    if event == cv2.EVENT_LBUTTONDOWN:
        # Left click down (select first point)
        drawing = True
        show_drawing = True
        p1 = x, y
        p2 = x, y
        is_click = True
        click_point = x, y

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
    cv2.line(frame, (track_point[0], 0), (track_point[0], h), color=color, thickness=_thickness)
    cv2.line(frame, (0, track_point[1]), (w, track_point[1]), color=color, thickness=_thickness)

def norm_2d_points(pts):
        """
        This function, norm_2d_points, is designed to normalize the coordinates of 2D points. 
        It takes as input a pts array of four 2D points.        
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

def tracking_camera(frame, track_point, control, power=0.03):
    """
    Calculation of offset from tracking
    """

    h, w, _ = frame.shape
    dy, dx = int(h / 2), int(w / 2)
    # Calculate diff
    offset = (dx-track_point[0], dy-track_point[1])
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

    cv2.namedWindow("output", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('output', on_mouse)
    siyi_control = SIYIControl()

    while True:

        # Read frame from camera
        if is_click:
            selected_point = click_point
            is_click = False

        frame = siyi_cap.read()

        # If a ROI is selected, draw it
        if show_drawing:
            # Fix p2 to be always within the frame
            p2 = (
                0 if p2[0] < 0 else (p2[0] if p2[0] < frame.shape[1] else frame.shape[1]),
                0 if p2[1] < 0 else (p2[1] if p2[1] < frame.shape[0] else frame.shape[0])
            )
            cv2.rectangle(frame, p1, p2, (255, 0, 0), 2)

        # ML track and detection
        ml_results = model.track(frame, persist=True, tracker="botsort.yaml", conf=0.1, iou=0.5,  device="mps")
        if ml_results:
            is_bisy = False
            # overlay masks on original image
            if ml_results[0].boxes.id is not None:
                bboxes = np.array(ml_results[0].boxes.xyxy.cpu(), dtype="int")
                classes = np.array(ml_results[0].boxes.cls.cpu(), dtype="int")
                track_ids = np.array(ml_results[0].boxes.id.cpu(), dtype="int")

                if selected_point:
                  print("selected_point", selected_point)
                  select_obj_point = return_nearest_obj(ml_results, selected_point, 100)
                else:
                   select_obj_point = None

                for cls, bbox, track_id in zip(classes, bboxes, track_ids):       
                    (x, y, x2, y2) = bbox

                    if select_obj_point and track_id == select_obj_point.track_id:
                      # draw points track
                      track = track_history_ml[track_id]
                      center_x = int((x + x2) / 2)
                      center_y = int((y + y2) / 2)
                      track.append((int(center_x), int(center_y)))  # x, y center point
                      if len(track) > 10:  # retain 10 tracks
                          track.pop(0)
                      points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
                      cv2.polylines(frame, [points], isClosed=False, color=(255, 255, 255), thickness=2)

                      # draw selected border
                      draw_border(frame, (x,y), (x2, y2), (0,0,255), 2, 5, 10)
                      cv2.circle(frame, select_obj_point.centerPoint, 5, (0, 0, 255), 5)
                      draw_center(frame, selected_point, color=(255, 255, 255), _thickness=1)
                      
                    else:
                      draw_border(frame, (x,y), (x2, y2), (255,170,0), 2, 5, 10)

                    name = "ID: %s %s " % (track_id, model.names[cls])
                    cv2.putText(frame, name, (x, y - 5), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 225), 2)
                    
                    # add center point of point
                    center_x = int((x + x2) / 2)
                    center_y = int((y + y2) / 2)
                    cv2.circle(frame, (center_x, center_y), 5, (255, 255, 255), 2)
                    
        # Run tracker
        if tracker_roi:
            ret_tracking, bbox = tracker_roi.update(frame)
            if bbox_old != bbox:
                bbox_old = bbox

            # Draw bbox
            if ret_tracking:
                p1_ot = (int(bbox[0]), int(bbox[1]))
                p2_ot = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))               
                draw_border(frame, p1_ot, p2_ot, (0,128,255), 2, 5, 10)
                # draw line
                (x, y, x2, y2) = (p1_ot[0], p1_ot[1], p2_ot[0], p2_ot[1])
                center_x = int((x + x2) / 2)
                center_y = int((y + y2) / 2)
                track_history.append((int(center_x), int(center_y)))  # x, y center point
                if len(track_history) > 10:  # retain 10 tracks for 10 frames
                    track_history.pop(0)

                points = np.hstack(track_history).astype(np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [points], isClosed=False, color=(255, 255, 255), thickness=3)
                
                tracking_camera(frame, track_history[-1], siyi_control)
                selected_point = track_history[-1]
            else:
                if select_obj_point:
                    ret = tracker_roi.init(frame, select_obj_point.xywh)
                else:
                   selected_point = None

                cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
        


        # Show window    
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
          track_history.clear()

          if select_obj_point:
            #  select by ML
             ret = tracker_roi.init(frame, select_obj_point.xywh())
          else:
            # select by ROI
            if bbox_ROI[2] == 0 or bbox_ROI[3] == 0:
              print("Roi not celect")
              drawing = False
              show_drawing = False
              track_history.clear()
              selected_point = None
              if tracker_roi:
                  tracker_roi = None
            else:             
              ret = tracker_roi.init(frame, bbox_ROI)

          # here do something with ROI points values (p1 and p2)
        elif pressed in [ord('c'), ord('C')]:
            # Pressed C or Esc to cancel ROI
            drawing = False
            show_drawing = False
            track_history.clear()
            selected_point = None
            if tracker_roi:
                tracker_roi = None
        elif pressed in [27]:
            # Pressed Esc to cancel
            drawing = False
            show_drawing = False
            track_history.clear()
            if tracker_roi:
                tracker_roi = None
            break
        
    cv2.destroyAllWindows()
    siyi_cap.cap.release()
