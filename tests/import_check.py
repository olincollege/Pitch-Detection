import importlib.util
for pkg in ['cv2','moviepy','imageio','pydub','av','ffmpeg']:
    print(pkg, bool(importlib.util.find_spec(pkg)))
