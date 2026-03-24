# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2018 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

import os
from .mod_coordenadas import convertir_coordenadas
def __init__(self):
    pass

def exportar_txt(self, mapCanvas, conn, srid, nombre_modelo):
    #try:
    if os.path.isdir('c:/gis/energis6/Txt/')==False:
        os.mkdir('c:/gis/energis6/Txt/')

    if nombre_modelo == None or nombre_modelo == '':
        nombre_modelo = 'Ene=rGis5'

    str_archivo = 'c:/gis/energis6/Txt/' + nombre_modelo + '.txt'
    f = open(str_archivo,'w')
    f.writelines('Nodos' + '\n')
    cursor = conn.cursor()
    cursor.execute("SELECT geoname, ISNULL(nombre, ''), ISNULL(nodos.descripcion, ''), elementos_nodos.descripcion, xcoord, ycoord, tension, alimentador, zona FROM Nodos INNER JOIN Elementos_Nodos ON Nodos.elmt=Elementos_Nodos.id")
    #convierto el cursor en array
    nodos = tuple(cursor)
    cursor.close()
    for n in range (0, len(nodos)):
        coords = convertir_coordenadas(self, nodos[n][4], nodos[n][5], srid, 4326)
        str_longitud = str(coords[1])
        str_latitud = str(coords[0])
        f.writelines(str(nodos[n][0]) + ', ' + nodos[n][1].replace('\n',' ').replace(',',' ').strip() + ', ' + nodos[n][2].replace('\n',' ').replace(',',' ').strip() + ', ' + nodos[n][3].replace(',',' ') + ', ' + str(nodos[n][6]) + ', ' + nodos[n][7].replace(',',' ') + ', ' + nodos[n][8] + ', ' + str_longitud + ', ' + str_latitud + '\n')
    f.close()
    #---------------------------------------
    f = open(str_archivo,'a')
    f.writelines('\n')
    f.writelines('Lineas' + '\n')
    cursor = conn.cursor()
    cursor.execute("SELECT geoname, desde, hasta, fase, descripcion, tension, alimentador, obj.ToString() FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id")
    #convierto el cursor en array
    lineas = tuple(cursor)
    cursor.close()
    for l in range (0, len(lineas)):
        str_linea = ''
        str_polilinea = lineas[l][7].replace('LINESTRING (','').replace(')','')
        coordenadas = str_polilinea.split(', ')
        for coordenada in coordenadas:
            x, y = coordenada.split(' ')
            coords = convertir_coordenadas(self, x, y, srid, 4326)
            str_longitud = str(coords[1])
            str_latitud = str(coords[0])
            str_linea = str_linea + str_longitud + ' ' + str_latitud + ', '
        f.writelines(str(lineas[l][0]) + ', ' + str(lineas[l][1]) + ', ' + str(lineas[l][2]) + ', ' + lineas[l][3] + ', ' + lineas[l][4].replace(',',' ') + ', ' + str(lineas[l][5]) + ', ' + lineas[l][6].replace(',',' ') + ', (' + str_linea[:-2] + ')' + '\n')
    f.close()

    return 'Exportado en ' + str_archivo
    #except:
    #    return 'No se pudo exportar'
