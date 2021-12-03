#!/usr/bin/env python3

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QGridLayout, QFileDialog, QAction, QLineEdit, QLabel, QFormLayout
from ImagePlot import ImagePlot
from transformations import *
import pyqtgraph as pg
from skimage import io
import numpy as np
import csv
import sys
import time
import pdb
from dataclasses import dataclass

folder = 'images/2530/'
TRACE_PATH = None
TRACE_PATH_SAVE = None
RAW_PATH = None
RAW_PATH_SAVE = None
PTS_CSV_READ = None
PTS_CSV_SAVE = None

@dataclass
class FilePaths:
    # I need an adult
    TRACE_PATH: str = None
    TRACE_PATH_SAVE: str = None
    RAW_PATH: str = None
    RAW_PATH_SAVE: str = None
    PTS_CSV_READ: str = None
    PTS_CSV_SAVE: str = None

paths = FilePaths(TRACE_PATH, TRACE_PATH_SAVE, RAW_PATH, RAW_PATH_SAVE, PTS_CSV_READ, PTS_CSV_SAVE)

def read_csv(csv_fname):
    print(f'Loading points from {csv_fname}')
    c_pos = np.zeros(2)
    c_size = np.zeros(2)
    pts = np.zeros((2, 5, 2))
    with open(csv_fname, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                c_pos[0] = row[0]
                c_pos[1] = row[1]
                c_size[0] = float(row[2])
                c_size[1] = float(row[3])
            else:
                pts[0, line_count - 1, 0] = row[0]
                pts[0, line_count - 1, 1] = row[1]
                pts[1, line_count - 1, 0] = row[2]
                pts[1, line_count - 1, 1] = row[3]
            line_count += 1
    return [pts, c_pos, c_size]

def save_csv(csv_fname):
    if csv_fname is None:
        print('CSV Points save path not defined')
        return 0

    print(f'Saving points to {csv_fname}')
    pts = np.zeros((2, 5, 2))
    for i in range(2):
        pts[i,:,:] = image_plot[i].points
        image_plot[i].setPoints()
    [c_pos, c_size] = image_plot[2].getCrop()

    with open(csv_fname, mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow([c_pos[0], c_pos[1], c_size[0], c_size[1]])
        for pt in range(5):
            csv_writer.writerow([pts[0, pt, 0], pts[0, pt, 1], pts[1, pt, 0], pts[1, pt, 1]])

# TODO: re-implement all of these functions as toolbar functions
def key_press(event):
    # Locks ROI
    elif event.text() == 'm':
        image_plot[2].roi.translatable = (image_plot[2].roi.translatable != True)

    # Does transformation with selected points
    elif event.text() == 'a':
        pts = np.zeros((2, 5, 2))
        for i in range(2):
            pts[i, :, :] = image_plot[i].points
        [c_pos, c_size] = image_plot[2].getCrop()

        non0_pts = (pts != 0)
        selected_pts = np.logical_or(non0_pts[:,:,0], non0_pts[:,:,1])
        overlapping = np.logical_and(selected_pts[0], selected_pts[1])
        
        ref_pts = pts[0, overlapping]
        trans_pts = pts[1, overlapping]
        print(image_plot[0].image.shape[::-1])

        if np.sum(overlapping) > 2:
            print(f"Using {np.sum(overlapping)} point alignment...")
            align = transform_5pt(image_plot[1].image, ref_pts, trans_pts, \
                    image_plot[0].image.shape[::-1])
        elif np.sum(overlapping) == 2:
            print("Warning: Using 2 point alignment (suboptimal)...")
            align = transform_2pt(image_plot[1].image, ref_pts, trans_pts, image_plot[0].image.shape[::-1])
        elif np.sum(overlapping) < 2:
            print("Not enough valid points selected")
            return 0

        # The fused image on the right:
        image_plot[2].setImage(align, disp=False)
        image_plot[2].overlayImage(image_plot[0].image)
        image_plot[2].roi.setSize(pg.Point(c_size[0], c_size[1]))
      
class Window(QMainWindow):
    sigKeyPress = pyqtSignal(object)
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Manual Align")

        self.central_win = QWidget()
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)


        # Setting up the image plots
        self.image_plot = []

        plot = ImagePlot()
        plot.sigKeyPress.connect(key_press)
        self.layout.addWidget(plot, 0, 0, 2, 1)
        self.image_plot.append(plot)

        plot = ImagePlot()
        plot.sigKeyPress.connect(key_press)
        self.layout.addWidget(plot, 2, 0, 2, 1)
        self.image_plot.append(plot)

        plot = ImagePlot(use_roi = True)
        plot.sigKeyPress.connect(key_press)
        self.layout.addWidget(plot, 0, 1, 4, 2)
        self.image_plot.append(plot)
#        self.layout.setColumnStretch(1, 0)
        #self.layout = QHBoxLayout()

        '''
        # Setting up the plot file name selector thing
        label1 = QLabel("Name")
        edit1 = QLineEdit()
        self.form = QFormLayout()
        self.form.addRow(label1, edit1)
        self.layout.addLayout(self.form, 3,1,2,1)
        '''

        self.central_win.setLayout(self.layout)
        self.setCentralWidget(self.central_win)

        menu = self.menuBar()
        fileMenu = menu.addMenu("&File")

        openRawAction = QAction("&Open Image", self)
        openRawAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_O))
        openRawAction.triggered.connect(self.openRaw)
        fileMenu.addAction(openRawAction)

        openTraceAction = QAction("&Open Tracing", self)
        openTraceAction.triggered.connect(self.openTrace)
        fileMenu.addAction(openTraceAction)

        openPointsAction = QAction("&Open Points CSV", self)
        openPointsAction.triggered.connect(self.openPoints)
        openPointsAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_L))
        fileMenu.addAction(openPointsAction)

        saveAction = QAction("&Save Aligned Image...", self)
        saveAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
        saveAction.triggered.connect(self.saveImage)
        fileMenu.addAction(saveAction)

        saveTraceAction = QAction("&Save Trace Aligned Image...", self)
#        saveTraceAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_T))
        saveTraceAction.triggered.connect(self.saveTrace)
        fileMenu.addAction(saveTraceAction)

        savePointsAction = QAction("&Save Points CSV...", self)
        savePointsAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_P))
        savePointsAction.triggered.connect(self.savePoints)
        fileMenu.addAction(savePointsAction)

    def setLayout(self):
        self.central_win.setLayout(self.layout)
        self.setCentralWidget(self.central_win)

    def openRaw(self):
        if select := QFileDialog.getOpenFileName(win, 'Open file', '.', "Image files (*.jpg *.gif *.png *.tif)")[0]:
            paths.RAW_PATH = select
            image_plot[1].setImage(paths.RAW_PATH)
            paths.PTS_CSV_SAVE = None
            paths.RAW_PATH_SAVE = None

    def openTrace(self):
        if select := QFileDialog.getOpenFileName(win, 'Open file', '.', "Image files (*.jpg *.gif *.png *.tif)")[0]:
            paths.TRACE_PATH = select
            image_plot[0].setImage(paths.TRACE_PATH)
            paths.TRACE_PATH_SAVE = None

    def openPoints(self):
        if select := QFileDialog.getOpenFileName(win, 'Open file', '.', "CSV File(*.csv)")[0]:
            paths.PTS_CSV_READ = select
            [pts, c_pos, c_size] = read_csv(paths.PTS_CSV_READ)
            for i in [0, 1]:
                image_plot[i].points = pts[i, :, :]
                image_plot[i].setPoints()
            image_plot[2].roi.setPos(c_pos[0], c_pos[1], update=False)
            image_plot[2].roi.setSize(c_size)
    
    def saveImage(self):
        [c_pos, c_size] = image_plot[2].getCrop()
        if paths.RAW_PATH_SAVE is None:
            if select := QFileDialog.getSaveFileName(win, 'Save Aligned Image', '.')[0]:
                paths.RAW_PATH_SAVE = select
                if paths.PTS_CSV_SAVE is None:
                    paths.PTS_CSV_SAVE = f'{select[:-4]}.csv'

        image_plot[2].saveImage(paths.RAW_PATH_SAVE, c_pos, c_size)

    def saveTrace(self):
        [c_pos, c_size] = image_plot[2].getCrop()
        if paths.TRACE_PATH_SAVE is None:
            if select := QFileDialog.getSaveFileName(win, 'Save Aligned Tracing', '.')[0]:
                paths.TRACE_PATH_SAVE = select
            
        image_plot[0].saveImage(paths.TRACE_PATH_SAVE, c_pos, c_size)

    def savePoints(self):
        if paths.PTS_CSV_SAVE is None:
            if select := QFileDialog.getSaveFileName(win, 'Save file', '.')[0]:
                paths.PTS_CSV_SAVE = select
        
        save_csv(paths.PTS_CSV_SAVE)

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication([])
win = Window()

image_plot = win.image_plot

if paths.TRACE_PATH is not None:
    image_plot[0].setImage(paths.TRACE_PATH)

if paths.RAW_PATH is not None:
    image_plot[1].setImage(paths.RAW_PATH)

# You can access points by accessing image_plot1.points
win.show()

if (sys.flags.interactive != 1) or not hasattr(Qt.QtCore, "PYQT_VERSION"):
    QApplication.instance().exec_()

