import cv2
cap = cv2.VideoCapture('C:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Never Gonna Give You Up - Rick Astley.mp4')
print('open', cap.isOpened())
ret, frame = cap.read()
print('read', ret, None if frame is None else frame.shape)
cap.release()
