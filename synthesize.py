# -*- coding: utf-8 -*-
# /usr/bin/python2
'''
By kyubyong park. kbpark.linguist@gmail.com.
https://www.github.com/kyubyong/tacotron
'''

from __future__ import print_function

from hyperparams import Hyperparams as hp
import tqdm
from data_load import load_data
import tensorflow as tf
from train import Graph
from utils import spectrogram2wav, load_spectrograms
from scipy.io.wavfile import write
import os
from glob import glob
import numpy as np


def synthesize():
    if not os.path.exists(hp.sampledir): os.mkdir(hp.sampledir)

    # Load data
    texts = load_data(mode="synthesize")

    # reference audio
    mels, maxlen = [], 0
    files = glob(hp.ref_audio)
    for f in files:
        _, mel, _= load_spectrograms(f)
        mel = np.reshape(mel, (-1, hp.n_mels))
        maxlen = max(maxlen, mel.shape[0])
        mels.append(mel)

    ref = np.zeros((len(mels), maxlen, hp.n_mels), np.float32)
    for i, m in enumerate(mels):
        ref[i, :m.shape[0], :] = m

    # Load graph
    g = Graph(mode="synthesize"); print("Graph loaded")

    saver = tf.train.Saver()
    with tf.Session() as sess:
        saver.restore(sess, tf.train.latest_checkpoint(hp.logdir)); print("Restored!")

        # Feed Forward
        ## mel
        y_hat = np.zeros((texts.shape[0], 200, hp.n_mels*hp.r), np.float32)  # hp.n_mels*hp.r
        for j in tqdm.tqdm(range(200)):
            _y_hat = sess.run(g.y_hat, {g.x: texts, g.y: y_hat, g.ref: ref})
            y_hat[:, j, :] = _y_hat[:, j, :]
        ## mag
        mags = sess.run(g.z_hat, {g.y_hat: y_hat})
        for i, mag in enumerate(mags):
            print("File {}.wav is being generated ...".format(i+1))
            audio = spectrogram2wav(mag)
            write(os.path.join(hp.sampledir, '{}.wav'.format(i+1)), hp.sr, audio)

if __name__ == '__main__':
    synthesize()
    print("Done")
