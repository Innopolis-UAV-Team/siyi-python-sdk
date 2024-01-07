import numpy as np
import cv2

# For Details Reference Link:
# http://stackoverflow.com/questions/46036477/drawing-fancy-rectangle-around-face
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

# ============================================================================

if __name__ == '__main__':

    img = np.zeros((512,512,3), dtype=np.uint8)
    img[:]=(100,100,100)
    # b g r
    draw_border(img, (10,10), (100, 80), (255,0,0), 2, 10, 10)
    draw_border(img, (128,128), (340, 340), (255,0,0), 2, 10, 10)

    cv2.imshow('Fancy Rectangle',img)
    cv2.waitKey()
    cv2.destroyAllWindows()