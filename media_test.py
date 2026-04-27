import soundfile as sf
from pathlib import Path

target = Path('C:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Never Gonna Give You Up - Rick Astley.mp4')
print('exists', target.exists())
try:
    data, rate = sf.read(str(target), dtype='float32')
    print('soundfile read ok', data.shape, rate)
except Exception as e:
    print('soundfile error', repr(e))
