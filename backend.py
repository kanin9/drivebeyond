import cv2
import time
import datetime
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from pyqtgraph.Qt import QtCore

# import mss.windows
from facereid.landmarks_detector import LandmarksDetector
# mss.windows.CAPTUREBLT = 0
from fer import FER
# from sface import SFace
from facereid.face_identifier import FaceIdentifier
from facereid.faces_database import FacesDatabase
# from mss.windows import MSS as mss
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtChart import QBarSet
from openvino.runtime import Core


class Result:
    OUTPUT_SIZE = 7

    def __init__(self, roi):
        # self.image_id = output[0]
        # self.label = int(output[1])
        self.confidence = 1.0
        self.position = np.array((roi[0], roi[1]))  # (x, y)
        self.size = np.array((roi[2], roi[3]))  # (w, h)

    def rescale_roi(self, roi_scale_factor=1.0):
        self.position -= self.size * 0.5 * (roi_scale_factor - 1.0)
        self.size *= roi_scale_factor

    def resize_roi(self, frame_width, frame_height):
        self.position[0] *= frame_width
        self.position[1] *= frame_height
        self.size[0] = self.size[0] * frame_width - self.position[0]
        self.size[1] = self.size[1] * frame_height - self.position[1]

    def clip(self, width, height):
        min = [0, 0]
        max = [width, height]
        self.position[:] = np.clip(self.position, min, max)
        self.size[:] = np.clip(self.size, min, max)


def format(detection):
    res = np.empty((5, 2))

    landmarks, roi = detection

    for i, lm in enumerate(landmarks):
        res[i] = np.array([(lm[0] - roi[0]) / roi[2], (lm[1] - roi[1]) / roi[3]])

    return res


class Worker(QObject):
    finished = pyqtSignal()
    requestUpdate = pyqtSignal()


    def __init__(self):
        super(QObject, self).__init__()
        self.run = False

        self.data = {}
        self.idx = 0
        self.timestamp = None
        self.bgr = None
        self.img = None

        # self.sct = mss()
        """
        core = Core()

        self.landmarks_detector = LandmarksDetector(core,
                                                    'facereid/intel/landmarks-regression-retail-0009/FP32/landmarks-regression-retail-0009.xml')

        self.identifier = FaceIdentifier(core,
                                         'facereid/intel/face-reidentification-retail-0095/FP32/face-reidentification'
                                         '-retail-0095.xml',
                                         match_threshold=0.3,
                                         match_algo='HUNGARIAN')

        self.landmarks_detector.deploy('CPU', 32)
        self.identifier.deploy('CPU', 32)

        self.database = FacesDatabase(r"database/",
                                      self.identifier,
                                      self.landmarks_detector,
                                      None,
                                      False)

        self.identifier.set_faces_database(self.database)
        """

        self.detector = FER(fdnn="yunet", scale_factor=1.1)

    def scale(self, array, index):
        if index >= array.shape[0]:
            tmp = array
            array = np.zeros(array.shape[0] * 2)
            array[:tmp.shape[0]] = tmp
        return array

    def capture(self):
        self.run = True
        # bounding_box = {'top': 0, 'left': 0, 'width': 1920, 'height': 1080}

        data = {
            'surprise': np.zeros(100),
            'happy': np.zeros(100),
            'neutral': np.zeros(100),
            'angry': np.zeros(100),
            'sad': np.zeros(100),
            'disgust': np.zeros(100),
            'fear': np.zeros(100)
        }

        oldtime = time.time()
        start = time.time()
        timestamp = np.zeros(100)
        idx = 0

        deviceId = 0
        cap = cv2.VideoCapture(deviceId)
        # w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while self.run:
            _, self.bgr = cap.read()

            # Use for screen capture
            # imgnp = np.array(self.sct.grab(bounding_box))
            # self.bgr = cv2.cvtColor(imgnp, cv2.COLOR_BGRA2BGR)

            response = self.analyze(self.bgr)

            emotions = ['surprise', 'happy', 'neutral', 'angry', 'sad', 'disgust', 'fear']

            sample = response['sample']

            for index, emotion in enumerate(emotions):
                value = 0.0
                if emotion in response['emotions']:
                    value = round(response['emotions'][emotion]['score'] / sample, 2)

                # self.bar.replace(index, value)

                data[emotion] = self.scale(data[emotion], idx)
                data[emotion][idx] = value

            timestamp = self.scale(timestamp, idx)

            now = time.time()
            timestamp[idx] = now - start

            #print("FPS:", 1 / (now - oldtime))
            oldtime = time.time()

            idx += 1

            self.data = data
            self.idx = idx
            self.timestamp = timestamp[:idx]

            self.img = self.bgr

            self.requestUpdate.emit()

    def stop(self, message=None):

        if message:
            print(message)
        else:
            print("Stopping worker")

        data = {
            'surprise': np.zeros(0),
            'happy': np.zeros(0),
            'neutral': np.zeros(0),
            'angry': np.zeros(0),
            'sad': np.zeros(0),
            'disgust': np.zeros(0),
            'fear': np.zeros(0)
        }

        self.run = False
        self.data = data
        self.idx = 0

    def analyze(self, image):
        faces = self.detector.detect_emotions(image)
        rois = [x['box'].astype(np.int32) for x in faces]

        landmarks = [(x['landmarks'], x['box'].astype(np.int32)) for x in faces]

        """
        face_identities, unknowns = self.identifier.infer(
            (image, [Result(roi) for roi in rois], [format(lm) for lm in landmarks]))

        for face, roi in zip(face_identities, rois):
            name = self.identifier.get_identity_label(face.id)
            cv2.putText(self.bgr, name, (roi[0], roi[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)

        #print([self.identifier.get_identity_label(face.id) for face in face_identities], unknowns)
        """

        for x in faces:
            bbox = x['box'].astype(np.int32)
            landmarks_ = x['landmarks']
            cv2.rectangle(self.bgr, (bbox[0], bbox[1]), (bbox[0] + bbox[2], bbox[1] + bbox[3]), (0, 255, 0), 2)
            # print(landmarks)

            for lm in landmarks_:
                cv2.circle(self.bgr, lm, 2, (255, 0, 0), 2)

        data = {
        }

        sample = 0

        if len(faces) > 0:
            sample = 1

        biggest = (0, 0, 0, 0)

        for face in faces:
            emotions = face['emotions']
            x, y, w, h = face['box']

            if w > biggest[0] and h > biggest[1]:
                biggest = (w, h, x, y)

                for emotion in emotions:
                    score = emotions[emotion]
                    if emotion in data:
                        data[emotion]['score'] = score
                    else:
                        data[emotion] = {
                            'score': score
                        }

        cv2.rectangle(self.bgr, (biggest[2], biggest[3]), (biggest[2] + biggest[0], biggest[1] + biggest[3]), (255, 0, 0), 3)

        mapping = {
            'emotions': data,
            'sample': sample
        }

        return mapping
