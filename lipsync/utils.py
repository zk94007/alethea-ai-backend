import numpy as np
import pickle
from moviepy.editor import *
from time import time

from lipsync.audio import load_wav, melspectrogram


def cycle_np(arr, slice_len, rotate=None, return_list=None):
    # Using list because numpy works with contigous memory only which leads to unnecessary copying. Saving ~ 0.2 second.
    larr = list(arr)
    if rotate: larr = larr[rotate:] + larr[:rotate]
    if len(larr) >= slice_len:
        return np.copy(larr[:slice_len])

    else:
        count = slice_len // len(arr)
        remaining_len = slice_len % len(arr)

        if not remaining_len:
            return np.repeat(larr, count, axis=0)

        if return_list:
            return list(np.repeat(larr, count, axis=0)) + list(np.copy(larr[:remaining_len]))
        return np.concatenate((np.repeat(larr, count, axis=0), larr[:remaining_len]))


def get_mel_chunks(audio_path, batch_size=100, fps=25, mel_step_size=16):
    wav = load_wav(audio_path, 16000)
    mel = melspectrogram(wav)

    mel_chunks = []
    mel_idx_multiplier = 80. / fps
    i = 0
    while 1:
        start_idx = int(i * mel_idx_multiplier)
        if start_idx + mel_step_size > len(mel[0]):
            mel_chunks.append(mel[:, len(mel[0]) - mel_step_size:])
            break
        mel_chunks.append(mel[:, start_idx: start_idx + mel_step_size])
        i += 1
    len_mel = len(mel_chunks)
    mel_data = np.asarray(mel_chunks).reshape((-1, 1, 80, 16)).astype(np.float16)
    mel_batches = list(create_batches(batch_size, mel_data))
    return len_mel, mel_batches


def create_batches(batch_size, arr):
    for i in range(0, len(arr), batch_size):
        yield arr[i:i + batch_size]


def load_preprocessed_data(preprocessed_data, video_path, estimated_frame, batch_size, len_mel, speaker_name):
    if not speaker_name in preprocessed_data.keys():
        preprocessed_data[speaker_name] = {}
        data = preprocessed_data[speaker_name]
        path = video_path.rsplit('/', 1)[:1][0]
        data['full_frames'] = list(np.load(f"{path}/frames.npy"))
        data['face_pos'] = np.load(f"{path}/face_positions.npy")
        data['face_dets'] = np.load(f"{path}/face_dets.npy").astype(np.float16)
        data['next_frames'] = pickle.load(open(f"{path}/next_frames.pkl", 'rb'))

    data = preprocessed_data[speaker_name]

    face_dets = cycle_np(data['face_dets'], len_mel, rotate=estimated_frame, return_list=False)
    face_pos = cycle_np(data['face_pos'], len_mel, rotate=estimated_frame, return_list=True)
    result_frames = cycle_np(data['full_frames'], len_mel, rotate=estimated_frame, return_list=True)

    face_dets = list(create_batches(batch_size, face_dets))
    return face_dets, face_pos, result_frames, data['next_frames'][estimated_frame]


def calculate_estimated_frame(cur_frame, text):
    # Temporary placeholder function. Will reimplement after network latency issue solved
    if cur_frame + 30 >= 50:
        return cur_frame + 30 - 50
    else:
        return cur_frame + 30


def linear_color_transfer(target_img, source_img, mode='pca', eps=1e-5):
    '''
    Matches the colour distribution of the target image to that of the source image
    using a linear transform.
    Images are expected to be of form (w,h,c) and float in [0,1].
    Modes are chol, pca or sym for different choices of basis.
    '''
    mu_t = target_img.mean(0).mean(0)
    t = target_img - mu_t
    t = t.transpose(2, 0, 1).reshape(t.shape[-1], -1)
    Ct = t.dot(t.T) / t.shape[1] + eps * np.eye(t.shape[0])
    mu_s = source_img.mean(0).mean(0)
    s = source_img - mu_s
    s = s.transpose(2, 0, 1).reshape(s.shape[-1], -1)
    Cs = s.dot(s.T) / s.shape[1] + eps * np.eye(s.shape[0])
    if mode == 'chol':
        chol_t = np.linalg.cholesky(Ct)
        chol_s = np.linalg.cholesky(Cs)
        ts = chol_s.dot(np.linalg.inv(chol_t)).dot(t)
    if mode == 'pca':
        eva_t, eve_t = np.linalg.eigh(Ct)
        Qt = eve_t.dot(np.sqrt(np.diag(eva_t))).dot(eve_t.T)
        eva_s, eve_s = np.linalg.eigh(Cs)
        Qs = eve_s.dot(np.sqrt(np.diag(eva_s))).dot(eve_s.T)
        ts = Qs.dot(np.linalg.inv(Qt)).dot(t)
    if mode == 'sym':
        eva_t, eve_t = np.linalg.eigh(Ct)
        Qt = eve_t.dot(np.sqrt(np.diag(eva_t))).dot(eve_t.T)
        Qt_Cs_Qt = Qt.dot(Cs).dot(Qt)
        eva_QtCsQt, eve_QtCsQt = np.linalg.eigh(Qt_Cs_Qt)
        QtCsQt = eve_QtCsQt.dot(np.sqrt(np.diag(eva_QtCsQt))).dot(eve_QtCsQt.T)
        ts = np.linalg.inv(Qt).dot(QtCsQt).dot(np.linalg.inv(Qt)).dot(t)
    matched_img = ts.reshape(*target_img.transpose(2, 0, 1).shape).transpose(1, 2, 0)
    matched_img += mu_s
    matched_img[matched_img > 1] = 1
    matched_img[matched_img < 0] = 0
    return np.clip(matched_img.astype(source_img.dtype), 0, 1)
