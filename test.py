import vlc
import time

player = vlc.MediaPlayer("/music/Wya.mp3")
player.audio_set_volume(100)
player.play()
time.sleep(0.5)


while player.get_state() not in (vlc.State.Ended, vlc.State.Error):
    time.sleep(0.1)

print("Playback finished")