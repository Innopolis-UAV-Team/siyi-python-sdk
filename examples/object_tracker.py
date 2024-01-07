import cv2
import time

# Videl load

cap = cv2.VideoCapture(0)
time.sleep(3)

# Read frame
ret, frame = cap.read()
cv2.namedWindow('Tracking', cv2.WINDOW_NORMAL)
# Our ROI, defined by two points
state = 0
# Our ROI, defined by two points
p1, p2 = (0, 0), (0, 0)
drawing = False  # True while ROI is actively being drawn by mouse
show_drawing = False  # True while ROI is drawn but is pending use or cancel
blue = (255, 0, 0)

# Called every time a mouse event happen
def on_mouse(event, x, y, flags, userdata):
    global p1, p2, drawing, show_drawing

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

# Register the mouse callback
cv2.setMouseCallback('Tracking', on_mouse)

tracker = None
bbox_old = (0, 0, 0, 0)

while (cap.isOpened()):
    ret, frame = cap.read()
    if not ret:
        break
    # If a ROI is selected, draw it
    if show_drawing:
        # Fix p2 to be always within the frame
        p2 = (
            0 if p2[0] < 0 else (p2[0] if p2[0] < frame.shape[1] else frame.shape[1]),
            0 if p2[1] < 0 else (p2[1] if p2[1] < frame.shape[0] else frame.shape[0])
        )
        cv2.rectangle(frame, p1, p2, blue, 2)
       
    # Обновление трекера
    if tracker:
        ret_ot, bbox = tracker.update(frame)
        if bbox_old != bbox:
            bbox_old = bbox
            print("track", bbox)
        # Рисование ограничивающего прямоугольника
        if ret_ot:
            p1_ot = (int(bbox[0]), int(bbox[1]))
            p2_ot = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
            cv2.rectangle(frame, p1_ot, p2_ot, (255,155,0), 2, 1)
        else:
            cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

    # Отображение результатов отслеживания
    cv2.imshow("Tracking", frame)

    pressed = cv2.waitKey(1)
    if pressed in [13, 32]:
        # Pressed Enter or Space to use ROI
        if tracker:
            tracker.clear()
        tracker = cv2.TrackerCSRT.create()
        drawing = False
        show_drawing = False
        print(p1,p2)
        bbox1 = (p1[0],p1[1],p2[0],p2[1])
        print("bbox", bbox1)
        ret = tracker.init(frame, bbox1)

        # here do something with ROI points values (p1 and p2)
    elif pressed in [ord('c'), ord('C'), 27]:
        # Pressed C or Esc to cancel ROI
        drawing = False
        show_drawing = False
   


# Закрытие окна отображения
cap.release()
cv2.destroyAllWindows()