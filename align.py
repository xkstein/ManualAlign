#!/usr/bin/env python3

# TODO:
# Add commandline argument support for like all of the vars that need to be set up
# make an object that handles all the io, but I kinda want to refrain for like just making this OO for the sake of OO

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QFileDialog, QAction
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

folder = 'images/2312/'
TRACE_PATH =    f'{folder}trace_new_clean_2hr2312 numbered.png'
TRACE_PATH_SAVE = f'{folder}aligned/2hr2312_trace.png'
RAW_PATH =      f'{folder}2HR_Al_100nm_2312_F6_1.tif'
RAW_PATH_SAVE = None
PTS_CSV_READ = f'{folder}aligned/2hr2312_1.csv'
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

#raw = io.imread('roitest.png', as_gray=True)
raw = io.imread(paths.RAW_PATH, as_gray=True)
if raw.dtype != np.uint8:
    raw = np.uint8(255/np.max(raw) * raw)
trace = io.imread(paths.TRACE_PATH, as_gray=True)
if trace.dtype != np.uint8:
    trace = np.uint8(255/np.max(trace) * trace)

align = []

#pts = np.zeros((2, 5, 2))

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
    print(f'Saving points to {csv_fname}')
    pts = np.zeros((2, 5, 2))
    for i in range(2):
        pts[i,:,:] = image_plot[i].points
        image_plot[i].setPoints()
    [c_pos, c_size] = get_crop(image_plot[2])

    with open(csv_fname, mode='w') as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow([c_pos[0], c_pos[1], c_size[0], c_size[1]])
        for pt in range(5):
            csv_writer.writerow([pts[0, pt, 0], pts[0, pt, 1], pts[1, pt, 0], pts[1, pt, 1]])

def cropnsave(fname, img, c_pos, c_size):
    if fname is None:
        print('Image name not defined, cannot save')
        return 0
    if int(c_pos[1] + c_size[0]) > img.shape[0] or int(c_pos[0] + c_size[1]) > img.shape[1]:
        print(f'Oversized crop, adding black border to {fname}')
        matt = np.zeros((int(c_pos[1] + c_size[0]), int(c_pos[0] + c_size[1])), dtype=np.uint8)
        matt[:img.shape[0], :img.shape[1]] = img[:matt.shape[0], :matt.shape[1]]
        # NOTE: you definitely could use something other than qt as your export plugin, I found that the default was some 14x slower
        io.imsave(fname, matt[int(c_pos[1]):int(c_pos[1]+c_size[0]), \
                                            int(c_pos[0]):int(c_pos[0]+c_size[1])], plugin='qt')
    else:
        io.imsave(fname, img[int(c_pos[1]):int(c_pos[1]+c_size[0]), \
                                            int(c_pos[0]):int(c_pos[0]+c_size[1])], plugin='qt')

def get_crop(plot):
    pos = np.array([plot.roi.pos().x(), plot.roi.pos().y()])
    dimensions = np.array([plot.roi.size().x(), plot.roi.size().y()])
    return [pos, dimensions]

def key_press(event):
    global align, raw

    # Loads points
    if event.text() == 'l':
        [pts, c_pos, c_size] = read_csv(PTS_CSV_READ)
        for i in [0, 1]:
            image_plot[i].points = pts[i, :, :]
            image_plot[i].setPoints()
        image_plot[2].roi.setPos(c_pos[0], c_pos[1], update=False)
        image_plot[2].roi.setSize(c_size)

    # Saves the selected points
    if event.text() == 'p':
        if PTS_CSV_SAVE is None:
            PTS_CSV_SAVE = QFileDialog.getSaveFileName(win, 'Save file', '.')[0]
            save_csv(PTS_CSV_SAVE)
        else:
            save_csv(PTS_CSV_SAVE)

    # Opens a file
    elif event.text() == 'o':
        paths.RAW_PATH = QFileDialog.getOpenFileName(win, 'Open file', '.', "Image files (*.jpg *.gif *.png *.tif)")[0]
        raw = io.imread(paths.RAW_PATH, as_gray=True)
        if raw.dtype != np.uint8:
            raw = np.uint8(255/np.max(raw) * raw)
        image_plot[1].setImage(raw)
        paths.RAW_PATH_SAVE = None
        paths.PTS_CSV_SAVE = None

    # Locks ROI
    elif event.text() == 'm':
        image_plot[2].roi.translatable = (image_plot[2].roi.translatable != True)

    # Does transformation with selected points
    elif event.text() == 'a':
        pts = np.zeros((2, 5, 2))
        for i in range(2):
            pts[i, :, :] = image_plot[i].points
        [c_pos, c_size] = get_crop(image_plot[2])

        non0_pts = (pts != 0)
        selected_pts = np.logical_or(non0_pts[:,:,0], non0_pts[:,:,1])
        overlapping = np.logical_and(selected_pts[0], selected_pts[1])
        
        ref_pts = pts[0, overlapping]
        trans_pts = pts[1, overlapping]

        if np.sum(overlapping) > 2:
            print(f"Using {np.sum(overlapping)} point alignment...")
            align = transform_5pt(image_plot[0].image, ref_pts, trans_pts, (trace.shape[1], trace.shape[0]))
        elif np.sum(overlapping) == 2:
            print("Warning: Using 2 point alignment (suboptimal)...")
            align = transform_2pt(raw, ref_pts, trans_pts, (trace.shape[1], trace.shape[0]))
        elif np.sum(overlapping) < 2:
            print("Not enough valid points selected")
            return 0

        # The fused image on the right:
        fuse = np.zeros((align.shape[0], align.shape[1], 3))
        fuse[:,:,:] = np.dstack((align,align,align))
        fuse[trace == 0, 0] = 255
        fuse[trace == 0, 1] = 0
        fuse[trace == 0, 2] = 0
        image_plot[2].setImage(fuse)
        image_plot[2].roi.setSize(pg.Point(c_size[0], c_size[1]))

    # Saves aligned images
    elif event.text() == 's':
        [c_pos, c_size] = get_crop(image_plot[2])
        if paths.RAW_PATH_SAVE is None:
            paths.RAW_PATH_SAVE = QFileDialog.getSaveFileName(win, 'Save file', '.')[0]
            #RAW_PATH_SAVE = QFileDialog.getSaveFileName(central_win, 'Save file', '.')[0]
            if paths.PTS_CSV_SAVE is None:
                paths.PTS_CSV_SAVE = f'{RAW_PATH_SAVE[:-4]}.csv'
            
        cropnsave(paths.RAW_PATH_SAVE, align, c_pos, c_size)
        cropnsave(paths.TRACE_PATH_SAVE, trace, c_pos, c_size)
      
class Window(QMainWindow):
    sigKeyPress = pyqtSignal(object)
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Manual Align")

        self.central_win = QWidget()
        self.layout = QHBoxLayout()
        self.central_win.setLayout(self.layout)
        self.setCentralWidget(self.central_win)

        menu = self.menuBar()
        fileMenu = menu.addMenu("&File")

        openRawAction = QAction("&Open Image", self)
        openRawAction.setData("blechelshkj")
        openRawAction.triggered.connect(self.openRaw)
        fileMenu.addAction(openRawAction)
        fileMenu.addAction("Open Tracing")
        fileMenu.addAction("Open Points CSV")
        fileMenu.addAction("Save Alignment...")
        fileMenu.addAction("Save Points to CSV...")

    def addWidget(self, widget):
        self.layout.addWidget(widget)

    def openRaw(self):
        paths.RAW_PATH = QFileDialog.getOpenFileName(win, 'Open file', '.', "Image files (*.jpg *.gif *.png *.tif)")[0]
        image_plot[1].setImage(paths.RAW_PATH)

    def openTrace(self):
        paths.TRACE_PATH = QFileDialog.getOpenFileName(win, 'Open file', '.', "Image files (*.jpg *.gif *.png *.tif)")[0]
        image_plot[0].setImage(paths.TRACE_PATH)

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication([])
#win = QMainWindow()
win = Window()

plot_has_roi=[False, False, True]
image_plot = []

for i, use_roi in enumerate(plot_has_roi):
    plot = ImagePlot(use_roi = use_roi)
    plot.sigKeyPress.connect(key_press)
    win.addWidget(plot)
    image_plot.append(plot)

image_plot[0].setImage(paths.TRACE_PATH)
image_plot[1].setImage(paths.RAW_PATH)

# You can access points by accessing image_plot1.points
win.show()

if (sys.flags.interactive != 1) or not hasattr(Qt.QtCore, "PYQT_VERSION"):
    QApplication.instance().exec_()

