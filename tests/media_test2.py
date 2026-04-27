import imageio
import cv2
from pathlib import Path

target = Path('C:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Never Gonna Give You Up - Rick Astley.mp4')
print('exists', target.exists())
reader = imageio.get_reader(str(target), format='ffmpeg')
print('meta', reader.get_meta_data())
frame = next(reader)
print('frame shape', frame.shape, frame.dtype)
reader.close()
