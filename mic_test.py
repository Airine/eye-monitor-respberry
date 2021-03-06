import pyaudio
import Queue
import threading
import numpy as np
from gcc_phat import gcc_phat
import math
from mic_array import MicArray
import numpy as np
from scipy.fftpack import fft
import matplotlib.pyplot as plt
from multiprocessing import Process, Queue
import os
import time
import pygame
import signal
import subprocess
plt.switch_backend("agg")

AUDIO_NAME = 'raw_data/sig22k_5s.wav'
SAMPLE_RATE = 48000
CHANNELS = 8

def play(audio, end_time=20.0):
    pygame.mixer.init()
    pygame.mixer.music.load(audio)
    pygame.mixer.music.play()
    start = time.time()
    while pygame.mixer.music.get_busy() == True:
        if time.time() - start > end_time:
            print('play break')
            break
        continue

# Get record chunks in `time_range` seconds.
def get_chunks(time_range=1.0):

    # from pixel_ring import pixel_ring

    is_quit = threading.Event()

    def signal_handler(sig, num):
        is_quit.set()
        print('Quit')

    signal.signal(signal.SIGINT, signal_handler)
    print('------')
    chunks = list()
    play_p = Process(target=play, args=(AUDIO_NAME, time_range,))
    with MicArray(SAMPLE_RATE, CHANNELS, SAMPLE_RATE / CHANNELS *time_range)  as mic:
        # proc = subprocess.Popen(['aplay', '-d', str(time_range), AUDIO_NAME])
        play_p.start()
        start = time.time()
        for chunk in mic.read_chunks():
            if time.time()-start > time_range:
                break
            chunks.append(chunk)

            if is_quit.is_set():
                break
    print('------')
    play_p.join()
    print('record finished')
    return chunks

# Preprocess and return the processed chunk list.
def preprocess(chunks, channels=8):
    chans = [list() for i in range(channels)]
    start = 0
    for c in chunks:
        for i in range(len(c)):
            channel = i % channels
            chans[channel].append(c[i])
    print('------')
    print('preprocess finished')
    return [np.asarray(chan) for chan in chans]

# Plot the fft figure of the channels
def plot_fft(N, T, pro_chans):

    # N = 48000
    # T = 1.0 / 48000
    # x = np.linspace(0.0, N*T, N)
    i = 1
    for c in pro_chans:
        print('------')
        print('ploting fft')
        yf = fft(c)
        xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
        plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
        plt.grid()
        plt.show()
        plt.savefig('fft-channel-{}.png'.format(i), format='png')
        plt.close()
        i += 1

# plot the signal in time sequence.
def plot_signal(pro_chans, head=False):
    i = 1
    for c in pro_chans:
        print('------')
        print('ploting')
        x = np.linspace(1, len(c), len(c))
        if head:
            x = np.linspace(1, 200, 200)
            c = c[:200]
        plt.plot(x, c)
        plt.grid()
        plt.show()
        plt.savefig('time-channel-{}.png'.format(i), format='png')
        plt.close()
        i += 1

def save_to_npy(pro_chans):
    dir = 'data/ddl/'
    for i in range(len(pro_chans)):
        target_file = dir + 'channel{}'.format(i)+'.npy'
        file_dir = os.path.split(target_file)[0]
        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)
        print(target_file)
        np.save(target_file, pro_chans[i])

if __name__ == '__main__':
    chunks = get_chunks(5)
    pro_chans = preprocess(chunks, channels=8)
    N = 48000
    T = 1.0 / 48000
    save_to_npy(pro_chans)
    plot_signal(pro_chans, head=True)
    plot_fft(N, T, pro_chans)
