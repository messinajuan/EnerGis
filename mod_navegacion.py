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

import os
#from PyQt6.QtWidgets import QMessageBox

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

def __init__(self):
    pass

def buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo_buscado):
    #--------------------------------------------------------------------------------------
    #esta función devuelve una lista de lineas que tocan a un nodo (hasta 32), la cantidad
    #y la lista de nodos a los que se dirigen esas lineas, y ordenados como las mismas
    #--------------------------------------------------------------------------------------
    cant_lineas_del_nodo = 0
    lineas_del_nodo=[]
    proximos_nodos=[]
    try:
        cant_lineas_del_nodo = mnodos[nodo_buscado][4]
        for m in range (0, cant_lineas_del_nodo):
            linea = mnodos[nodo_buscado][m + 5]
            lineas_del_nodo.append(linea)
            if nodo_buscado == mlineas[linea][3]:
                proximos_nodos.append(mlineas[linea][2])
            elif nodo_buscado == mlineas[linea][2]:
                proximos_nodos.append(mlineas[linea][3])
            else:
                return cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos
        return cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos
    except:
        return cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos

def buscar_loops(self, mnodos, mlineas):
    #reduccion de matrices de nodos y lineas
    cant_spurs = 1
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            mnodos[n][45] = 1
            if mnodos[n][4]==0:
                mnodos[n][45] = 0
            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3): # and mnodos[n][2]!=1:
                cant_spurs = cant_spurs + 1
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    id = lineas_del_nodo[i]
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]
                    mlineas[id][1] = 0
                    mlineas[id][2] = 0
                    mlineas[id][3] = 0
                    mlineas[id][4] = 0
                    mlineas[id][5] = 0
                    mlineas[id][6] = 0
                    mlineas[id][12] = 0
                    mnodos[pf][4] = mnodos[pf][4] - 1
                    for v in range (1, 32):
                        if mnodos[pf][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pf][4 + m] = mnodos[pf][4 + m + 1]
                            mnodos[pf][4 + 32] = 0
                            break #v = 32
                    mnodos[pt][4] = mnodos[pt][4] - 1
                    for v in range (1, 32):
                        if mnodos[pt][4 + v] == id:
                            for m in range (v, 31):
                                mnodos[pt][4 + m] = mnodos[pt][4 + m + 1]
                            mnodos[pt][4 + 32] = 0
                            break #v = 32
                mnodos[n][1] = 0
                mnodos[n][45] = 0
    for n in range (0, len(mlineas)):
        if mlineas[n][1]!=0:
            mlineas[n][12] = 1
