import ffmpegcv
import cv2

# Создайте объект VideoCaptureStream с URL вашего RTCP
stream = ffmpegcv.VideoCaptureStream("rtsp://192.168.144.25:8554/main.264")


while True:
    # Считывайте кадры из потока
    ret, frame = stream.read()

    # Если кадр успешно считан, отобразите его
    if ret:
        cv2.imshow('Frame', frame)

    # Если нажата клавиша 'q', выйдите из цикла
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Закройте поток и освободите ресурсы
stream.close()
cv2.destroyAllWindows()
