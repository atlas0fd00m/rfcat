#!/usr/bin/env python3
#
# Copyright 2012 atlas
#
# This file was adapted from a part of Project Ubertooth written by Jared Boone
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

from __future__ import print_function
from __future__ import division

from future import standard_library
standard_library.install_aliases()
from builtins import bytes
from builtins import range
from past.utils import old_div
import sys
import time
import numpy
import threading
import rflib
from rflib.bits import ord23
from .bits import correctbytes
# import cPickle in Python 2 instead of pickle in Python 3
if sys.version_info < (3,):
    import cPickle as pickle
else:
    import pickle as pickle

from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt, QPointF, QLineF

def ensureQapp():
    global _qt_app
    if not globals().get("_qt_app"):
        _qt_app = QtWidgets.QApplication([])


APP_SPECAN   = 0x43
SPECAN_QUEUE = 1

class SpecanThread(threading.Thread):
    def __init__(self, data, low_frequency, high_frequency, freq_step, delay, new_frame_callback):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self._data = data

        self._delay = delay
        self._low_frequency = low_frequency
        self._high_frequency = high_frequency
        self._freq_step = freq_step
        self._new_frame_callback = new_frame_callback
        self._stopping = False
        self._stopped = False

    def run(self):
        # this is where we pull in the data from the device
        #frame_source = self._device.specan(self._low_frequency, self._high_frequency)

        num_chans = int(old_div((self._high_frequency - self._low_frequency), self._freq_step))
        
        if type(self._data) == list:
            for rssi_values, timestamp in self._data:
                rssi_values = [ (old_div((ord23(x)^0x80),2))-88 for x in rssi_values[4:] ]
                # since we are not accessing the dongle, we need some sort of delay
                time.sleep(self._delay)
                frequency_axis = numpy.linspace(self._low_frequency, self._high_frequency, num=len(rssi_values), endpoint=True)

                self._new_frame_callback(numpy.copy(frequency_axis), numpy.copy(rssi_values))
                if self._stopping:
                    break
        else:
            while not self._stopping:
                try:
                    rssi_values, timestamp = self._data.recv(APP_SPECAN, SPECAN_QUEUE, 10000)
                    rssi_values = [ (old_div((ord23(x)^0x80),2))-88 for x in rssi_values ]
                    frequency_axis = numpy.linspace(self._low_frequency, self._high_frequency, num=len(rssi_values), endpoint=True)

                    self._new_frame_callback(numpy.copy(frequency_axis), numpy.copy(rssi_values))
                except:
                    sys.excepthook(*sys.exc_info())
            self._data._stopSpecAn()
            
    def stop(self):
        self._stopping = True
        self.join(3.0)
        self._stopped = True

class RenderArea(QtWidgets.QWidget):
    def __init__(self, data, low_freq=2.400e9, high_freq=2.483e9, freq_step=1e6, delay=0, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        
        self._graph = None
        self._reticle = None
        
        self._data = data
        self._delay = delay
        self._frame = None
        self._persisted_frames = None
        self._persisted_frames_depth = 350
        self._path_max = None
        
        self._low_frequency = low_freq #2.400e9
        self._high_frequency = high_freq #2.483e9
        self._frequency_step = freq_step #1e6
        self._high_dbm = 0.0
        self._low_dbm = -100.0

        self._hide_markers = False
        self._mouse_x = None
        self._mouse_y = None
        self._mouse_x2 = None
        self._mouse_y2 = None
        
        self._thread = SpecanThread(self._data,
                                    self._low_frequency,
                                    self._high_frequency,
                                    self._frequency_step,
                                    self._delay,
                                    self._new_frame)
        self._thread.start()
        
    def stop_thread(self):
        self._thread.stop()
    
    def _new_graph(self):
        self._graph = QtGui.QPixmap(self.width(), self.height())
        self._graph.fill(Qt.black)
    
    def _new_reticle(self):
        self._reticle = QtGui.QPixmap(self.width(), self.height())
        self._reticle.fill(Qt.transparent)
        
    def _new_persisted_frames(self, frequency_bins):
        self._persisted_frames = numpy.empty((self._persisted_frames_depth, frequency_bins))
        self._persisted_frames.fill(-128 + -54)
        self._persisted_frames_next_index = 0
    
    def minimumSizeHint(self):
        x_points = round(old_div((self._high_frequency - self._low_frequency), self._frequency_step))
        y_points = round(self._high_dbm - self._low_dbm)
        return QtCore.QSize(x_points * 4, y_points * 1)
    
    def _new_frame(self, frequency_axis, rssi_values):
        #print repr(frequency_axis)
        #print repr(rssi_values)
        self._frame = (frequency_axis, rssi_values)
        if self._persisted_frames is None:
            self._new_persisted_frames(len(frequency_axis))
        self._persisted_frames[self._persisted_frames_next_index] = rssi_values
        self._persisted_frames_next_index = (self._persisted_frames_next_index + 1) % self._persisted_frames.shape[0]
        self.update()
    
    def _draw_graph(self):
        if self._graph is None:
            self._new_graph()
        elif self._graph.size() != self.size():
            self._new_graph()
        
        painter = QtGui.QPainter(self._graph)

        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.fillRect(0, 0, self._graph.width(), self._graph.height(), QtGui.QColor(0, 0, 0, 10))
            
            if self._frame:
                frequency_axis, rssi_values = self._frame
                
                path_now = QtGui.QPainterPath()
                path_max = QtGui.QPainterPath()
                
                bins = list(range(len(frequency_axis)))
                x_axis = self._hz_to_x(frequency_axis)
                y_now = self._dbm_to_y(rssi_values)
                y_max = self._dbm_to_y(numpy.amax(self._persisted_frames, axis=0))
                
                # TODO: Wrapped Numpy types with float() to support old (<1.0) PySide API in Ubuntu 10.10
                path_now.moveTo(float(x_axis[0]), float(y_now[0]))
                for i in bins:
                    path_now.lineTo(float(x_axis[i]), float(y_now[i]))
                
                # TODO: Wrapped Numpy types with float() to support old (<1.0) PySide API in Ubuntu 10.10
                path_max.moveTo(float(x_axis[0]), float(y_max[0]))
                db_tmp = self._low_dbm
                max_max = None
                for i in bins:
                    path_max.lineTo(float(x_axis[i]), float(y_max[i]))
                    if self._y_to_dbm(y_max[i]) > db_tmp:
                        db_tmp = self._y_to_dbm(y_max[i])
                        max_max = i
                
                pen = QtGui.QPen()
                pen.setBrush(Qt.white)
                painter.setPen(pen)
                painter.drawPath(path_now)
                self._path_max = path_max
                if not max_max == None and not self._hide_markers:
                    pen.setBrush(Qt.red)
                    pen.setStyle(Qt.DotLine)
                    painter.setPen(pen)
                    painter.drawText(QPointF(x_axis[max_max] + 4, 30), '%.06f' % (old_div(self._x_to_hz(x_axis[max_max]), 1e6)))
                    painter.drawText(QPointF(30, y_max[max_max] - 4), '%d' % (self._y_to_dbm(y_max[max_max])))
                    painter.drawLine(QPointF(x_axis[max_max], 0), QPointF(x_axis[max_max], self.height()))
                    painter.drawLine(QPointF(0, y_max[max_max]), QPointF(self.width(), y_max[max_max]))
                    if self._mouse_x:
                        painter.drawText(QPointF(self._hz_to_x(self._mouse_x) + 4, 58), '(%.06f)' % ((old_div(self._x_to_hz(x_axis[max_max]), 1e6)) - (old_div(self._mouse_x, 1e6))))
                        pen.setBrush(Qt.yellow)
                        painter.setPen(pen)
                        painter.drawText(QPointF(self._hz_to_x(self._mouse_x) + 4, 44), '%.06f' % (old_div(self._mouse_x, 1e6)))
                        painter.drawText(QPointF(54, self._dbm_to_y(self._mouse_y) - 4), '%d' % (self._mouse_y))
                        painter.drawLine(QPointF(self._hz_to_x(self._mouse_x), 0), QPointF(self._hz_to_x(self._mouse_x), self.height()))
                        painter.drawLine(QPointF(0, self._dbm_to_y(self._mouse_y)), QPointF(self.width(), self._dbm_to_y(self._mouse_y)))
                        if self._mouse_x2:
                            painter.drawText(QPointF(self._hz_to_x(self._mouse_x2) + 4, 118), '(%.06f)' % ((old_div(self._mouse_x, 1e6)) - (old_div(self._mouse_x2, 1e6))))
                    if self._mouse_x2:
                        pen.setBrush(Qt.red)
                        painter.setPen(pen)
                        painter.drawText(QPointF(self._hz_to_x(self._mouse_x2) + 4, 102), '(%.06f)' % ((old_div(self._x_to_hz(x_axis[max_max]), 1e6)) - (old_div(self._mouse_x2, 1e6))))
                        pen.setBrush(Qt.magenta)
                        painter.setPen(pen)
                        painter.drawText(QPointF(self._hz_to_x(self._mouse_x2) + 4, 88), '%.06f' % (old_div(self._mouse_x2, 1e6)))
                        painter.drawText(QPointF(78, self._dbm_to_y(self._mouse_y2) - 4), '%d' % (self._mouse_y2))
                        painter.drawLine(QPointF(self._hz_to_x(self._mouse_x2), 0), QPointF(self._hz_to_x(self._mouse_x2), self.height()))
                        painter.drawLine(QPointF(0, self._dbm_to_y(self._mouse_y2)), QPointF(self.width(), self._dbm_to_y(self._mouse_y2)))
                        if self._mouse_x:
                            painter.drawText(QPointF(self._hz_to_x(self._mouse_x) + 4, 74), '(%.06f)' % ((old_div(self._mouse_x2, 1e6)) - (old_div(self._mouse_x, 1e6))))
        finally:
            painter.end()
            
    def _draw_reticle(self):
        if self._reticle is None or (self._reticle.size() != self.size()):
            self._new_reticle()
            
            dbm_lines = [QLineF(self._hz_to_x(self._low_frequency), self._dbm_to_y(dbm),
                                self._hz_to_x(self._high_frequency), self._dbm_to_y(dbm))
                         for dbm in numpy.arange(self._low_dbm, self._high_dbm, 20.0)]
            dbm_labels = [(dbm, QPointF(self._hz_to_x(self._low_frequency) + 2, self._dbm_to_y(dbm) - 2))
                          for dbm in numpy.arange(self._low_dbm, self._high_dbm, 20.0)]
            
            frequency_lines = [QLineF(self._hz_to_x(frequency), self._dbm_to_y(self._high_dbm),
                                      self._hz_to_x(frequency), self._dbm_to_y(self._low_dbm))
                               for frequency in numpy.arange(self._low_frequency, self._high_frequency, self._frequency_step * 20.0)]
            frequency_labels = [(frequency, QPointF(self._hz_to_x(frequency) + 2, self._dbm_to_y(self._high_dbm) + 10))
                                for frequency in numpy.arange(self._low_frequency, self._high_frequency, self._frequency_step * 10.0)]
            
            painter = QtGui.QPainter(self._reticle)
            try:
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                
                painter.setPen(Qt.blue)
                
                # TODO: Removed to support old (<1.0) PySide API in Ubuntu 10.10
                #painter.drawLines(dbm_lines)
                for dbm_line in dbm_lines: painter.drawLine(dbm_line)
                # TODO: Removed to support old (<1.0) PySide API in Ubuntu 10.10
                #painter.drawLines(frequency_lines)
                for frequency_line in frequency_lines: painter.drawLine(frequency_line)
                
                painter.setPen(Qt.white)
                for dbm, point in dbm_labels:
                    painter.drawText(point, '%+.0f' % dbm)
                for frequency, point in frequency_labels:
                    painter.drawText(point, '%.02f' % (old_div(frequency, 1e6)))
                    
            finally:
                painter.end()
    
    def paintEvent(self, event):
        self._draw_graph()
        self._draw_reticle()
        
        painter = QtGui.QPainter(self)
        try:
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(QtGui.QPen())
            painter.setBrush(QtGui.QBrush())

            if self._graph:
                painter.drawPixmap(0, 0, self._graph)
            
            if self._path_max:
                painter.setPen(Qt.green)
                painter.drawPath(self._path_max)

            painter.setOpacity(0.5)
            if self._reticle:
                painter.drawPixmap(0, 0, self._reticle)
        finally:
            painter.end()

    def _hz_to_x(self, frequency_hz):
        delta = frequency_hz - self._low_frequency
        range = self._high_frequency - self._low_frequency
        normalized = old_div(delta, range)
        #print "freq: %s \nlow: %s \nhigh: %s \ndelta: %s \nrange: %s \nnormalized: %s" % (frequency_hz, self._low_frequency, self._high_frequency, delta, range, normalized)
        return normalized * self.width()

    def _x_to_hz(self, x):
        range = self._high_frequency - self._low_frequency
        tmp = old_div(x, self.width())
        delta = tmp * range
        return delta + self._low_frequency
                             
    def _dbm_to_y(self, dbm):
        delta = self._high_dbm - dbm
        range = self._high_dbm - self._low_dbm
        normalized = old_div(delta, range)
        return normalized * self.height()

    def _y_to_dbm(self, y):
        range = self._high_dbm - self._low_dbm
        tmp = old_div(y, self.height())
        delta = tmp * range
        return self._high_dbm - delta

class Window(QtWidgets.QWidget):
    def __init__(self, data, low_freq, high_freq, spacing, delay=.01, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self._low_freq = low_freq
        self._high_freq = high_freq
        self._spacing = spacing
        self._delay= delay

        self._data = self._open_data(data)
        
        self.render_area = RenderArea(self._data, low_freq, high_freq, spacing, delay)

        main_layout = QtWidgets.QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.render_area, 0, 0)
        self.setLayout(main_layout)
        
        self.setWindowTitle("RfCat Spectrum Analyzer (thanks Ubertooth!)")

    def sizeHint(self):
        return QtCore.QSize(480, 160)
    
    def _open_data(self, data):
        if type(data) == str:
            if data == '-':
                data = rflib.RfCat()
                data._debug = 1
                freq = int(self._low_freq)
                spc = int(self._spacing)
                numChans = int(old_div((self._high_freq-self._low_freq), self._spacing))
                data._doSpecAn(freq, spc, numChans)
            else:
                data = pickle.load(open(data,'rb'))
        if data is None:
            raise Exception('Data not found')
        return data
    
    def closeEvent(self, event):
        self.render_area.stop_thread()
        event.accept()

    # handle mouse button clicks
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.render_area._mouse_x = self.render_area._x_to_hz(float(event.x()))
            self.render_area._mouse_y = self.render_area._y_to_dbm(float(event.y()))
            self.render_area._hide_markers = False
        if event.button() == Qt.RightButton:
            self.render_area._mouse_x2 = self.render_area._x_to_hz(float(event.x()))
            self.render_area._mouse_y2 = self.render_area._y_to_dbm(float(event.y()))
            self.render_area._hide_markers = False
        if event.button() == Qt.MidButton:
            self.render_area._mouse_x = None
            self.render_area._mouse_y = None
            self.render_area._mouse_x2 = None
            self.render_area._mouse_y2 = None
            self.render_area._hide_markers = not self.render_area._hide_markers
        event.accept()
        return

    # handle key presses
    def keyPressEvent(self, event):
        # test for non-alphanumeric keys first
        # arrow key
        if event.key() >= Qt.Key_Left and event.key() <= Qt.Key_Down:
            # left
            if event.key() == Qt.Key_Left:
                    self._low_freq -= self._spacing
                    self._high_freq -= self._spacing
            # up
            if event.key() == Qt.Key_Up:
                    self._spacing = int(self._spacing * 1.1)
            # right
            if event.key() == Qt.Key_Right:
                    self._low_freq += self._spacing
                    self._high_freq += self._spacing
            # down
            if event.key() == Qt.Key_Down:
                    self._spacing = int(self._spacing / 1.1)
            # this will redraw window with the correct labels etc., but we also need to re-start
            # specan on the dongle, and I'm not sure how best to do that!
            self.layout().removeWidget(self.render_area)
            self.render_area = RenderArea(self._data, self._low_freq, self._high_freq, self._spacing, self._delay)
            self.layout().addWidget(self.render_area, 0, 0)
            event.accept()
            return

        # anything else is alphanumeric
        try:
            key= correctbytes(event.key()).upper()
            event.accept()
        except:
            print('Unknown key pressed: 0x%x' % event.key())
            event.ignore()
            return
        if key == 'H':
            print('Key              Action') 
            print()
            print(' <LEFT ARROW>        Reduce base frequency by one step')
            print(' <RIGHT ARROW>       Increase base frequency by one step')
            print(' <DOWN ARROW>        Reduce frequency step 10%')
            print(' <UP ARROW>          Increase frequency step 10%')
            print(' <LEFT MOUSE>        Mark LEFT frequency / signal strength at pointer')
            print(' <RIGHT MOUSE>       Mark RIGHT frequency / signal strength at pointer')
            print(' <MIDDLE MOUSE>      Toggle visibility of frequency / signal strength markers')
            print(' H                   Print this HELP text')
            print(' M                   Simulate MIDDLE MOUSE click (for those with trackpads)')
            print(' Q                   Quit')
            return
        if key == 'M':
            self.render_area._mouse_x = None
            self.render_area._mouse_y = None
            self.render_area._mouse_x2 = None
            self.render_area._mouse_y2 = None
            self.render_area._hide_markers = not self.render_area._hide_markers
            return
        if key == 'Q':
            print('Quit!')
            self.close()
            return
        print('Unsupported key pressed:', key)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    f = sys.argv[1]
    fbase = eval(sys.argv[2])
    fhigh = eval(sys.argv[3])
    fdelta = eval(sys.argv[4])
    if len(sys.argv) > 5:
        delay = eval(sys.argv[5])
    else:
        delay = .01

    window = Window(f, fbase, fhigh, fdelta, delay)
    #window = Window('../data.again', 902.0, 928.0, 3e-1)
    window.show()
    sys.exit(app.exec_())
