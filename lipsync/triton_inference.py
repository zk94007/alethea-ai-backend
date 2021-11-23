import uuid

import numpy as np
from time import time
import cv2, pickle
from moviepy.editor import *
from subprocess import Popen, PIPE
import subprocess as sp
import tritonclient.http as httpclient
from lipsync.utils import get_mel_chunks, load_preprocessed_data, calculate_estimated_frame, linear_color_transfer

import warnings

warnings.filterwarnings('ignore')

# Begins here
triton_client = httpclient.InferenceServerClient(
    url='18.117.252.78:8000', concurrency=4)
outputs = []
outputs.append(httpclient.InferRequestedOutput('540', binary_data=True))

fps = 25
mel_step_size = 16
batch_size = 100
preprocessed_data = {}


def process(speaker_name, audio, video_path, cur_frame=1, color_transfer=False):
    times = {}
    start = time()
    audio_path = audio
    len_mel, mel_batches = get_mel_chunks(audio_path)
    estimated_frame = calculate_estimated_frame(cur_frame, len_mel)
    face_dets, face_pos, result_frames, estimated_frames = load_preprocessed_data(preprocessed_data, video_path,
                                                                                  estimated_frame, batch_size, len_mel, speaker_name)

    times['mel'] = round(time() - start, 3)
    start = time()

    requests = []
    for face_det, mel_batch in zip(face_dets, mel_batches):
        input_mel = httpclient.InferInput('input.1', [len(face_det), 1, 80, 16], 'FP16')
        input_mel.set_data_from_numpy(mel_batch, binary_data=True)
        input_face = httpclient.InferInput('input.40', [len(face_det), 6, 96, 96], 'FP16')
        input_face.set_data_from_numpy(face_det, binary_data=True)
        requests.append(
            triton_client.async_infer('wav2lip_t4_214_fp16_dynamic', [input_mel, input_face], outputs=outputs))

    results = []
    for request in requests:
        result = request.get_result().as_numpy('540')
        results.append(result)
    results = np.transpose(np.concatenate(results).reshape((-1, 3, 96, 96)), (0, 2, 3, 1))

    times['inference'] = round(time() - start, 3)
    start = time()

    results = (np.asarray(results) * 255).astype('uint8')
    for i, (frame, result, position) in enumerate(zip(result_frames, results, face_pos)):
        y1, y2, x1, x2 = position
        result = cv2.resize(result, (x2 - x1, y2 - y1))
        if color_transfer:
            target_face = result.astype(np.float32) / 255.0
            source_face = frame[y1:y2, x1:x2].astype(np.float32) / 255.0
            result = (linear_color_transfer(target_face, source_face) * 255).astype('uint8')
        tmp = frame.copy()
        frame[y1:y2, x1:x2] = result

    times['post_processing'] = round(time() - start, 3)
    start = time()

    request_id = uuid.uuid4().hex[:7]
    result_path = f'media/generate_clips/{request_id}.mp4'

    if speaker_name == 'alice':
        # result_frames = [frame[:, :, ::-1] for frame in result_frames]
        result_frames = result_frames[..., ::-1]
    ImageSequenceClip(result_frames, fps=fps).write_videofile(result_path,
                                                              audio=audio,
                                                              threads=0,
                                                              codec='libx264',
                                                              preset='ultrafast',
                                                              logger=None)

    times['encoding'] = round(time() - start, 3)

    return result_path, times, estimated_frames
