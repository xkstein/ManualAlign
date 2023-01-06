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
import logging
from dataclasses import dataclass
from functools import partialmethod
from pathlib import Path

logging.basicConfig(filename='align.log', filemode='w', level=logging.DEBUG)

@dataclass
class FilePaths:
    # I need an adult
    REFERENCE_PATH: str = None
    REFERENCE_PATH_SAVE: str = None
    RAW_PATH: str = None
    RAW_PATH_SAVE: str = None
    PTS_CSV_READ: str = None
    PTS_CSV_SAVE: str = None

# Set default values here
paths = FilePaths()

def read_csv(csv_fname):
    logging.info(f'Loading points from {csv_fname}')
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
        logging.error('CSV Points save path not defined')
        return 0

    logging.info(f'Saving points to {csv_fname}')
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

class Window(QMainWindow):
    sigKeyPress = pyqtSignal(object)
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Manual Align")
        self.file_dialog = QFileDialog()
        self.file_dialog.setFileMode(QFileDialog.AnyFile)

        self.central_win = QWidget()
        self.layout = QGridLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setVerticalSpacing(0)
        self.layout.setHorizontalSpacing(0)

        # Setting up the image plots
        self.image_plot = []

        plot = ImagePlot()
        plot.sigKeyPress.connect(self.keyPress)
        self.layout.addWidget(plot, 0, 0, 2, 1)
        self.image_plot.append(plot)

        plot = ImagePlot()
        plot.sigKeyPress.connect(self.keyPress)
        self.layout.addWidget(plot, 2, 0, 2, 1)
        self.image_plot.append(plot)

        plot = ImagePlot(use_roi=True, select_pts=False)
        self.layout.addWidget(plot, 0, 1, 4, 2)
        self.image_plot.append(plot)

        self.central_win.setLayout(self.layout)
        self.setCentralWidget(self.central_win)

        menu = self.menuBar()
        fileMenu = menu.addMenu("&File")
        editMenu = menu.addMenu("&Edit")

        openRawAction = QAction("&Open Image", self)
        openRawAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_O))
        openRawAction.triggered.connect(self.openRaw)
        fileMenu.addAction(openRawAction)

        openReferenceAction = QAction("&Open Reference Image", self)
        openReferenceAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_R))
        openReferenceAction.triggered.connect(self.openReference)
        fileMenu.addAction(openReferenceAction)

        openPointsAction = QAction("&Open Points CSV", self)
        openPointsAction.triggered.connect(self.openPoints)
        openPointsAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_L))
        fileMenu.addAction(openPointsAction)

        saveFullAction = QAction("&Save Aligned Image...", self)
        saveFullAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_S))
        saveFullAction.triggered.connect(self.saveFullImage)
        fileMenu.addAction(saveFullAction)

        saveCropAction = QAction("&Save Cropped Aligned Image...", self)
        saveCropAction.setShortcut(QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_S))
        saveCropAction.triggered.connect(self.saveCropImage)
        fileMenu.addAction(saveCropAction)

        saveReferenceAction = QAction("&Save Cropped Reference Image...", self)
        saveReferenceAction.triggered.connect(self.saveReference)
        fileMenu.addAction(saveReferenceAction)

        savePointsAction = QAction("&Save Points CSV...", self)
        savePointsAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_P))
        savePointsAction.triggered.connect(self.savePoints)
        fileMenu.addAction(savePointsAction)

        alignAction = QAction("&Align", self)
        alignAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_A))
        alignAction.triggered.connect(self.align)
        editMenu.addAction(alignAction)

        clearPointsAction = QAction("&Clear Points", self)
        clearPointsAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_X))
        clearPointsAction.triggered.connect(self.clearPoints)
        editMenu.addAction(clearPointsAction)

        lockROIAction = QAction("&Lock ROI", self, checkable=True)
        lockROIAction.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_M))
        lockROIAction.triggered.connect(self.lockROI)
        editMenu.addAction(lockROIAction)

    def keyPress(self, event):
        if ( event.text().isdigit() and int(event.text()) <= 5 
                                    and int(event.text()) > 0 ):
            pti = int(event.text()) - 1
            for plot in self.image_plot:
                plot.pti = pti

    def setLayout(self):
        self.central_win.setLayout(self.layout)
        self.setCentralWidget(self.central_win)

    def openRaw(self):
        self.file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        self.file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.tif)")
        if self.file_dialog.exec_():
            select = self.file_dialog.selectedFiles()[0]
            self.file_dialog.setDirectory(str(Path(select).parent))

            paths.RAW_PATH = select
            image_plot[1].setImage(paths.RAW_PATH)
            paths.PTS_CSV_SAVE = None
            paths.RAW_PATH_SAVE = None

    def openReference(self):
        self.file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        self.file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.tif)")
        if self.file_dialog.exec_():
            select = self.file_dialog.selectedFiles()[0]
            self.file_dialog.setDirectory(str(Path(select).parent))

            paths.REFERENCE_PATH = select
            image_plot[0].setImage(paths.REFERENCE_PATH)
            paths.REFERENCE_PATH_SAVE = None

    def openPoints(self):
        self.file_dialog.setAcceptMode(QFileDialog.AcceptOpen)
        self.file_dialog.setNameFilter("CSV File (*.csv)")
        if self.file_dialog.exec_():
            select = self.file_dialog.selectedFiles()[0]

            paths.PTS_CSV_READ = select
            [pts, c_pos, c_size] = read_csv(paths.PTS_CSV_READ)
            for i in [0, 1]:
                image_plot[i].points = pts[i, :, :]
                image_plot[i].setPoints()
            image_plot[2].roi.setPos(c_pos[0], c_pos[1], update=False)
            image_plot[2].roi.setSize(c_size)

    def saveAlignedImage(self, crop: bool):
        if paths.RAW_PATH_SAVE is None:
            self.file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            self.file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.tif)")
            if self.file_dialog.exec_():
                select = self.file_dialog.selectedFiles()[0]
                self.file_dialog.setDirectory(str(Path(select).parent))

                paths.RAW_PATH_SAVE = select
                if paths.PTS_CSV_SAVE is None:
                    paths.PTS_CSV_SAVE = f'{select[:-4]}.csv'

        [c_pos, c_size] = [None, None]
        if crop:
            [c_pos, c_size] = image_plot[2].getCrop()

        try:
            image_plot[2].saveImage(paths.RAW_PATH_SAVE, c_pos=c_pos, \
                                    c_size=c_size)
        except Exception as e:
            paths.RAW_PATH_SAVE = None
            paths.PTS_CSV_SAVE = None
            raise e

    saveFullImage = partialmethod(saveAlignedImage, False)
    saveCropImage = partialmethod(saveAlignedImage, True)

    def saveReference(self):
        [c_pos, c_size] = image_plot[2].getCrop()
        if paths.REFERENCE_PATH_SAVE is None:
            self.file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            self.file_dialog.setNameFilter("Images (*.png *.xpm *.jpg *.tif)")
            if self.file_dialog.exec_():
                select = self.file_dialog.selectedFiles()[0]
                self.file_dialog.setDirectory(str(Path(select).parent))

                paths.REFERENCE_PATH_SAVE = select
            
        image_plot[0].saveImage(paths.REFERENCE_PATH_SAVE, c_pos, c_size)

    def savePoints(self):
        if paths.PTS_CSV_SAVE is None:
            self.file_dialog.setAcceptMode(QFileDialog.AcceptSave)
            self.file_dialog.setNameFilter("CSV File (*.csv)")
            if self.file_dialog.exec_():
                select = self.file_dialog.selectedFiles()[0]

                paths.PTS_CSV_SAVE = select
        
        save_csv(paths.PTS_CSV_SAVE)

    def align(self):
        pts = np.zeros((2, 5, 2))
        for i in range(2):
            pts[i, :, :] = self.image_plot[i].points
        [c_pos, c_size] = self.image_plot[2].getCrop()

        non0_pts = (pts != 0)
        selected_pts = np.logical_or(non0_pts[:,:,0], non0_pts[:,:,1])
        overlapping = np.logical_and(selected_pts[0], selected_pts[1])
        
        ref_pts = pts[0, overlapping]
        trans_pts = pts[1, overlapping]

        if np.sum(overlapping) > 2:
            logging.info(f"Using {np.sum(overlapping)} point alignment...")
            align = transform_5pt(self.image_plot[1].image, ref_pts, trans_pts,
                                  self.image_plot[0].image.shape[::-1])
        elif np.sum(overlapping) == 2:
            logging.warning("Warning: Using 2 point alignment (suboptimal)...")
            align = transform_2pt(self.image_plot[1].image, ref_pts, trans_pts,
                                  self.image_plot[0].image.shape[::-1])
        elif np.sum(overlapping) < 2:
            logging.error("Not enough valid points selected")
            return 0

        # The fused image on the right:
        self.image_plot[2].setImage(align, disp=False)
        self.image_plot[2].overlayImage(image_plot[0].image)
        self.image_plot[2].roi.setSize(pg.Point(c_size[0], c_size[1]))


    def clearPoints(self):
        self.image_plot[0].points = np.zeros((5,2))
        self.image_plot[0].setPoints()
        self.image_plot[1].points = np.zeros((5,2))
        self.image_plot[1].setPoints()
        
    def lockROI(self, e):
        self.image_plot[2].roi.translatable = ( e != True )

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
app = QApplication([])
win = Window()

image_plot = win.image_plot

image_plot[0].setImage(paths.REFERENCE_PATH)
image_plot[1].setImage(paths.RAW_PATH)

if paths.PTS_CSV_READ is not None:
    [pts, c_pos, c_size] = read_csv(paths.PTS_CSV_READ)
    for i in [0, 1]:
        image_plot[i].points = pts[i, :, :]
        image_plot[i].setPoints()

# You can access points by accessing image_plot1.points
win.show()

if (sys.flags.interactive != 1) or not hasattr(Qt.QtCore, "PYQT_VERSION"):
    QApplication.instance().exec_()

