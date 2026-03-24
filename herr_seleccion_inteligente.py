#-----------------------------------------------------------
#
# Plain Geometry Editor is a QGIS plugin to edit geometries
# using plain text editors (WKT, WKB)
#
# Copyright    : (C) 2013 Denis Rouzaud
# Email        : denis.rouzaud@gmail.com
#
#-----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this progsram; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------

#from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import pyqtSignal
from qgis.core import QgsVectorLayer, QgsFeature
from qgis.gui import QgsMapToolIdentify

class seleccionInteligente(QgsMapToolIdentify):

    geomIdentified = pyqtSignal(QgsVectorLayer, QgsFeature)

    def __init__(self, canvas):
        self.canvas = canvas
        QgsMapToolIdentify.__init__(self, canvas)
        #self.setCursor(QCursor())
        pass

    def canvasReleaseEvent(self, mouseEvent):
        try:
            capas_seleccionables=[]
            n = self.canvas.layerCount()
            layers = [self.canvas.layer(i) for i in range(n)]
            #hacemos que se busque en las capas que queremos !!!
            for lyr in layers:
                if lyr.name()[:6] == 'Lineas':
                    capas_seleccionables.append(lyr)
                if lyr.name()[:5] == 'Nodos':
                    capas_seleccionables.append(lyr)
                
            results = self.identify(mouseEvent.x(), mouseEvent.y(), self.LayerSelection, capas_seleccionables)
        except:
            #print ("PICKLAYER EXCEPTION: ",e)
            results = []
        if len(results) > 0:
            #print (results[0].mFeature.attributes())
            self.geomIdentified.emit(results[0].mLayer, QgsFeature(results[0].mFeature))
