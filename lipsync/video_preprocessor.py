import numpy as np
from lipsync.face_detection.api import FaceAlignment, LandmarksType
from tqdm import tqdm
from moviepy.editor import *
from shapely.geometry import Polygon
import cv2, pickle
import skvideo.io


def get_smoothened_boxes(boxes, T):
    for i in range(len(boxes)):
        if i + T > len(boxes):
            window = boxes[len(boxes) - T:]
        else:
            window = boxes[i: i + T]
        boxes[i] = np.mean(window, axis=0)
    return boxes


def face_detect(images):
    detector = FaceAlignment(LandmarksType._2D,
                                            flip_input=False, device='cpu')

    batch_size = 2

    while 1:
        predictions = []
        try:
            for i in tqdm(range(0, len(images), batch_size)):
                predictions.extend(detector.get_detections_for_batch(np.array(images[i:i + batch_size])))
        except RuntimeError:
            if batch_size == 1:
                raise RuntimeError(
                    'Image too big to run face detection on GPU. Please use the --resize_factor argument')
            batch_size //= 2
            print('Recovering from OOM error; New batch size: {}'.format(batch_size))
            continue
        break

    results = []
    pady1, pady2, padx1, padx2 = 0, 0, 0, 0
    for rect, image in zip(predictions, images):
        if rect is None:
            cv2.imwrite('temp/faulty_frame.jpg', image)  # check this frame where the face was not detected.
            raise ValueError('Face not detected! Ensure the video contains a face in all the frames.')
        y1 = max(0, rect[1] - pady1)
        y2 = min(image.shape[0], rect[3] + pady2)
        x1 = max(0, rect[0] - padx1)
        x2 = min(image.shape[1], rect[2] + padx2)

        results.append([x1, y1, x2, y2])

    boxes = np.array(results)
    boxes = get_smoothened_boxes(boxes, T=5)
    boxes = np.array([(y1, y2, x1, x2) for (x1, y1, x2, y2) in boxes])
    return boxes


def calculate_iou(box_1, box_2):
    iou = box_1.intersection(box_2).area / box_1.union(box_2).area
    return iou


def calculate_next_closest_frames(positions):
    next_closest = {}
    for i in range(len(positions)):
        next_closest[i] = [i]

    for frame in range(len(positions)):
        ymin, ymax, xmin, xmax = positions[frame]
        box_1 = Polygon([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
        tmp_pos = np.roll(positions, frame, axis=0)
        j = 10
        thresh = 0.95
        while j < len(tmp_pos):
            ymin, ymax, xmin, xmax = tmp_pos[j]
            box_2 = Polygon([[xmin, ymin], [xmax, ymin], [xmax, ymax], [xmin, ymax]])
            if j > 40: thresh = 0.90
            if j > 60: thresh = 0.85
            if calculate_iou(box_1, box_2) > thresh:
                f = j + frame
                if f > len(positions):
                    f = f - len(positions)
                next_closest[frame].append(f)
                if len(next_closest[frame]) >= 11: break
                j += 5
            else:
                j += 1
    return next_closest


def preprocess_video(video_path, width):
    if width is None: width = 740
    width = int(width)
    folder_path = video_path.rsplit('/', 1)[:1][0]
    clip = VideoFileClip(video_path)
    width = min(width, clip.size[0])
    frames = skvideo.io.vread(video_path)
    cv2.imwrite('temp/frame.jpg', frames[10])
    clip = ImageSequenceClip(frames, clip.fps)
    clip = clip.fx(vfx.resize, width=width)
    clip.fps = 25
    frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) for frame in clip.iter_frames()]
    frames = [cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) for frame in clip.iter_frames()]
    print("Final frame shape :", frames[0].shape)
    positions = face_detect(frames)
    faces = np.asarray(
        [cv2.resize(frame[y1:y2, x1:x2], (96, 96)) for frame, (y1, y2, x1, x2) in zip(frames, positions)])
    cv2.imwrite('temp/face.jpg', faces[10])
    faces_masked = np.copy(faces)
    faces_masked[:, 96 // 2:] = 5
    face_dets = np.concatenate((faces_masked, faces), axis=-1) / 255.
    face_dets = np.transpose(face_dets, (0, 3, 1, 2))
    next_frames = calculate_next_closest_frames(positions)

    np.save(f"{folder_path}/face_positions.npy", positions)
    np.save(f"{folder_path}/frames.npy", frames)
    np.save(f"{folder_path}/face_dets.npy", face_dets)
    pickle.dump(next_frames, open(f"{folder_path}/next_frames.pkl", 'wb'))

    return None
