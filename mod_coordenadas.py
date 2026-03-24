# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2026 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import pyproj

def __init__(self):
    pass

def convertir_coordenadas(self, x, y, epsg1, epsg2):
    x = round(float(x),6)
    y = round(float(y),6)
    try:
        # Define las coordenadas de origen en tu sistema de coordenadas actual
        coordenadas_origen = (x, y)
        # Crea un objeto de transformación de proyección
        transformador = pyproj.Transformer.from_crs('EPSG:' + str(epsg1), 'EPSG:' + str(epsg2), always_xy=True)
        # Realiza la conversión a WGS84 (EPSG:4326)
        coordenadas_wgs84 = transformador.transform(*coordenadas_origen)
        return [round(coordenadas_wgs84[1],6),round(coordenadas_wgs84[0],6)]
        #return list(reversed(coordenadas_wgs84))
    except:
        return 'Error'
