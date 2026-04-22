            # Load lyrics
            lyrics_file = 'c:/Users/lbennicoff1/.vscode/YIN-Pitch/Figures/Assets/lyrics.txt'
            with open(lyrics_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line and ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        try:
                            minutes = int(parts[0])
                            seconds = int(parts[1])
                            lyrics_text = parts[2]
                            timestamp = minutes * 60 + seconds
                            self.lyrics_times.append(timestamp)
                            self.lyrics.append(lyrics_text)
                        except:
                            continue
