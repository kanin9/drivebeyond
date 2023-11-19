import math
import os
import random
import sys
import time
from functools import partial
import collections

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtChart import QChart, QStackedBarSeries, QBarSet, QChartView, QBarCategoryAxis, QValueAxis, QBarSeries
from PyQt5.QtGui import QFont, QPixmap, QImage, QMovie, QLinearGradient, QColor, QPalette, QBrush, QIcon, QPainter, \
    QPainterPath, QPen
from PyQt5.QtMultimedia import QSound, QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QPushButton, QGridLayout, QVBoxLayout, QHBoxLayout, \
    QFrame, QLabel, QWidget, QGraphicsOpacityEffect, QSizePolicy, QLayout
from PyQt5.QtCore import QThread, QUrl, pyqtSignal, QTimer, QPropertyAnimation, QPoint, QSequentialAnimationGroup, Qt, \
    QRect
from PyQt5.uic import loadUi
from PyQt5.uic.properties import QtGui

from backend import Worker
import cv2

thread = QThread()
worker = Worker()
worker.moveToThread(thread)
thread.started.connect(worker.capture)
worker.finished.connect(thread.quit)
stop = True

mediaPlayer = QMediaPlayer()

challengeRound = 0

threshold = {
    'angry': 0.03,
    'happy': 0.8,
    'sad': 0.1,
    'neutral': 0.8,
    'disgust': 0.03,
    'surprise': 0.8
}

emotions = ['happy', 'angry', 'sad', 'surprise', 'disgust', 'neutral']

locale = {
    'ru': {
        'happy': 'счастье',
        'sad': 'грусть',
        'angry': 'злость',
        'surprise': 'удивление',
        'disgust': 'отвращение',
        'neutral': 'нейтральность'
    },
    'kz': {
        'happy': 'қуаныш',
        'sad': 'мұң',
        'angry': 'ашу',
        'surprise': 'аң-таң',
        'disgust': 'жиіркеніш',
        'neutral': 'бейтараптық'
    },
    'en': {
        'happy': 'happiness',
        'sad': 'sadness',
        'angry': 'anger',
        'surprise': 'wonder',
        'disgust': 'disgust',
        'neutral': 'neutrality'
    }
}

lang = "ru"

def setLanguage(language):
    global lang
    lang = language
    print(lang)
    goPage(1)

def nested_dict():
    return collections.defaultdict(nested_dict)

results = nested_dict()

def nextPage():
    window.stackedWidget.setCurrentIndex(window.stackedWidget.currentIndex() + 1)
    window.homeButton.clicked.connect(partial(goPage, window.stackedWidget.currentIndex()))
    #window.stackedWidget.currentWidget().update()
    if type(window.stackedWidget.currentWidget()) is TrainingScreen:
        window.stackedWidget.currentWidget().connect()
        mediaPlayer.setMedia(window.stackedWidget.currentWidget().audio)
        mediaPlayer.play()

    elif type(window.stackedWidget.currentWidget()) in [CongratulationWidget, StatisticsWidget, EndStatisticsWidget, PerformanceWidget, ChallengeWidget, GuidingScreen, SelectionMenu]:
        window.stackedWidget.currentWidget().connect()
        #print("Connected: ", widget.currentWidget().ui)

def goBack():
    if window.stackedWidget.currentIndex() > 0:
        window.stackedWidget.setCurrentIndex(window.stackedWidget.currentIndex() - 1)
        if type(window.stackedWidget.currentWidget()) is TrainingScreen:

            window.stackedWidget.currentWidget().connect()
            mediaPlayer.setMedia(window.stackedWidget.currentWidget().audio)
            mediaPlayer.play()

def goPage(num):
    if type(window.stackedWidget.currentWidget()) is TrainingScreen:
        try:
            window.stackedWidget.currentWidget().disconnect()
        except Exception:
            pass

    window.stackedWidget.setCurrentIndex(num)
    if type(window.stackedWidget.currentWidget()) is TrainingScreen:
        window.homeButton.clicked.connect(partial(goPage, window.stackedWidget.currentIndex()))
        window.stackedWidget.currentWidget().connect()
        mediaPlayer.setMedia(window.stackedWidget.currentWidget().audio)
        mediaPlayer.play()

    elif type(window.stackedWidget.currentWidget()) in [CongratulationWidget, StatisticsWidget, EndStatisticsWidget, PerformanceWidget, ChallengeWidget, GuidingScreen]:
        window.stackedWidget.currentWidget().connect()

class QDynamicLabel(QLabel):
    clicked = pyqtSignal(str)

    def __init__(self, emotion, parent=None):
        self.emotion = emotion

        super(QDynamicLabel, self).__init__(parent)

    def enterEvent(self, ev):
        self.setStyleSheet("border: 2px dashed gray")

    def leaveEvent(self, ev):
        self.setStyleSheet("border: 0px dashed gray")

    def mousePressEvent(self, ev):
        self.clicked.emit(self.emotion)

class GuidingScreen(QDialog):
    def __init__(self, ui):
        super(GuidingScreen, self).__init__()
        self.ui = ui
        loadUi(ui, self)
        self.setObjectName("parentWidget")

        self.layout = QVBoxLayout()
        self.bottom = QFrame()
        self.bottomLayout = QHBoxLayout()
        self.bottom.setLayout(self.bottomLayout)

        if ui != "uis/mainscreen.ui" and ui != "uis/finalscreen.ui":
            self.returnButton = QPushButton()
            self.returnButton.setFixedSize(221, 91);
            self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")

            self.bottomLayout.addWidget(self.returnButton, alignment=QtCore.Qt.AlignBottom)

            self.returnButton.clicked.connect(goBack)

        if hasattr(self, "changepage"):
            self.bruh = self.changepage
            self.bottomLayout.addWidget(self.bruh, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)

            self.bruh.clicked.connect(nextPage)

        self.layout.addWidget(self.bottom, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        self.setLayout(self.layout)

    def connect(self):
        if lang == "kz":
            if self.ui != "uis/mainscreen.ui" and self.ui != "uis/finalscreen.ui":
                self.returnButton.setStyleSheet("border-image: url('uis/goback_kz.png');")
            if hasattr(self, "changepage"):
                self.bruh.setStyleSheet("border-image: url('uis/buttonbg_kz.png');")
            try:
                self.setStyleSheet('#parentWidget { border-image: url("' + f"{self.ui[:-3] + 'bg_kz' + '.PNG'}" + '") 0 0 0 0 stretch stretch; }');
            except Exception as e:
                print(e)
        elif lang == "en":
            if self.ui != "uis/mainscreen.ui" and self.ui != "uis/finalscreen.ui":
                self.returnButton.setStyleSheet("border-image: url('uis/goback_en.png');")
            if hasattr(self, "changepage"):
                self.bruh.setStyleSheet("border-image: url('uis/buttonbg_en.png');")
            try:
                self.setStyleSheet('#parentWidget { border-image: url("' + f"{self.ui[:-3] + 'bg_en' + '.PNG'}" + '") 0 0 0 0 stretch stretch; }');
            except Exception as e:
                print(e)


class ReactionPopup(QLabel):
    def __init__(self, resource, parent=None, size=(256, 256)):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.resize(size[0], size[1])

        self.movie = QMovie(resource)
        self.movie.setScaledSize(QtCore.QSize(size[0], size[1]))
        self.movie.frameChanged.connect(self.animate)
        self.end = self.movie.frameCount()

        self.effect = QGraphicsOpacityEffect(self)
        self.effect.setOpacity(0)

        self.setMovie(self.movie)
        self.setGraphicsEffect(self.effect)

        self.easeFunction = self.easeInOutSinusoidal

    def animate(self, currFrame):
        self.updateEffect(currFrame)

        if currFrame == self.end - 1:
            self.effect.setOpacity(0)
            self.movie.stop()

    def updateEffect(self, currFrame):

        squashed = currFrame / self.end

        self.effect.setOpacity(
            self.easeFunction(
                squashed
            )
        )


    def easeInOutSinusoidal(self, x):
        """
        x: should be in range of [0, 1]
        Sinusoidal ease in and out function.
        """
        return math.sin(x * math.pi)

class TrainingScreen(QMainWindow):
    def __init__(self, ui, emotion, level):
        super(TrainingScreen, self).__init__()
        self.ui = ui
        self.level = level
        fullPath = os.path.join(os.getcwd() + f"/resources/audio/{emotion}.mp3")
        url = QUrl.fromLocalFile(fullPath)
        self.audio = QMediaContent(url)

        self.startTime = None
        self.skipButton = None
        self.elapsed = 0.0
        self.done = False
        self.emotion = emotion

        loadUi(ui, self)
        self.loops = 0
        self.layout = QVBoxLayout()
        self.bottom = QFrame()
        self.feedbackPopup = ReactionPopup("resources/gif/thumbs-up.gif", parent=self)
        self.feedbackPopup.move(self.width() // 2 - 128, self.height() // 2 - 128)
        self.bottomLayout = QHBoxLayout()
        self.returnButton = QPushButton()
        self.returnButton.setFixedSize(221, 91)
        self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")

        self.bottomLayout.addWidget(self.returnButton, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        self.returnButton.clicked.connect(self.goBack)

        self.bottomLayout.addWidget(self.button, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        self.bottom.setLayout(self.bottomLayout)

        self.cameraLabel = QLabel()
        self.cameraLabel.setFixedSize(640, 480)

        self.cameraLabel.setPixmap(QPixmap("resources/static/nocamera.jpg"))

        self.header = QLabel(f"<P><font font-family='Bahnschrift' font-size=30>Нажми на кнопку \"начать тест\"<br>и постарайся изобразить</font> <b><big>{locale['ru'][emotion]}</big></b></P>")
        self.header.setFont(QFont("Bahnschrift", 28))
        self.header.setAlignment(QtCore.Qt.AlignCenter)

        self.layout.addWidget(self.header, alignment=QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.centered = QFrame()
        self.centeredLayout = QHBoxLayout()

        if self.level < 1:
            self.labelDynamic = QLabel()
            self.labelDynamic.setMaximumSize(QtCore.QSize(300, 300))
            self.movie = QMovie(f"resources/gif/{emotion}1.gif")
            self.movie.setScaledSize(QtCore.QSize(300, 300))
            self.labelDynamic.setMovie(self.movie)
            self.movie.setSpeed(150)
            self.movie.start()

            self.centeredLayout.addWidget(self.labelDynamic)
        elif self.level < 2:
            self.labelStatic = QLabel()
            self.imageStatic = QPixmap(f"resources/static/{emotion}_collage.jpg")
            self.labelStatic.setFixedSize(500, 500)
            self.labelStatic.setPixmap(self.imageStatic.scaled(self.labelStatic.size(), QtCore.Qt.IgnoreAspectRatio,
                                                               QtCore.Qt.SmoothTransformation))
            self.centeredLayout.addWidget(self.labelStatic)

        self.centeredLayout.addWidget(self.cameraLabel)

        self.centered.setLayout(self.centeredLayout)
        self.layout.addWidget(self.centered)

        self.layout.addWidget(self.bottom, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        self.centralwidget.setLayout(self.layout)
        self.button.clicked.connect(self.beginCapture)

    def beginCapture(self):
        if not self.done:
            thread.start()

    def connect(self):
        if lang == "kz":
            fullPath = os.path.join(os.getcwd() + f"/resources/audio/kz/{self.emotion}.mp3")
            url = QUrl.fromLocalFile(fullPath)
            self.audio = QMediaContent(url)

            self.header.setText(f"<P><font font-family='Bahnschrift' font-size=30>«Тестті бастау» түймесін басып,<br></font> <b><big>{locale['kz'][self.emotion]}</big></b> <font font-family='Bahnschrift' font-size=30>эмоциясын көрсетуге тырысыңыз</font></P>")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_kz.png');")
        elif lang == "en":
            fullPath = os.path.join(os.getcwd() + f"/resources/audio/en/{self.emotion}.mp3")
            url = QUrl.fromLocalFile(fullPath)
            self.audio = QMediaContent(url)

            self.header.setText(
                f"<P><font font-family='Bahnschrift' font-size=30>Press the «Start the test» button and try to portray <br></font> <b><big>{locale['en'][self.emotion]}</big></b> <font font-family='Bahnschrift' font-size=30></font></P>")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_en.png');")

        if not self.done:
            if lang == "ru":
                self.button.setStyleSheet('border-image: url("uis/starttest.PNG")')
            elif lang == "kz":
                self.button.setStyleSheet('border-image: url("uis/starttest_kz.png")')
            elif lang == "en":
                self.button.setStyleSheet('border-image: url("uis/starttest_en.png")')
        else:
            if lang == "ru":
                self.button.setStyleSheet('border-image: url("uis/restart.png")')
            elif lang == "kz":
                self.button.setStyleSheet('border-image: url("uis/restart_kz.png")')
            elif lang == "en":
                self.button.setStyleSheet('border-image: url("uis/restart_en.png")')

            if self.skipButton is None:
                self.skipButton = QPushButton()
                # self.skipButton.move(1100, 620)
                if lang == "ru":
                    self.skipButton.setStyleSheet('border-image: url("uis/skipbutton.png")')
                elif lang == "kz":
                    self.skipButton.setStyleSheet('border-image: url("uis/skipbutton_kz.png")')
                else:
                    self.skipButton.setStyleSheet('border-image: url("uis/skipbutton_en.png")')

                self.skipButton.setFixedSize(221, 91)
                self.skipButton.clicked.connect(self.next)
                self.bottomLayout.addWidget(self.skipButton, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
                self.skipButton.show()

        self.startTime = None

        self.done = False

        try:
            self.button.clicked.disconnect(self.next)
        except:
            pass
        self.button.clicked.connect(self.beginCapture)
        worker.requestUpdate.connect(self.update)

    def closeEvent(self, event):
        worker.stop("Close event, killing worker")
        thread.quit()
        thread.wait()
        cv2.destroyAllWindows()

    def disconnect(self):
        worker.stop("Disconnect")
        thread.quit()
        thread.wait()
        worker.requestUpdate.disconnect(self.update)
        self.cameraLabel.setPixmap(QPixmap("resources/static/nocamera.jpg"))
        self.startTime = None

    def goBack(self):
        mediaPlayer.stop()
        #print("Going back in", self.ui)

        if not self.done:
            #print("Not done and going back in", self.ui)
            worker.stop("Going back, killing worker")
            thread.quit()
            thread.wait()
            worker.requestUpdate.disconnect(self.update)

            self.cameraLabel.setPixmap(QPixmap("resources/static/nocamera.jpg"))
            self.startTime = None

            cv2.destroyAllWindows()

        currIndex = window.stackedWidget.currentIndex()

        if currIndex == 9 or currIndex == 21 or currIndex == 33:
            goPage(8)
        else:
            goBack()

    def next(self):
        #print(results)
        mediaPlayer.stop()
        worker.stop("Pressed skip button, killing worker")
        self.done = True
        thread.quit()
        thread.wait()

        try:
            worker.requestUpdate.disconnect(self.update)
        except Exception as e:
            print("Exception while trying to disconnect signal from slot in", self.emotion, e)

        cv2.destroyAllWindows()


        nextPage()

    def report(self):
        results[self.level][self.emotion] = self.elapsed * self.done

    def update(self):
        if self.done:
            return

        idx = worker.idx
        data = worker.data
        limit = threshold[self.emotion]
        if idx == 0:
            return

        if self.startTime is None:
            self.startTime = time.time()

        if time.time() - self.startTime > 15.0 and self.skipButton is None:
            self.skipButton = QPushButton()
            if lang == "ru":
                self.skipButton.setStyleSheet('border-image: url("uis/skipbutton.png")')
            elif lang == "kz":
                self.skipButton.setStyleSheet('border-image: url("uis/skipbutton_kz.png")')
            else:
                self.skipButton.setStyleSheet('border-image: url("uis/skipbutton_en.png")')

            self.skipButton.setFixedSize(221, 91)
            self.skipButton.clicked.connect(self.next)
            self.bottomLayout.addWidget(self.skipButton, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
            self.skipButton.show()


        if data[self.emotion][idx - 1] >= limit and time.time() - self.startTime > 3.0:
            self.feedbackPopup.movie.start()
            worker.stop("Performed " + self.emotion + ", killing worker")
            thread.quit()
            thread.wait()
            worker.requestUpdate.disconnect(self.update)

            if lang == "kz":
                ss = 'border-image: url("uis/buttonbg_kz.png")'
            elif lang == "ru":
                ss = 'border-image: url("uis/buttonbg.png")'
            else:
                ss = 'border-image: url("uis/buttonbg_en.png")'

            self.done = True
            self.elapsed = time.time() - self.startTime

            self.report()

            if self.skipButton is not None:
                self.bottomLayout.removeWidget(self.skipButton)
                self.skipButton.close()
                self.skipButton = None

            self.button.setStyleSheet(ss)
            self.button.clicked.connect(self.next)

        else:
            #cv2.imshow('Feed', worker.img)
            img = cv2.cvtColor(worker.img, cv2.COLOR_BGR2RGB)
            converted = QImage(img.data, img.shape[1], img.shape[0], QImage.Format_RGB888)
            pic = QPixmap.fromImage(converted.scaled(640, 480, QtCore.Qt.KeepAspectRatio))
            self.cameraLabel.setPixmap(pic)

    def animate(self, frame):
        self.effect.setOpacity(-(frame+1)**2/900 + (frame+1)/15)

        if frame == self.thumbsUpMovie.frameCount() - 1:
            self.thumbsUpMovie.stop()
            self.thumbsUpLabel.close()

class SelectionMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Выбери свой уровень сложности")
        self.label.setFont(QFont("Bahnschrift", 28, QFont.Bold))
        self.label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

        self.layout.addWidget(self.label)

        self.central = QFrame()
        self.centralLayout = QHBoxLayout()

        self.firstButton = QPushButton()
        self.firstButton.setFixedSize(200, 200)
        self.firstButton.setStyleSheet("border-image: url('uis/first.png')")
        self.firstButton.clicked.connect(partial(goPage, 9))

        self.secButton = QPushButton()
        self.secButton.setFixedSize(200, 200)
        self.secButton.setStyleSheet("border-image: url('uis/second.png')")
        self.secButton.clicked.connect(partial(goPage, 21))

        self.thirdButton = QPushButton()
        self.thirdButton.setFixedSize(200, 200)
        self.thirdButton.setStyleSheet("border-image: url('uis/third.png')")
        self.thirdButton.clicked.connect(partial(goPage, 33))

        self.centralLayout.addWidget(self.firstButton)
        self.centralLayout.addWidget(self.secButton)
        self.centralLayout.addWidget(self.thirdButton)
        self.central.setLayout(self.centralLayout)
        self.layout.addWidget(self.central, alignment=QtCore.Qt.AlignTop)

        self.returnButton = QPushButton()
        self.returnButton.setFixedSize(221, 91);
        self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")

        self.layout.addWidget(self.returnButton, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)

        self.returnButton.clicked.connect(goBack)

        self.setLayout(self.layout)

    def connect(self):
        if lang == "kz":
            self.label.setText("Киындық деңгейін таңдаңыз")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_kz.png');")
        elif lang == "en":
            self.label.setText("Choose the exercise difficulty")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_en.png');")

class ChallengeWidget(QWidget):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.misses = 0

        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.emotion = random.choice(emotions)

        self.central = QFrame()
        self.centralLayout = QHBoxLayout()
        self.central.setLayout(self.centralLayout)


        self.header = QLabel(f"<P>Выбери изображение с эмоцией <big><b>{locale['ru'][self.emotion]}</b></big></P>")
        self.header.setFont(QFont("Bahnschrift", 28))
        self.header.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.header, alignment=QtCore.Qt.AlignCenter)

        self.labels = []

        answerIndex = random.randint(0, level + 1)
        chose = [self.emotion]

        for i in range(level+2):
            if i == answerIndex:
                pick = self.emotion
            else:
                pick = random.choice(list(set(emotions) - set(chose)))

            label = QDynamicLabel(pick)
            label.clicked.connect(self.press)

            chose.append(pick)

            url = os.path.join(os.getcwd(), "resources/challenge/")

            images = [name for name in os.listdir(url) if pick in name]

            pickedImage = random.choice(images)

            pixMap = QPixmap(url + pickedImage)

            label.setFixedSize(300, 300)
            label.setPixmap(pixMap.scaled(label.size(), QtCore.Qt.IgnoreAspectRatio,
                                                               QtCore.Qt.SmoothTransformation))
            self.labels.append(label)
            self.centralLayout.addWidget(label)

        self.layout.addWidget(self.central, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignCenter)

        self.next = QPushButton()
        # self.skipButton.move(1100, 620)
        #self.next.setStyleSheet('border: 4px solid black')
        #self.next.setText("ДАЛЕЕ")
        #self.next.setFont(QFont("Arial Black", 14))
        self.next.setStyleSheet('border-image: url("uis/buttonbg.png")')
        self.next.setFixedSize(221, 91)
        self.next.clicked.connect(nextPage)

        self.bottom = QFrame()
        self.bottomLayout = QHBoxLayout()
        #self.bottomLayout.setSpacing(0)
        #self.bottomLayout.setContentsMargins(0, 0, 0, 0)
        #self.bottomLayout.addStretch(1)

        self.returnButton = QPushButton()
        self.returnButton.setFixedSize(221, 91)
        self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")
        self.returnButton.clicked.connect(goBack)

        self.bottomLayout.addWidget(self.returnButton, alignment=QtCore.Qt.AlignCenter)


        self.bottom.setLayout(self.bottomLayout)
        self.layout.addWidget(self.bottom, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)


        self.setLayout(self.layout)

        self.feedbackPopup = ReactionPopup("resources/gif/thumbs-up.gif", parent=self)
        self.feedbackPopup.move(1500 // 2 - 128, 870 // 2 - 128)

        self.wrongPopup = ReactionPopup("resources/gif/cross.gif", parent=self)
        self.wrongPopup.move(1500 // 2 - 128, 870 // 2 - 128)

    def report(self):
        if self.emotion in results[self.level]['challenges']:
            results[self.level]['challenges'][self.emotion]['misses'] += self.misses
            results[self.level]['challenges'][self.emotion]['hits'] += 1
        else:
            results[self.level]['challenges'][self.emotion]['misses'] = self.misses
            results[self.level]['challenges'][self.emotion]['hits'] = 1

    def connect(self):
        if lang == "kz":
            self.header.setText(f"<P><big><b>{locale['kz'][self.emotion].capitalize()}</b></big> эмоциясы бар суретті таңдап алыңыз</P>")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_kz.png');")
            self.next.setStyleSheet('border-image: url("uis/buttonbg_kz.png")')
        elif lang == "en":
            self.header.setText(
                f"<P>Choose the picture that portrays <big><b>{locale['en'][self.emotion]}</b></big></P>")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_en.png');")
            self.next.setStyleSheet('border-image: url("uis/buttonbg_en.png")')

    def press(self, pick):
        if pick == self.emotion:
            self.feedbackPopup.movie.start()
            self.bottomLayout.addWidget(self.next, alignment=QtCore.Qt.AlignCenter)
        else:
            self.misses += 1
            self.wrongPopup.movie.start()

class CongratulationWidget(QDialog):
    def __init__(self):
        super().__init__()

        self.setObjectName("parentWidget")
        self.setStyleSheet("#parentWidget { border-image: url('uis/congrats.png') 0 0 0 0 stretch stretch;}")

        self.layout = QVBoxLayout()
        self.header = QLabel("Молодец, ты прошел уровень!")
        self.header.setFont(QFont("Bahnschrift", 28))
        self.header.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.header, alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)

        self.bottom = QFrame()
        self.bottomLayout = QHBoxLayout()

        self.returnButton = QPushButton()
        self.returnButton.setFixedSize(221, 91)
        #self.returnButton.setStyleSheet('border: 4px solid black')
        #self.returnButton.setText("НАЗАД")
        #self.returnButton.setFont(QFont("Arial Black", 14))
        self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")
        self.returnButton.clicked.connect(goBack)

        self.bottomLayout.addWidget(self.returnButton)

        self.next = QPushButton()
        #self.next.setStyleSheet('border: 4px solid black')
        #self.next.setText("ДАЛЕЕ")
        #self.next.setFont(QFont("Arial Black", 14))
        self.next.setStyleSheet('border-image: url("uis/buttonbg.png")')
        self.next.setFixedSize(221, 91)
        self.next.clicked.connect(nextPage)
        self.bottomLayout.addWidget(self.next)

        self.bottom.setLayout(self.bottomLayout)

        self.layout.addWidget(self.bottom, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)
        self.setLayout(self.layout)

    def connect(self):
        if lang == "kz":
            self.header.setText("Сен деңгейден өттің, жарайсың!")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_kz.png');")
            self.next.setStyleSheet('border-image: url("uis/buttonbg_kz.png")')
        elif lang == "en":
            self.header.setText("Well done, you completed the level!")
            self.returnButton.setStyleSheet("border-image: url('uis/goback_en.png');")
            self.next.setStyleSheet('border-image: url("uis/buttonbg_en.png")')

class StatisticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.returnButton = QPushButton()
        self.next = QPushButton()
        self.layout = QVBoxLayout()

        self.chart = QChart()
        self.series = QStackedBarSeries()

        surprise = QBarSet("Wonder")
        happy = QBarSet("Happiness")
        neutral = QBarSet("Neutrality")
        angry = QBarSet("Anger")
        sad = QBarSet("Sadness")
        disgust = QBarSet("Disgust")

        self.sets = {
            'surprise': surprise,
            'happy': happy,
            'neutral': neutral,
            'sad': sad,
            'angry': angry,
            'disgust': disgust
        }
        # print(results)
        for level in [0, 1, 2]:
            if not results[level]:
                for barset in self.sets.values():
                    barset.append(0.0)
                continue

            for key, value in results[level].items():
                if type(value) is float:
                    self.sets[key].append(value)
                else:
                    self.sets[key].append(0.0)

        for barset in self.sets.values():
            self.series.append(barset)

        self.chart.addSeries(self.series)
        self.chart.setTitle("Level completion time")
        self.chart.setTitleFont(QFont("Bahnschrift", 16, QFont.Bold))

        axisX = QBarCategoryAxis()
        axisX.append(['First', 'Second', 'Third'])
        axisX.setLabelsFont(QFont("Arial", 12))

        self.chart.addAxis(axisX, Qt.AlignBottom)
        self.series.attachAxis(axisX)
        self.axisY = QValueAxis()
        self.axisY.setMinorTickCount(10)
        #self.axisY.setTickType(QValueAxis.TicksDynamic)
        #self.axisY.setTickAnchor(0.0)
        #self.axisY.setTickInterval(2.0)
        self.axisY.setLabelsFont(QFont("Arial", 12))

        self.chart.addAxis(self.axisY, Qt.AlignLeft)
        self.series.attachAxis(self.axisY)
        self.chart.legend().setVisible(True)
        self.chart.legend().setFont(QFont("Arial", 12))
        self.chart.legend().setAlignment(Qt.AlignRight)

        self.chartView = QChartView(self.chart)
        self.chartView.setFixedSize(900, 700)

        # self.next.setText("ДАЛЕЕ")
        # self.next.setFont(QFont("Arial Black", 14))
        # self.next.setStyleSheet('border: 4px solid black')
        self.layout.addWidget(self.chartView, alignment=QtCore.Qt.AlignCenter)
        self.setLayout(self.layout)

    def connect(self):
        print("Updated")

        upperRange = 0

        for level in [0, 1, 2]:
            if not results[level]:
                for barset in self.sets.values():
                    barset.replace(level, 0.0)
                continue

            top = 0

            for key, value in results[level].items():
                if type(value) is float:
                    self.sets[key].replace(level, value)
                    top += value
                else:
                    self.sets[key].replace(level, 0.0)

            upperRange = max(top, upperRange)

        self.axisY.setRange(0.0, upperRange)
        #self.axisY.setTickInterval(int(upperRange / 10))

        self.chart.removeSeries(self.series)
        self.chart.addSeries(self.series)

        self.chart.update()
        self.chartView.update()
        self.update()

class EndStatisticsWidget(StatisticsWidget):
    def __init__(self):
        super().__init__()

    def connect(self):
        super().connect()
        self.bottom = QFrame()
        self.bottomLayout = QHBoxLayout()

        self.returnButton.setFixedSize(221, 91)
        self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")
        self.returnButton.clicked.connect(goBack)

        self.next.setStyleSheet('border-image: url("uis/buttonbg.png")')
        self.next.setFixedSize(221, 91)
        self.next.clicked.connect(nextPage)

        self.bottomLayout.addWidget(self.returnButton, alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)
        self.bottomLayout.addWidget(self.next, alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignBottom)

        self.bottom.setLayout(self.bottomLayout)

        self.layout.addWidget(self.bottom, alignment=QtCore.Qt.AlignBottom | QtCore.Qt.AlignCenter)

        self.setLayout(self.layout)

class PerformanceWidget(QWidget):
    def __init__(self, level):
        super().__init__()
        self.level = level
        self.layout = QVBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.SeriesAnimations)

        self.barset = QBarSet("Эмоции")

        self.series = QStackedBarSeries()

        for key in emotions:
            if not results[self.level][key]:
                self.barset.append(0.0)
            else:
                self.barset.append(results[self.level][key])

        self.series.append(self.barset)
        # ['happy', 'angry', 'sad', 'surprise', 'disgust', 'neutral']

        #categories = QBarCategoryAxis()
        #categories.append(['Счастье', 'Злость', 'Грусть', 'Удивление', 'Отвращение', 'Нейтрал'])
        #categories.setLabelsFont(QFont("Arial", 12))


        self.axisY = QValueAxis()
        self.axisY.setMinorTickCount(10)
        self.axisY.setLabelsFont(QFont("Arial", 12))
        self.axisY.setTitleText('Time / seconds')
        self.chart.addAxis(self.axisY, Qt.AlignLeft)
        self.series.attachAxis(self.axisY)

        self.chart.addSeries(self.series)
        self.chart.setTitle("Level statistics")
        self.chart.setTitleFont(QFont("Bahnschrift", 16, QFont.Bold))

        self.axisX = QBarCategoryAxis()

        self.axisX.append(["Happiness", "Anger", "Sadness", "Wonder", "Disgust", "Neutrality"])

        self.chart.legend().setVisible(False)
        #self.chart.legend().setAlignment(Qt.AlignBottom)
        #self.chart.legend().setFont(QFont("Arial", 12))
        self.chart.setAxisX(self.axisX)

        self.chartview = QChartView(self.chart)
        self.chartview.setChart(self.chart)
        self.chartview.setFixedSize(900, 700)

        self.next = QPushButton()
        self.returnButton = QPushButton()

        self.returnButton.setFixedSize(221, 91)
        self.returnButton.setStyleSheet("border-image: url('uis/goback.png');")
        self.returnButton.clicked.connect(goBack)

        self.next.setStyleSheet('border-image: url("uis/buttonbg.png")')
        self.next.setFixedSize(221, 91)
        self.next.clicked.connect(nextPage)

        self.bottom = QFrame()
        self.bottomLayout = QHBoxLayout()

        self.bottomLayout.addWidget(self.returnButton, alignment=Qt.AlignCenter | Qt.AlignBottom)
        self.bottomLayout.addWidget(self.next, alignment=Qt.AlignCenter | Qt.AlignBottom)

        self.bottom.setLayout(self.bottomLayout)

        self.layout.addWidget(self.chartview, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.bottom, alignment=Qt.AlignCenter)
        self.setLayout(self.layout)

    def connect(self):
        print("Updated performance")
        if lang == "kz":
            self.returnButton.setStyleSheet("border-image: url('uis/goback_kz.png');")
            self.next.setStyleSheet('border-image: url("uis/buttonbg_kz.png")')
        elif lang == "en":
            self.returnButton.setStyleSheet("border-image: url('uis/goback_en.png');")
            self.next.setStyleSheet('border-image: url("uis/buttonbg_en.png")')

        upperLimit = 0.0

        for idx, key in enumerate(emotions):
            if results[self.level][key]:
                self.barset.replace(idx, results[self.level][key])
                upperLimit = max(upperLimit, results[self.level][key])

        self.axisY.setRange(0.0, upperLimit)

        self.chart.removeSeries(self.series)
        self.chart.addSeries(self.series)


        self.chart.update()
        self.chartview.update()
        self.update()

class Drawer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setContentsMargins(0, 0, 0, 0)
        self._maximum_height = 200

        self.palette = QPalette()
        self.palette.setColor(QPalette.Window, QColor(240, 240, 240)) #QColor(240, 240, 240)
        self.setAutoFillBackground(True)
        self.setPalette(self.palette)

        self._animation = QtCore.QPropertyAnimation(self, b"height")
        self._animation.setStartValue(30)
        self._animation.setEndValue(self._maximum_height)
        self._animation.setDuration(400)
        self._animation.valueChanged.connect(self.setFixedHeight)
        #self.hide()

    @property
    def maximum_height(self):
        return self._maximum_height

    @maximum_height.setter
    def maximum_height(self, h):
        self._maximum_height = h
        self._animation.setEndValue(self._maximum_height)

    def open(self):
        self._animation.setDirection(QtCore.QAbstractAnimation.Forward)
        self._animation.start()
        self.show()

    def close(self):
        self._animation.setDirection(QtCore.QAbstractAnimation.Backward)
        self._animation.start()

    def enterEvent(self, a0: QtCore.QEvent) -> None:
        self.open()

    def leaveEvent(self, a0: QtCore.QEvent) -> None:
        self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        path = QPainterPath()
        #pen = QPen(Qt.black)

        path.addRect(0, self.height() - 4, self.width(), 4)
        painter.fillPath(path, Qt.black)
        painter.drawPath(path)

        super().paintEvent(event)

class LanguageChooser(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.label = QLabel("Выберите язык / Тілді таңдаңыз / Choose your language")
        self.label.setFont(QFont("Bahnschrift", 28, QFont.Bold))
        self.label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

        self.central = QFrame()
        self.centralLayout = QHBoxLayout()

        self.firstButton = QPushButton()
        self.firstButton.setFixedSize(200, 200)
        self.firstButton.setStyleSheet("border-image: url('uis/ru.png')")
        self.firstButton.clicked.connect(partial(setLanguage, "ru"))

        self.secondButton = QPushButton()
        self.secondButton.setFixedSize(200, 200)
        self.secondButton.setStyleSheet("border-image: url('uis/kz.png')")
        self.secondButton.clicked.connect(partial(setLanguage, "kz"))

        self.thirdButton = QPushButton()
        self.thirdButton.setFixedSize(200, 200)
        self.thirdButton.setStyleSheet("border-image: url('uis/en.png')")
        self.thirdButton.clicked.connect(partial(setLanguage, "en"))

        self.layout.addWidget(self.label)
        self.centralLayout.addWidget(self.firstButton)
        self.centralLayout.addWidget(self.secondButton)
        self.centralLayout.addWidget(self.thirdButton)
        self.central.setLayout(self.centralLayout)
        self.layout.addWidget(self.central, alignment=QtCore.Qt.AlignTop)

        self.setLayout(self.layout)

class MainWidget(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        pages = [LanguageChooser(),
                 GuidingScreen("uis/mainscreen.ui"), GuidingScreen("uis/training1.ui"),
                 GuidingScreen("uis/training2.ui"),
                 GuidingScreen("uis/training3.ui"), GuidingScreen("uis/training4.ui"),
                 GuidingScreen("uis/training5.ui"),
                 GuidingScreen("uis/training7.ui"), SelectionMenu()]

        for level in range(3):
            bag = [TrainingScreen("uis/testing1.ui", "angry", level), TrainingScreen("uis/testing2.ui", "happy", level),
                   TrainingScreen("uis/testing3.ui", "sad", level),
                   TrainingScreen("uis/testing4.ui", "neutral", level), TrainingScreen("uis/testing5.ui", "disgust", level),
                   TrainingScreen("uis/testing6.ui", "surprise", level)]

            random.seed(time.time_ns() % 1000)
            random.shuffle(bag)
            bag += [PerformanceWidget(level), CongratulationWidget(), ChallengeWidget(level), ChallengeWidget(level),
                    ChallengeWidget(level), ChallengeWidget(level)]
            pages += bag

        pages += [EndStatisticsWidget(), GuidingScreen("uis/finalscreen.ui"), StatisticsWidget()]

        for page in pages:
            self.addWidget(page)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon('icon.ico'))
        self.setWindowTitle("Drive Beyond")
        self.resize(1500, 870)


        self.layout = QVBoxLayout()
        self.drawer = Drawer(self)

        self.stackedWidget = MainWidget()

        self.drawerMainLayout = QVBoxLayout()
        self.drawerMainLayout.setContentsMargins(0, 8, 0, 0)

        self.drawerBar = QFrame()
        self.drawerLayout = QHBoxLayout()
        self.drawerLayout.addStretch(1)
        self.drawerLayout.setSpacing(20)
        self.drawerLayout.setSizeConstraint(QLayout.SetMaximumSize)

        self.homeButton = QPushButton()
        self.homeButton.setFixedSize(91, 91)
        self.homeButton.setStyleSheet("border-image: url('uis/home.png')")
        self.homeButton.clicked.connect(partial(goPage, 0))

        self.performanceButton = QPushButton()
        self.performanceButton.setFixedSize(91, 91)
        self.performanceButton.setStyleSheet("border-image: url('uis/statistics.png')")
        self.performanceButton.clicked.connect(partial(goPage, 47))

        self.drawerLayout.addWidget(self.homeButton, alignment=Qt.AlignCenter)
        self.drawerLayout.addWidget(self.performanceButton, alignment=Qt.AlignCenter)
        self.drawerLayout.addStretch(1)
        self.drawerBar.setLayout(self.drawerLayout)

        pullLabel = QLabel()
        pullLabel.setFixedSize(32, 16)
        pullLabel.setPixmap(QPixmap("uis/dropdown.png").scaled(pullLabel.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation))

        self.drawerMainLayout.addWidget(pullLabel, alignment=Qt.AlignCenter)
        self.drawerMainLayout.addWidget(self.drawerBar)

        self.drawer.setLayout(self.drawerMainLayout)

        self.show()

        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 30, 0, 0)
        self.layout.addWidget(self.stackedWidget)

        self.setLayout(self.layout)
        self.drawer.raise_()

    def resizeEvent(self, event):
        self.drawer.setFixedWidth(self.width())
        super().resizeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
