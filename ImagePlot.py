import sys
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
import pyqtgraph as pg
from skimage import io, transform, color
import numpy as np
from dataclasses import dataclass
import logging

pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')

class ImagePlot(pg.GraphicsLayoutWidget):
    sigKeyPress = pyqtSignal(object)
    color_dict = { 'r':(255,0,0), 'g':(0,255,0), 'b':(0,0,255),
                   'p':(255,0,255), 'y':(255,255,0) }

    def __init__(self, use_roi=False, select_pts=True):
        self.pti = 0
        self.image = np.array([])

        super(ImagePlot, self).__init__()

        self.p1 = pg.PlotItem() 
        self.addItem(self.p1)
        self.p1.vb.invertY(True) # Images need inverted Y axis
        self.p1.showAxes(False)

        # Use ScatterPlotItem to draw points
        self.scatterItem = pg.ScatterPlotItem(
            size=10, 
            pen=pg.mkPen(None), 
            brush=pg.mkBrush(255, 0, 0),
            hoverable=True,
            hoverBrush=pg.mkBrush(0, 255, 255)
        )
        self.scatterItem.setZValue(2) # Ensure scatterPlotItem is always at top
        self.points = np.zeros((5,2))

        self.p1.addItem(self.scatterItem)

        self.use_roi = use_roi
        self.select_pts = select_pts
        if self.use_roi:
            self.roi = pg.RectROI(pos=(0,0), size=(100,100), aspectLocked=True)
            self.roi.setPen((255,0,0))
            self.roi.setZValue(20)
            self.p1.addItem(self.roi)

    def setImage(self, image, size=None, disp=True):
        # pg.ImageItem.__init__ method takes input as an image array
        if image is None:
            return

        if isinstance(image, str):
            img = io.imread(image)
            if len(img.shape) > 2:
                try:
                    img = color.rgb2gray(img)
                except ValueError:
                    img = img[:,:,0]

            if img.dtype != np.uint8:
                img = np.uint8(255/np.max(img) * img)
            image = img

        if size is not None:
            image = transform.resize(image, size)

        self.image = image

        if disp:
            self.p1.clear()
            self.p1.addItem(self.scatterItem)
            if self.use_roi:
                self.p1.addItem(self.roi)
            self.image_item = pg.ImageItem(image)
            self.image_item.setOpts(axisOrder='row-major')
            self.p1.getViewBox().setAspectLocked(True, ratio=(image.shape[1]/image.shape[0]))
            self.p1.addItem(self.image_item)

    def overlayImage(self, image):
        # TODO: Add other color/opacity support
        self.p1.clear()
        self.p1.addItem(self.scatterItem)
        if self.use_roi:
            self.p1.addItem(self.roi)

        fuse = np.zeros((self.image.shape[0], self.image.shape[1], 3))
        fuse[:,:,:] = np.dstack((self.image,self.image,self.image))
        fuse[image == 0, 0] = 255
        fuse[image == 0, 1] = 0
        fuse[image == 0, 2] = 0

        self.image_item = pg.ImageItem(fuse)
        self.image_item.setOpts(axisOrder='row-major')
        self.p1.getViewBox().setAspectLocked(True, ratio=(fuse.shape[1]/fuse.shape[0]))
        self.p1.addItem(self.image_item)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            self.points[self.pti, :] = [0, 0]
            self.setPoints()
        if event.key() == Qt.Key_H:
            self.p1.autoRange()
        self.sigKeyPress.emit(event)

    def mouseDoubleClickEvent(self, event):
        if not self.select_pts:
            return
        point = self.p1.vb.mapSceneToView(event.pos()) # get the point clicked
        # Get pixel position of the mouse click
        x, y = int(point.x()), int(point.y())
        self.points[self.pti, :] = [x, y]
        self.setPoints()
        super().mouseDoubleClickEvent(event)

    def setPoints(self):
        spots = []
        ind = 0
        for point in self.points:
            if point.all() != 0:
                spot = {'pos':point, 'brush':self.color_dict[['r','g','b','p','y'][ind]], \
                        'symbol':'+'}
                spots.append(spot)
            ind += 1
        self.scatterItem.setData(spots=spots)

    def getCrop(self):
        pos = np.array([self.roi.pos().x(), self.roi.pos().y()])
        dimensions = np.array([self.roi.size().x(), self.roi.size().y()])
        return [pos, dimensions]

    # TODO:
    # Figure out a better way to do all of this cropping, obviously this is pretty suboptimal
    # NOTE:
    # You definitely could use something other than qt as your export plugin, 
    # I found that the default was some 14x slower
    def saveImage(self, fname, c_pos=None, c_size=None):
        if c_pos is None or c_size is None:
            io.imsave(fname, self.image, plugin='qt')
            return

        if fname is None:
            logging.error('Image name not defined, cannot save')
            return 0
        if any(c_pos < 0):
            logging.info(f'Oversized crop (and negative roi), adding black border to {fname}')
            x = -int(c_pos[0]) if c_pos[0] < 0 else 0
            y = -int(c_pos[1]) if c_pos[1] < 0 else 0
            matt = np.zeros((int(c_size[1]), int(c_size[0])), dtype=np.uint8)
            off_x = int(c_pos[0]) if c_pos[0] > 0 else 0
            off_y = int(c_pos[1]) if c_pos[1] > 0 else 0

            matt[y:, x:] = self.image[off_y:int(c_size[1]) - y + off_y,off_x:int(c_size[0]) - x + off_x]
            # see note
            io.imsave(fname, matt, plugin='qt')
        else:
            if int(c_pos[1] + c_size[0]) > self.image.shape[0] or int(c_pos[0] + c_size[1]) > self.image.shape[1]:
                logging.info(f'Oversized crop, adding black border to {fname}')
                matt = np.zeros((int(c_pos[1] + c_size[0]), int(c_pos[0] + c_size[1])), dtype=np.uint8)
                matt[:self.image.shape[0], :self.image.shape[1]] = self.image[:matt.shape[0], :matt.shape[1]]
                # see note
                io.imsave(fname, \
                        matt[int(c_pos[1]):int(c_pos[1]+c_size[0]), \
                        int(c_pos[0]):int(c_pos[0]+c_size[1])], plugin='qt')
            else:
                io.imsave(fname, \
                        self.image[int(c_pos[1]):int(c_pos[1]+c_size[0]), \
                        int(c_pos[0]):int(c_pos[0]+c_size[1])], plugin='qt')
            

if __name__ == "__main__":

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication([])
    win = QMainWindow()

    central_win = QWidget()
    layout = QHBoxLayout()
    central_win.setLayout(layout)
    win.setCentralWidget(central_win)

    image_plot1 = ImagePlot()
    image_plot2 = ImagePlot()
    layout.addWidget(image_plot1)
    layout.addWidget(image_plot2)

    image_plot1.setImage('roitest.png', )
    image_plot2.setImage('roitest.png')
    # You can access points by accessing image_plot1.points
    win.show()

    if (sys.flags.interactive != 1) or not hasattr(Qt.QtCore, "PYQT_VERSION"):
        QApplication.instance().exec_()
