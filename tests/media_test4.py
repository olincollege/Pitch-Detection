import subprocess
from pathlib import Path
import imageio_ffmpeg as ffmpeg

path = Path('C:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Never Gonna Give You Up - Rick Astley.mp4')
exe = ffmpeg.get_ffmpeg_exe()
print('ffmpeg exe', exe)
cmd = [exe, '-i', str(path), '-vn', '-f', 'wav', '-']
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = proc.communicate(timeout=10)
print('return', proc.returncode, 'out bytes', len(out))
print('err sample', err.decode('latin1')[:200])
