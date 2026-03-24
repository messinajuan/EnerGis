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
import json
import tempfile
from PyQt6.QtWidgets import QMessageBox

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

#Nodos                          Lineas
#39:aux2:elm                    7:aux2:
#40:aux3:alimentador            8:aux3:
#41:aux4:                       9:aux4:
#43:aux6:nodo_padre            10:aux5:nodo_padre
#44:aux7:                      11:aux6:
#45:aux8:marca_reducciones     12:aux7:marca_reducciones

#Navegar a los extremos:
#Logica:
#   Se buscan loops
#   Si el nodo a navegar está en un loop aviso
#   Se abren los loops quitando una linea
#   Se reduce la red por spurs
#   Si dentro de los nodos navegados están los de la lpinea quitada, se agrega esa linea

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

def navegar_compilar_red(self, mnodos, mlineas, monodos, fuente_navegada):
    #--------------------------------------------------------------------------------------
    #esta rutina navega la red desde una fuente y marca el camino que recorre .
    #--------------------------------------------------------------------------------------
    n = 0
    nodo = 0
    #****************************************
    nodo = fuente_navegada
    pendientes = []
    nodo_padre = nodo
    repetir = True
    accion = 'Navegar Fuente'
    #****************************************
    try:
        mnodos[fuente_navegada][3] = fuente_navegada
        while repetir == True:
            repetir = False
            if nodo == 0:
                #me fijo si me quedo algun seccionador abierto sin ordenar, se pone al final
                for n in range (0, len(mnodos)):
                    if mnodos[n][2] == 3: #es un seccionador abierto
                        if not n in monodos:
                            monodos.append(n)
                repetir = True
            else:
                if not nodo in monodos:
                    accion = 'Ordenando Nodos'
                    monodos.append(nodo)
                #****************************************
                mnodos[nodo][3] = fuente_navegada
                #****************************************
                accion = 'Buscar Lineas'
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo)
                #****************************************
                for n in range (0, cant_lineas_del_nodo):
                    if mnodos[proximos_nodos[n]][2] == 3:
                        #como el ultimo nodo de cada spur
                        mlineas[lineas_del_nodo[n]][4] = fuente_navegada
                        mnodos[proximos_nodos[n]][3] = fuente_navegada
                        if mnodos[proximos_nodos[n]][43] == 0:
                            mnodos[proximos_nodos[n]][43] = nodo
                        if mlineas[lineas_del_nodo[n]][10] == 0:
                            mlineas[lineas_del_nodo[n]][10] = nodo
                        #aca no dejo pendientes porque se trata de una seccionador abierto
            #****************************************
            if mnodos[nodo][2]==3:
                #como el ultimo nodo de cada spur
                #Aca esta suponiendo que el seccionador abierto tiene una sola línea que le llega, pero esta mal
                #hay que marcar la linea del lado que venia navegando.
                mlineas[mnodos[nodo][5]][4] = fuente_navegada
                if mlineas[mnodos[nodo][5]][10] == 0:
                    mlineas[mnodos[nodo][5]][10] = nodo_padre
                #si cambia la tension del pendiente blanqueo el ultimo trafo navegado
                    #eso falta
                #paso al nodo siguiente
                if len(pendientes) > 0:
                    nodo = pendientes[-1] #tomo el nodo del ultimo valor de la lista
                    pendientes.pop() #elimino el ultimo valor de la lista
                    nodo_padre = mnodos[nodo][43]
                    #repetir = True
            if repetir==False: #si repetir=True voy hasta el fondo para iterar
                accion = 'Buscar lineas del nodo'
                #****************************************
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, nodo)
                #****************************************
                camino = -1
                #escojo el primer camino aún no recorrido
                accion = 'Escoger Camino'
                for n in range (0, cant_lineas_del_nodo):
                    if mlineas[lineas_del_nodo[n]][4] == 0:
                        camino = n
                        n = cant_lineas_del_nodo + 1
                linea_navegando = lineas_del_nodo[camino]
                mlineas[linea_navegando][4] = fuente_navegada
                if mlineas[linea_navegando][10] == 0:
                    mlineas[linea_navegando][10] = nodo
                #****************************************
                #agrego los caminos pendientes que aún no estan pendientes
                accion = 'Agregar Pendientes'
                for n in range (0, cant_lineas_del_nodo):
                    if camino!=n:
                        if mlineas[lineas_del_nodo[n]][4] == 0:
                            pendientes.append(proximos_nodos[n])
                            if mnodos[proximos_nodos[n]][43] == 0:
                                mnodos[proximos_nodos[n]][43] = nodo
                            if mlineas[lineas_del_nodo[n]][10] == 0:
                                mlineas[lineas_del_nodo[n]][10] = nodo
                if camino!=-1:
                    #si cambia la tension del pendiente blanqueo el ultimo trafo navegado
                        #eso falta
                    #paso al nodo siguiente
                    nodo_padre = nodo
                    #****************************************
                    accion = 'Elegir Pemdiemte'
                    nodo = proximos_nodos[camino]
                    mnodos[nodo][3] = fuente_navegada
                else:
                    if mnodos[nodo][4]==1: #ultimo nodo (de cada spur)
                        accion = 'Spur'
                        mlineas[mnodos[nodo][5]][4] = fuente_navegada
                        if mlineas[mnodos[nodo][5]][10] == 0:
                            mlineas[mnodos[nodo][5]][10] = nodo_padre
                    #si cambia la tension del pendiente blanqueo el ultimo trafo navegado
                        #eso falta
                    #paso al nodo siguiente
                    if len(pendientes)==0:
                        return 'Red Navegada'
                    accion = 'Tomar Pendiemte'
                    nodo = pendientes[-1] #tomo el nodo del ultimo valor de la lista
                    pendientes.pop() #elimino el ultimo valor de la lista
                    nodo_padre = mnodos[nodo][43]
            repetir = True
            nodo_padre = nodo
        return 'Verificar Navegacion'
    except:
        return 'Navegacion - Verificar nodo - en ' + accion + ': ' + str(mnodos[nodo][1])

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

def navegar_a_la_fuente(self, mnodos, mlineas, geoname):
    fuentes = []
    lineas_de_fuentes = []
    for n in range (0, len(mlineas)):
        if mnodos[mlineas[n][2]][2]==1:
            lineas_de_fuentes.append(n)
            fuentes.append(mlineas[n][2])
        if mnodos[mlineas[n][3]][2]==1:
            lineas_de_fuentes.append(n)
            fuentes.append(mlineas[n][3])
    #reduccion de matrices de nodos y lineas
    cant_spurs = 1
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3) and mnodos[n][2]!=1 and mnodos[n][1]!=geoname:
                cant_spurs = cant_spurs + 1
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    try:
                        id = lineas_del_nodo[i]
                    except:
                        QMessageBox.information(None, "Mensaje", "Error 1 en Nodo : " + str(mnodos[n][1]) + " (" + str(n) +")")
                        return
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]
                    mlineas[id][1] = 0
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
    #reduccion de matrices de nodos y lineas para nodos con dos lineas
    nodos_asociados=[]
    lineas_asociadas=[]
    nodos_anulados=[]
    cant_dobles = 1
    while cant_dobles != 0:
        cant_dobles = 0
        for n in range (0, len(mnodos)):
            if mnodos[n][1]!=0 and mnodos[n][4]==2 and mnodos[n][1]!=geoname:
                b_existe=False
                for x in range(0, len(nodos_anulados)):
                    if mnodos[n][1]==nodos_anulados[x]:
                        b_existe=True
                if b_existe==False:
                    # de:
                    #      linea 1       linea 2
                    #  A ----------- N ------------ B
                    # pasa a:
                    #        linea 1 (N, Linea2)
                    #  A -------------------------- B
                    #este es el nodo
                    #QMessageBox.information(None, "Mensaje", "nodo a reducir: " + str(mnodos[n][1]))
                    cant_dobles = cant_dobles + 1
                    cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                    #identificamos el nodo B
                    linea2 = lineas_del_nodo[1]
                    #si hay nodos dobles en guirnalda, puede pasar que en una misma iteracion tenga dos seguidos
                    #pero si procesé uno y lo anulé no lo tomo en cuenta
                    if mnodos[proximos_nodos[0]][1]!=mnodos[proximos_nodos[1]][1]:
                        #QMessageBox.information(None, "Mensaje", "linea 2: " + str(mlineas[linea2][1]))
                        if mlineas[linea2][2]==mnodos[n][0]:
                            nodo_B=mlineas[linea2][3]
                        else:
                            nodo_B=mlineas[linea2][2]
                        #modificamos la linea 1
                        linea1 = lineas_del_nodo[0]
                        #QMessageBox.information(None, "Mensaje", "linea 1: " + str(mlineas[linea1][1]))
                        if mlineas[linea1][2]==mnodos[n][0]:
                            #asignamos nodo hasta a la linea 2
                            mlineas[linea1][2] = nodo_B
                        else:
                            #asignamos nodo hasta a la linea 2
                            mlineas[linea1][3] = nodo_B
                        #asignamos la linea 1 al nodo B
                        for v in range (1, 32):
                            if mnodos[nodo_B][4 + v] == linea2:
                                #QMessageBox.information(None, "Mensaje", "cambiamos en nodo : " + str(mnodos[nodo_B][1]) + " para que toque a linea 1 : " + str(mlineas[linea1][1]))
                                mnodos[nodo_B][4 + v] = linea1
                        #a la linea 1 le guardamos nodo y linea reducido
                        lineas_asociadas.append([linea1,mlineas[linea2][0],mlineas[linea2][1]])
                        nodos_asociados.append([linea1,mnodos[n][0],mnodos[n][1]])
                        #borramos la linea 2
                        mlineas[linea2][1] = 0
                        #borramos el nodo
                        mnodos[n][1] = 0
                    else:
                        #QMessageBox.information(None, "Mensaje", "No se procesa nodo " + str(mnodos[n][1]))
                        nodos_anulados.append(mnodos[n][1])
        #reducimos lineas paralelas (faltarian los triangulos)
        lineas=[]
        for n in range (0, len(mlineas)):
            if mlineas[n][1]!=0:
                # de:
                #      linea 1
                #  A ----------- B
                #      linea 2
                #  A ----------- B
                # pasa a:
                #    linea 1 (Linea2)
                #  A ---------------- B
                b_existe=False
                for m in range (0, len(lineas)):
                    if (lineas[m][2]==mlineas[n][2] and lineas[m][3]==mlineas[n][3]) or (lineas[m][2]==mlineas[n][3] and lineas[m][3]==mlineas[n][2]):
                        #esta es la linea
                        #QMessageBox.information(None, "Mensaje", "líneas paralelas: " + str(mlineas[n][1]) + " - " + str(lineas[m][1]))
                        b_existe=True
                        pos = lineas[m][0]
                        #a la linea le guardamos la linea reducida
                        lineas_asociadas.append([n,mlineas[pos][0],mlineas[pos][1]])
                        k=mlineas[pos][2]
                        for v in range (1, 32):
                            if mnodos[k][4 + v] == mlineas[pos][0]:
                                #borramos la linea de los nodos
                                mnodos[k][4] = mnodos[k][4] - 1
                                #QMessageBox.information(None, "Mensaje", "1 al nodo : " + str(mnodos[k][1]) + " le quedan " + str(mnodos[k][4]) + " conexiones")
                                for w in range (v, 31):
                                    mnodos[k][4 + w] = mnodos[k][4 + w + 1]
                                mnodos[k][4 + 32] = 0
                                break #v = 32
                        k=mlineas[pos][3]
                        for v in range (1, 32):
                            if mnodos[k][4 + v] == mlineas[pos][0]:
                                #borramos la linea de los nodos
                                mnodos[k][4] = mnodos[k][4] - 1
                                #QMessageBox.information(None, "Mensaje", "2 al nodo : " + str(mnodos[k][1]) + " le quedan " + str(mnodos[k][4]) + " conexiones")
                                for w in range (v, 31):
                                    mnodos[k][4 + w] = mnodos[k][4 + w + 1]
                                mnodos[k][4 + 32] = 0
                                break #v = 32
                        mlineas[pos][1] = 0
                if b_existe==False:
                    #agrego la linea para despues poder comparar
                    #QMessageBox.information(None, "Mensaje", "agrego línea no paralela: " + str(mlineas[n][1]))
                    lineas.append([mlineas[n][0],mlineas[n][1],mlineas[n][2],mlineas[n][3]])
    #reduccion de matrices de nodos y lineas
    cant_spurs = 1
    while cant_spurs != 0:
        cant_spurs = 0
        for n in range (0, len(mnodos)):
            if mnodos[n][1]!=0 and (mnodos[n][4]==1 or mnodos[n][2]==3) and mnodos[n][2]!=1 and mnodos[n][1]!=geoname:
                #QMessageBox.information(None, "Mensaje", "spur final : " + str(mnodos[n][1]))
                cant_spurs = cant_spurs + 1
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos, mlineas, n)
                for i in range (0, cant_lineas_del_nodo):
                    try:
                        id = lineas_del_nodo[i]
                    except:
                        QMessageBox.information(None, "Mensaje", "Error 2 en Nodo : " + str(mnodos[n][1]) + " (" + str(n) +")")
                        return
                    pf = mlineas[id][2]
                    pt = mlineas[id][3]
                    #Si la linea tenia asociados, los borramos para no marcarlos al final
                    for m in range (0, len(nodos_asociados)):
                        if nodos_asociados[m][0]==id:
                            nodos_asociados[m][0]=0
                    for m in range (0, len(lineas_asociadas)):
                        if lineas_asociadas[m][0]==id:
                            lineas_asociadas[m][0]=0
                    mlineas[id][1] = 0
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
    #marcamos
    for n in range (0, len(mnodos)):
        if mnodos[n][1]!=0:
            mnodos[n][45] = 1
        else:
            mnodos[n][45] = 0
    lineas_loop=[]
    for n in range (0, len(mlineas)):
        if mlineas[n][1]!=0:
            mlineas[n][12] = 1
            lineas_loop.append(mlineas[n][0])
    #QMessageBox.information(None, "Mensaje", "Lineas Loop : " + str(lineas_loop))
    b_agregue=True
    while b_agregue==True:
        b_agregue=False
        for n in range (0, len(lineas_asociadas)):
            #QMessageBox.information(None, "Mensaje", "Linea asociada : " + str(lineas_asociadas[n][0]))
            for m in range (0, len(lineas_loop)):
                if lineas_asociadas[n][0]==lineas_loop[m]:
                    b_existe=False
                    #buscamos en lineas loop si ya esta la linea asociada
                    for k in range (0, len(lineas_loop)):
                        if lineas_loop[k]==lineas_asociadas[n][1]:
                            b_existe=True
                    #si aun no está la agregamos
                    if b_existe==False:
                        #restituimos el geoname en mlineas
                        mlineas[lineas_asociadas[n][1]][1] = lineas_asociadas[n][2]
                        mlineas[lineas_asociadas[n][1]][12] = 1
                        lineas_loop.append(lineas_asociadas[n][1])
                        #QMessageBox.information(None, "Mensaje", "Linea Loop : " + str(lineas_asociadas[n][1]) + ' : ' + str(lineas_asociadas[n][2]))
                        #QMessageBox.information(None, "Mensaje", "Lineas Loop : " + str(lineas_loop))
                        b_agregue=True
    for n in range (0, len(fuentes)):
        mnodos[fuentes[n]][45]=0
    for n in range (0, len(mlineas)):
        if mlineas[n][12]==1:
            #marcamos los nodos
            for m in range (0, len(nodos_asociados)):
                if nodos_asociados[m][0]==n:
                    mnodos[nodos_asociados[m][1]][45]=1
                    mnodos[nodos_asociados[m][1]][1]=nodos_asociados[m][2]
                    #QMessageBox.information(None, "Mensaje", "Agrego nodo : " + str(nodos_asociados[m][2]))
            #marco las fuentes
            for m in range (0, len(lineas_de_fuentes)):
                if lineas_de_fuentes[m]==n:                    
                    if mnodos[mlineas[n][2]][2]==1:
                        mnodos[mlineas[n][2]][45]=1
                    if mnodos[mlineas[n][3]][2]==1:
                        mnodos[mlineas[n][3]][45]=1
                    #QMessageBox.information(None, "Mensaje", "Fuente de linea : " + str(mlineas[n][1]))
        else:
            mlineas[n][12] = 0

def nodos_por_salida(self, conn):
    #----------------
    #-----LOOPS------
    #----------------
    nodos_en_loops = []
    seccionadores_en_loops = []
    lineas_abiertas = []
    b_proceso=True
    pasada = 0
    mnodos = []
    mnodos2 = []
    mlineas = []
    mlineas2 = []
    while b_proceso==True:
        b_proceso=False
        pasada = pasada + 1
        #QMessageBox.information(None, "Mensaje", "pasada : " + str(pasada))
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            mnodos = tuple(listanodos)
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            mlineas = tuple(listalineas)
        #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
        #anulamos las lineas para eliminar loops
        for k in range (0, len(lineas_abiertas)):
            #QMessageBox.information(None, "Mensaje", "Linea abierta " + str(lineas_abiertas[k]))
            for n in range (0, len(mlineas)):
                if mlineas[n][1] == lineas_abiertas[k]:
                    #la saco de proximos nodos
                    for m in range(0, len(mnodos)):
                        for j in range(5, 37):
                            if mnodos[m][j] == mlineas[n][0]:
                                #resto uno a la cantidad de lineas
                                mnodos[m][4]=mnodos[m][4]-1
                                #corro las lineas asociadas
                                for l in range(j, 31):
                                    mnodos[m][l]=mnodos[m][l+1]
                                mnodos[m][32]=0
                    #anulo la linea
                    #QMessageBox.information(None, "Mensaje", "Anulo linea " + str(mlineas[n][1]))
                    mlineas[n][0]=0
                    #corto el for
                    break #n=len(mlineas)
        #--------------------------------------------
        buscar_loops(self, mnodos, mlineas)
        #--------------------------------------------
        for n in range(0, len(mnodos)):
            if mnodos[n][45] == 1:
                #si encontre loop tengo que seguir
                b_proceso=True
                #guardo los nodos en loops (aux)
                b_existe=False
                for m in range(0,len(nodos_en_loops)):
                    if nodos_en_loops[m]==mnodos[n][0]:
                        b_existe=True
                if b_existe==False:
                    nodos_en_loops.append(mnodos[n][0])
                #guardo los seccionadores en loops
                if mnodos[n][2] == 2:
                    b_existe=False
                    for m in range(0,len(seccionadores_en_loops)):
                        if seccionadores_en_loops[m]==mnodos[n][1]:
                            b_existe=True
                    if b_existe==False:
                        seccionadores_en_loops.append(mnodos[n][1])
        #tengo que elegir una linea del loop relacionada a un nodo del loop
        for l in range (0, len(mlineas)):
            if mlineas[l][12] == 1:
                #elijo la primer linea para abrir
                desde=False
                hasta=False
                #tiene que ser una linea relacionada a dos nodos del loop
                for k in range (0, len(nodos_en_loops)):
                    if nodos_en_loops[k]==mlineas[l][2]:
                        desde = True
                    if nodos_en_loops[k]==mlineas[l][3]:
                        hasta = True
                if desde==True and hasta==True:
                    b_existe=False
                    for m in range(0,len(lineas_abiertas)):
                        if lineas_abiertas[m]==mlineas[l][1]:
                            b_existe=True
                    if b_existe==False:
                        lineas_abiertas.append(mlineas[l][1])
                        #QMessageBox.information(None, "Mensaje", "Agrego linea " + str(mlineas[l][1]))
                    #corto el for
                    break
    #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
    #-----------------------------
    #-----REDUCCION DE SPURS------
    #-----------------------------
    #QMessageBox.information(None, "Mensaje", "reduccion")
    ruta = os.path.join(tempfile.gettempdir(), "jnodos")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jnodos = a.read()
        # Analizar el contenido JSON en un objeto Python
        listanodos = json.loads(jnodos)
        mnodos2 = tuple(listanodos)
    ruta = os.path.join(tempfile.gettempdir(), "jlineas")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jlineas = a.read()
        # Analizar el contenido JSON en un objeto Python
        listalineas = json.loads(jlineas)
        mlineas2 = tuple(listalineas)
    for k in range (0, len(lineas_abiertas)):
        for n in range (0, len(mlineas2)):
            if mlineas2[n][1] == lineas_abiertas[k]:
                #QMessageBox.information(None, "Mensaje", "Anulo linea: " + str(mlineas2[n][1]))
                #la saco de proximos nodos
                for m in range(0, len(mnodos2)):
                    for j in range(5, 37):
                        if mnodos2[m][j] == mlineas2[n][0]:
                            #resto uno a la cantidad de lineas
                            #QMessageBox.information(None, "Mensaje", "resto uno al nodo " + str(mnodos2[m][1]))
                            mnodos2[m][4]=mnodos2[m][4]-1
                            #QMessageBox.information(None, "Mensaje", "quedo en " + str(mnodos2[m][4]))
                            #corro las lineas asociadas
                            for l in range(j, 31):
                                mnodos2[m][l]=mnodos2[m][l+1]
                            mnodos2[m][32]=0
                            #corto el for
                            break
                #anulo la linea
                #QMessageBox.information(None, "Mensaje", "La anulo : " + str(mlineas2[n][1]))
                mlineas2[n][0]=0
                #corto el for
                break
    #vaciamos la tabla que guarda los nodos por alimentador (geoname, id)
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE Nodos_Alimentador")
        conn.commit()
    except:
        conn.rollback()
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    #armo un array vacio con una columna por nodo para alojar a los nodos asociados a cada uno
    for n in range (0, len(mnodos2)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos2[n][1])
    #Reduccion de Red por niveles de salidas de alimentador
    #Se utiliza el elemento y no el estado de los mismos
    #Se recorre el array de nodos, se le va asignando geoname=0 para anularlos
    #Con un máximo de 10 niveles se pretende encontrar los nodos por salida
    nivel = 1
    #Arranque
    seguir = 1
    #Se seguirá siempre y cuando queden salidas por recorrer
    while seguir == 1:
        #Arranque
        cant_spurs = 1
        #Se seguirá siempre y cuando existan spurs
        while cant_spurs != 0:
            #Blanqueo cantidad de spurs
            cant_spurs = 0
            #Se recorre el array de nodos tratando de agrupar para este nivel todos los nodos hacia la salida
            for n in range (0, len(mnodos2)):
                #si es aislado lo desmarco
                if mnodos2[n][4]==0:
                    mnodos2[n][45] = 0
                else:
                    #Marco el nodo que analizo en posicion 45
                    mnodos2[n][45] = 1
                #Si no esta borrado y (es spur o es SA) y no es fuente
                if mnodos2[n][1]!=0 and (mnodos2[n][4]==1 or mnodos2[n][39]==3) and mnodos2[n][2]!=1:
                    #Si no es salida de alimentador:
                    if mnodos2[n][2]!=8:
                        #sumo uno a la lista de spurs para continuar intentando reducir
                        cant_spurs = cant_spurs + 1
                        #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
                        na = nodos_asociados[n]
                        #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
                        na.append(mnodos2[n][1])
                        #Ahora el listado de asociados a este nodo es la lista total
                        nodos_asociados[n] = na
                        #Busco LA LINEA del nodo
                        cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos2, mlineas2, n)
                        for i in range (0, cant_lineas_del_nodo):
                            #Para cada una de las lineas del nodo, obtenemos desde y hasta
                            id = lineas_del_nodo[i]
                            pf = mlineas2[id][2]
                            pt = mlineas2[id][3]
                            #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                            #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                            #Si el nodo desde es n, el proximo setá el hasta
                            if pf==n:
                                #El nodo a asociar es el hasta
                                p = pt
                            elif pt==n:
                                #El nodo a asociar es el desde
                                p = pf
                            else: #Si no encuentro desde ni hasta hay un error
                                QMessageBox.information(None, "Mensaje", "Error 1 en línea : " + str(mlineas2[id][1]) + " (" + str(id) +")")
                            if mnodos2[p][0]!=0:
                                na = nodos_asociados[p]
                                for j in range (0, len(nodos_asociados[n])):
                                    na.append(nodos_asociados[n][j])
                                nodos_asociados[p] = na
                            #Borro existencia de la linea
                            mlineas2[id][1] = 0
                            mlineas2[id][2] = 0
                            mlineas2[id][3] = 0
                            mlineas2[id][4] = 0
                            mlineas2[id][5] = 0
                            mlineas2[id][6] = 0
                            mlineas2[id][12] = 0
                            #Al proximo nodo le quito a n como proximo nodo
                            mnodos2[p][4] = mnodos2[p][4] - 1
                            for v in range (1, 32):
                                if mnodos2[p][4 + v] == id:
                                    for m in range (v, 31):
                                        mnodos2[p][4 + m] = mnodos2[p][4 + m + 1]
                                    mnodos2[p][4 + 32] = 0
                                    break #v = 32
                        #Anulo el nodo que ya navegué
                        mnodos2[n][1] = 0
                        mnodos2[n][45] = 0
                    else: #Si el spur es una salida de alimentador:
                        #Si posee nodos asociados los paso a la base
                        if len(nodos_asociados[n])>0:
                            cursor = conn.cursor()
                            try: #geoname (nodo). id (geoname alimentador)
                                cursor.execute("INSERT INTO Nodos_Alimentador SELECT geoname, " + str(nodos_geoname[n]) + " FROM Nodos WHERE Nodos.Tension>0 AND geoname IN (" + str(nodos_geoname[n]) + "," + str(nodos_asociados[n]).replace('[','').replace(']','') + ")")
                                conn.commit()
                            except:
                                conn.rollback()
                            #Ya grabados los nodos asociados a la salida, desasociamos los nodos para que no pasen aguas arriba
                            nodos_asociados[n] = []
                            #nodos_asociados[n].append(0)
                            #Convierto a la salida en un nodo comun para poder seguir aguas arriba
                            mnodos2[n][2] = 0
        #si tengo todavia salidas para navegar, sumo un nivel
        existe=0
        for n in range (0, len(mnodos2)):
            if mnodos2[n][1]!=0 and mnodos2[n][2]==8:
                existe=1
                #QMessageBox.information(None, "Mensaje", "Salida : " + str(mnodos[n][1]))
                break #n = len(mnodos2)
        if existe==1:
            nivel = nivel + 1
            #QMessageBox.information(None, "Mensaje", "Nivel : " + str(nivel))
            seguir = 1
            if nivel > 10:
                seguir = 0
        else:
            seguir = 0
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE A SET d=o FROM (SELECT Nodos.Alimentador AS d, Nodos_1.Val1 AS o FROM Nodos_Alimentador INNER JOIN Nodos ON Nodos_Alimentador.Geoname = Nodos.Geoname INNER JOIN Nodos AS Nodos_1 ON Nodos_Alimentador.Id = Nodos_1.Geoname AND Nodos.Alimentador <> Nodos_1.Val1 WHERE (Nodos.Elmt <> 8)) A")
        cursor.execute("UPDATE A SET d=o FROM (SELECT Lineas.Alimentador AS d, Nodos.Alimentador AS o FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde AND Nodos.Alimentador <> Lineas.Alimentador INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname AND Nodos.Alimentador = Nodos_1.Alimentador) A")
        cursor.execute("UPDATE A SET d=o FROM (SELECT Lineas.Alimentador AS d, Nodos.Alimentador AS o FROM Nodos INNER JOIN Lineas ON Nodos.Geoname = Lineas.Desde AND Nodos.Alimentador <> Lineas.Alimentador INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname WHERE (Nodos_1.Estado = 3)) A")
        cursor.execute("UPDATE A SET d=o FROM (SELECT Lineas.Alimentador AS d, Nodos.Alimentador AS o FROM Nodos INNER JOIN Lineas ON Nodos.Alimentador <> Lineas.Alimentador AND Nodos.Geoname = Lineas.Hasta INNER JOIN Nodos AS Nodos_1 ON Lineas.Desde = Nodos_1.Geoname WHERE (Nodos_1.Estado = 3)) A")
        conn.commit()
    except:
        conn.rollback()
        QMessageBox.information(None, 'EnerGis 6', "No se pudieron actualizar Alimentadores !")

def nodos_por_seccionador(self, conn):
    #----------------
    #-----LOOPS------
    #----------------
    nodos_en_loops = []
    seccionadores_en_loops = []
    lineas_abiertas = []
    b_proceso=True
    pasada = 0
    while b_proceso==True:
        b_proceso=False
        pasada = pasada + 1
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            mnodos = tuple(listanodos)

        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            mlineas = tuple(listalineas)
        #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
        #anulamos las lineas para eliminar loops
        for k in range (0, len(lineas_abiertas)):
            #QMessageBox.information(None, "Mensaje", "Linea abierta " + str(lineas_abiertas[k]))
            for n in range (0, len(mlineas)):
                if mlineas[n][1] == lineas_abiertas[k]:
                    #la saco de proximos nodos
                    for m in range(0, len(mnodos)):
                        for j in range(5, 37):
                            if mnodos[m][j] == mlineas[n][0]:
                                #resto uno a la cantidad de lineas
                                mnodos[m][4]=mnodos[m][4]-1
                                #corro las lineas asociadas
                                for l in range(j, 31):
                                    mnodos[m][l]=mnodos[m][l+1]
                                mnodos[m][32]=0
                    #anulo la linea
                    #QMessageBox.information(None, "Mensaje", "Anulo linea " + str(mlineas[n][1]))
                    mlineas[n][0]=0
                    #corto el for
                    break #n=len(mlineas)
        #--------------------------------------------
        buscar_loops(self, mnodos, mlineas)
        #--------------------------------------------
        for n in range(0, len(mnodos)):
            if mnodos[n][45] == 1:
                #si encontre loop tengo que seguir
                b_proceso=True
                #guardo los nodos en loops (aux)
                b_existe=False
                for m in range(0,len(nodos_en_loops)):
                    if nodos_en_loops[m]==mnodos[n][0]:
                        b_existe=True
                if b_existe==False:
                    nodos_en_loops.append(mnodos[n][0])
                #guardo los seccionadores en loops
                if mnodos[n][2] == 2:
                    b_existe=False
                    for m in range(0,len(seccionadores_en_loops)):
                        if seccionadores_en_loops[m]==mnodos[n][1]:
                            b_existe=True
                    if b_existe==False:
                        seccionadores_en_loops.append(mnodos[n][1])
        #tengo que elegir una linea del loop relacionada a un nodo del loop
        for l in range (0, len(mlineas)):
            if mlineas[l][12] == 1:
                #elijo la primer linea para abrir
                desde=False
                hasta=False
                #tiene que ser una linea relacionada a dos nodos del loop
                for k in range (0, len(nodos_en_loops)):
                    if nodos_en_loops[k]==mlineas[l][2]:
                        desde = True
                    if nodos_en_loops[k]==mlineas[l][3]:
                        hasta = True
                if desde==True and hasta==True:
                    b_existe=False
                    for m in range(0,len(lineas_abiertas)):
                        if lineas_abiertas[m]==mlineas[l][1]:
                            b_existe=True
                    if b_existe==False:
                        lineas_abiertas.append(mlineas[l][1])
                        #QMessageBox.information(None, "Mensaje", "Agrego linea " + str(mlineas[l][1]))
                    #corto el for
                    break
    #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
    #-----------------------------
    #-----REDUCCION DE SPURS------
    #-----------------------------
    #QMessageBox.information(None, "Mensaje", "reduccion")
    ruta = os.path.join(tempfile.gettempdir(), "jnodos")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jnodos = a.read()
        # Analizar el contenido JSON en un objeto Python
        listanodos = json.loads(jnodos)
        mnodos2 = tuple(listanodos)
    ruta = os.path.join(tempfile.gettempdir(), "jlineas")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jlineas = a.read()
        # Analizar el contenido JSON en un objeto Python
        listalineas = json.loads(jlineas)
        mlineas2 = tuple(listalineas)
    for k in range (0, len(lineas_abiertas)):
        for n in range (0, len(mlineas2)):
            if mlineas2[n][1] == lineas_abiertas[k]:
                #QMessageBox.information(None, "Mensaje", "Anulo linea: " + str(mlineas2[n][1]))
                #la saco de proximos nodos
                for m in range(0, len(mnodos2)):
                    for j in range(5, 37):
                        if mnodos2[m][j] == mlineas2[n][0]:
                            #resto uno a la cantidad de lineas
                            #QMessageBox.information(None, "Mensaje", "resto uno al nodo " + str(mnodos2[m][1]))
                            mnodos2[m][4]=mnodos2[m][4]-1
                            #QMessageBox.information(None, "Mensaje", "quedo en " + str(mnodos2[m][4]))
                            #corro las lineas asociadas
                            for l in range(j, 31):
                                mnodos2[m][l]=mnodos2[m][l+1]
                            mnodos2[m][32]=0
                            #corto el for
                            break
                #anulo la linea
                #QMessageBox.information(None, "Mensaje", "La anulo : " + str(mlineas2[n][1]))
                mlineas2[n][0]=0
                #corto el for
                break
    #vaciamos la tabla que guarda los nodos por seccionador (geoname, id)
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE nodos_seccionador")
        conn.commit()
    except:
        conn.rollback()
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    for n in range (0, len(mnodos2)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos2[n][1])
    cant_spurs = 1
    pasada = 0
    while cant_spurs != 0:
        cant_spurs = 0
        pasada = pasada + 1
        for n in range (0, len(mnodos2)):
            mnodos2[n][45] = 1
            if mnodos2[n][4]==0:
                mnodos2[n][45] = 0
            #si geoname <> 0 y (tiene una linea o es secc abierto) y no es fuente:
            if mnodos2[n][1]!=0 and (mnodos2[n][4]==1 or mnodos2[n][2]==3) and mnodos2[n][2]!=1:
                #sumo uno a la lista de spurs para continuar intentando reducir
                cant_spurs = cant_spurs + 1
                #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
                na = nodos_asociados[n]
                #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
                na.append(mnodos2[n][1])
                #Ahora el listado de asociados a este nodo es la lista total
                nodos_asociados[n] = na
                #Busco LA LINEA del nodo
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos2, mlineas2, n)
                for i in range (0, cant_lineas_del_nodo):
                    #Para cada una de las lineas del nodo, obtenemos desde y hasta
                    id = lineas_del_nodo[i]
                    pf = mlineas2[id][2]
                    pt = mlineas2[id][3]
                    #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                    #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                    #Si el nodo desde es n, el proximo setá el hasta
                    if pf==n:
                        #El nodo a asociar es el hasta
                        p = pt
                    elif pt==n:
                        #El nodo a asociar es el desde
                        p = pf
                    else: #Si no encuentro desde ni hasta hay un error
                        QMessageBox.information(None, "Mensaje", "Error 1 en línea : " + str(mlineas2[id][1]) + " (" + str(id) +")")
                    if mnodos2[p][0]!=0:
                        na = nodos_asociados[p]
                        for j in range (0, len(nodos_asociados[n])):
                            na.append(nodos_asociados[n][j])
                        nodos_asociados[p] = na
                    #Borro existencia de la linea
                    mlineas2[id][1] = 0
                    mlineas2[id][2] = 0
                    mlineas2[id][3] = 0
                    mlineas2[id][4] = 0
                    mlineas2[id][5] = 0
                    mlineas2[id][6] = 0
                    mlineas2[id][12] = 0
                    #Al proximo nodo le quito a n como proximo nodo
                    mnodos2[p][4] = mnodos2[p][4] - 1
                    for v in range (1, 32):
                        if mnodos2[p][4 + v] == id:
                            for m in range (v, 31):
                                mnodos2[p][4 + m] = mnodos2[p][4 + m + 1]
                            mnodos2[p][4 + 32] = 0
                            break #v = 32
                #Si es seccionador cerrado:
                if mnodos2[n][2]==2:
                    for l in range(0, len(seccionadores_en_loops)):
                        if mnodos2[n][1]==seccionadores_en_loops[l]:
                            #QMessageBox.information(None, "EnerGis 6", "Seccionador " + str(mnodos2[n][1]))
                            nodos_asociados[n]=None
                            break #l = len(seccionadores_en_loops)
                    #Si posee nodos asociados los paso a la base
                    if nodos_asociados[n]!=None:
                        if len(nodos_asociados[n])>0:
                            cursor = conn.cursor()
                            try: #geoname (seccinador). nodos (lista de nodos asociados)
                                cursor.execute("INSERT INTO Nodos_Seccionador (geoname, nodos) VALUES (" + str(nodos_geoname[n]) + ",'" + str(nodos_asociados[n]).replace('[','').replace(']','').replace(' ','') + "')")
                                conn.commit()
                            except:
                                conn.rollback()
                #Anulo el nodo que ya navegué
                mnodos2[n][1] = 0

def nodos_por_transformador(self, conn):
    #----------------
    #-----LOOPS------
    #----------------
    nodos_en_loops = []
    seccionadores_en_loops = []
    lineas_abiertas = []
    b_proceso=True
    pasada = 0
    while b_proceso==True:
        b_proceso=False
        pasada = pasada + 1
        #QMessageBox.information(None, "Mensaje", "pasada : " + str(pasada))
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            mnodos = tuple(listanodos)
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            mlineas = tuple(listalineas)
        #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
        #anulamos las lineas para eliminar loops
        for k in range (0, len(lineas_abiertas)):
            #QMessageBox.information(None, "Mensaje", "Linea abierta " + str(lineas_abiertas[k]))
            for n in range (0, len(mlineas)):
                if mlineas[n][1] == lineas_abiertas[k]:
                    #la saco de proximos nodos
                    for m in range(0, len(mnodos)):
                        for j in range(5, 37):
                            if mnodos[m][j] == mlineas[n][0]:
                                #resto uno a la cantidad de lineas
                                mnodos[m][4]=mnodos[m][4]-1
                                #corro las lineas asociadas
                                for l in range(j, 31):
                                    mnodos[m][l]=mnodos[m][l+1]
                                mnodos[m][32]=0
                    #anulo la linea
                    #QMessageBox.information(None, "Mensaje", "Anulo linea " + str(mlineas[n][1]))
                    mlineas[n][0]=0
                    #corto el for
                    break #n=len(mlineas)
        #--------------------------------------------
        buscar_loops(self, mnodos, mlineas)
        #--------------------------------------------
        for n in range(0, len(mnodos)):
            if mnodos[n][45] == 1:
                #si encontre loop tengo que seguir
                b_proceso=True
                #guardo los nodos en loops (aux)
                b_existe=False
                for m in range(0,len(nodos_en_loops)):
                    if nodos_en_loops[m]==mnodos[n][0]:
                        b_existe=True
                if b_existe==False:
                    nodos_en_loops.append(mnodos[n][0])
                #guardo los seccionadores en loops
                if mnodos[n][2] == 2:
                    b_existe=False
                    for m in range(0,len(seccionadores_en_loops)):
                        if seccionadores_en_loops[m]==mnodos[n][1]:
                            b_existe=True
                    if b_existe==False:
                        seccionadores_en_loops.append(mnodos[n][1])
        #tengo que elegir una linea del loop relacionada a un nodo del loop
        for l in range (0, len(mlineas)):
            if mlineas[l][12] == 1:
                #elijo la primer linea para abrir
                desde=False
                hasta=False
                #tiene que ser una linea relacionada a dos nodos del loop
                for k in range (0, len(nodos_en_loops)):
                    if nodos_en_loops[k]==mlineas[l][2]:
                        desde = True
                    if nodos_en_loops[k]==mlineas[l][3]:
                        hasta = True
                if desde==True and hasta==True:
                    b_existe=False
                    for m in range(0,len(lineas_abiertas)):
                        if lineas_abiertas[m]==mlineas[l][1]:
                            b_existe=True
                    if b_existe==False:
                        lineas_abiertas.append(mlineas[l][1])
                        #QMessageBox.information(None, "Mensaje", "Agrego linea " + str(mlineas[l][1]))
                    #corto el for
                    break
    #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
    #-----------------------------
    #-----REDUCCION DE SPURS------
    #-----------------------------
    #QMessageBox.information(None, "Mensaje", "reduccion")
    ruta = os.path.join(tempfile.gettempdir(), "jnodos")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jnodos = a.read()
        # Analizar el contenido JSON en un objeto Python
        listanodos = json.loads(jnodos)
        mnodos2 = tuple(listanodos)
    ruta = os.path.join(tempfile.gettempdir(), "jlineas")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jlineas = a.read()
        # Analizar el contenido JSON en un objeto Python
        listalineas = json.loads(jlineas)
        mlineas2 = tuple(listalineas)
    for k in range (0, len(lineas_abiertas)):
        for n in range (0, len(mlineas2)):
            if mlineas2[n][1] == lineas_abiertas[k]:
                #QMessageBox.information(None, "Mensaje", "Anulo linea: " + str(mlineas2[n][1]))
                #la saco de proximos nodos
                for m in range(0, len(mnodos2)):
                    for j in range(5, 37):
                        if mnodos2[m][j] == mlineas2[n][0]:
                            #resto uno a la cantidad de lineas
                            #QMessageBox.information(None, "Mensaje", "resto uno al nodo " + str(mnodos2[m][1]))
                            mnodos2[m][4]=mnodos2[m][4]-1
                            #QMessageBox.information(None, "Mensaje", "quedo en " + str(mnodos2[m][4]))
                            #corro las lineas asociadas
                            for l in range(j, 31):
                                mnodos2[m][l]=mnodos2[m][l+1]
                            mnodos2[m][32]=0
                            #corto el for
                            break
                #anulo la linea
                #QMessageBox.information(None, "Mensaje", "La anulo : " + str(mlineas2[n][1]))
                mlineas2[n][0]=0
                #corto el for
                break
    #vaciamos la tabla que guarda los nodos por trafo (geoname, id)
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE Nodos_Transformador")
        conn.commit()
    except:
        conn.rollback()
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    #armo un array vacio con una columna por nodo para alojar a los nodos asociados a cada uno
    for n in range (0, len(mnodos2)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos2[n][1])
    #Reduccion de Red por niveles de transformacion
    #Se utiliza el elemento y no el estado de los mismos
    #Se recorre el array de nodos, se le va asignando geoname=0 para anularlos
    #Con un máximo de 10 niveles se pretende encontrar los nodos por trafo
    nivel = 1
    #Arranque
    seguir = 1
    #Se seguirá siempre y cuando queden trafos por recorrer
    while seguir == 1:
        #Arranque
        cant_spurs = 1
        #Se seguirá siempre y cuando existan spurs
        while cant_spurs != 0:
            #Blanqueo cantidad de spurs
            cant_spurs = 0
            #Se recorre el array de nodos tratando de agrupar para este nivel todos los nodos hacia la salida
            for n in range (0, len(mnodos2)):
                #si es aislado lo desmarco
                if mnodos2[n][4]==0:
                    mnodos2[n][45] = 0
                else:
                    #Marco el nodo que analizo en posicion 45
                    mnodos2[n][45] = 1
                #Si no esta borrado y (es spur o es SA) y no es fuente
                if mnodos2[n][1]!=0 and (mnodos2[n][4]==1 or mnodos2[n][39]==3) and mnodos2[n][2]!=1:
                    #Si no es trafo:
                    if mnodos2[n][2]!=4:
                        #sumo uno a la lista de spurs para continuar intentando reducir
                        cant_spurs = cant_spurs + 1
                        #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
                        na = nodos_asociados[n]
                        #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
                        na.append(mnodos2[n][1])
                        #Ahora el listado de asociados a este nodo es la lista total
                        nodos_asociados[n] = na
                        #Busco LA LINEA del nodo
                        cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos2, mlineas2, n)
                        for i in range (0, cant_lineas_del_nodo):
                            #Para cada una de las lineas del nodo, obtenemos desde y hasta
                            id = lineas_del_nodo[i]
                            pf = mlineas2[id][2]
                            pt = mlineas2[id][3]
                            #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                            #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                            #Si el nodo desde es n, el proximo setá el hasta
                            if pf==n:
                                #El nodo a asociar es el hasta
                                p = pt
                            elif pt==n:
                                #El nodo a asociar es el desde
                                p = pf
                            else: #Si no encuentro desde ni hasta hay un error
                                QMessageBox.information(None, "Mensaje", "Error 1 en línea : " + str(mlineas2[id][1]) + " (" + str(id) +")")
                            if mnodos2[p][0]!=0:
                                na = nodos_asociados[p]
                                for j in range (0, len(nodos_asociados[n])):
                                    na.append(nodos_asociados[n][j])
                                nodos_asociados[p] = na
                            #Borro existencia de la linea
                            mlineas2[id][1] = 0
                            mlineas2[id][2] = 0
                            mlineas2[id][3] = 0
                            mlineas2[id][4] = 0
                            mlineas2[id][5] = 0
                            mlineas2[id][6] = 0
                            mlineas2[id][12] = 0
                            #Al proximo nodo le quito a n como proximo nodo
                            mnodos2[p][4] = mnodos2[p][4] - 1
                            for v in range (1, 32):
                                if mnodos2[p][4 + v] == id:
                                    for m in range (v, 31):
                                        mnodos2[p][4 + m] = mnodos2[p][4 + m + 1]
                                    mnodos2[p][4 + 32] = 0
                                    break #v = 32
                        #Anulo el nodo que ya navegué
                        mnodos2[n][1] = 0
                        mnodos2[n][45] = 0
                    else: #Si el spur es trafo:
                        #Si posee nodos asociados los paso a la base
                        if len(nodos_asociados[n])>0:
                            cursor = conn.cursor()
                            try: #geoname (nodo). id (geoname trasformador)
                                cursor.execute("INSERT INTO Nodos_Transformador SELECT geoname, " + str(nodos_geoname[n]) + " FROM Nodos WHERE Nodos.Tension>0 AND geoname IN (" + str(nodos_geoname[n]) + "," + str(nodos_asociados[n]).replace('[','').replace(']','') + ")")
                                conn.commit()
                            except:
                                conn.rollback()
                            #Ya grabados los nodos asociados a la salida, desasociamos los nodos para que no pasen aguas arriba
                            nodos_asociados[n] = []
                            #nodos_asociados[n].append(0)
                            #Convierto a la salida en un nodo comun para poder seguir aguas arriba
                            mnodos2[n][2] = 0
        #si tengo todavia salidas para navegar, sumo un nivel
        existe=0
        for n in range (0, len(mnodos2)):
            if mnodos2[n][1]!=0 and mnodos2[n][2]==4:
                existe=1
                #QMessageBox.information(None, "Mensaje", "Salida : " + str(mnodos[n][1]))
                break #n = len(mnodos2)
        if existe==1:
            nivel = nivel + 1
            #QMessageBox.information(None, "Mensaje", "Nivel : " + str(nivel))
            seguir = 1
            if nivel > 10:
                seguir = 0
        else:
            seguir = 0
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE Suministros_Trafos")
        cursor.execute("INSERT INTO Suministros_Trafos SELECT DISTINCT Geoname, id FROM Suministros INNER JOIN Nodos_Transformador ON Suministros.id_nodo = Nodos_Transformador.Geoname")
        conn.commit()
    except:
        conn.rollback()

def cadena_a_la_fuente(self, conn, nodos_camino):
    #Reduce la red a los nodos del camino del nodo seleccionado a la fuente
    #ATENCION - CORTA EN TRAFOS Y REGULADORES - !!!
    #----------------
    #-----LOOPS------
    #----------------
    nodos_en_loops = []
    seccionadores_en_loops = []
    lineas_abiertas = []
    b_proceso=True
    pasada = 0
    mnodos = []
    mnodos2 = []
    mlineas = []
    mlineas2 = []
    while b_proceso==True:
        b_proceso=False
        pasada = pasada + 1
        ruta = os.path.join(tempfile.gettempdir(), "jnodos")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jnodos = a.read()
            # Analizar el contenido JSON en un objeto Python
            listanodos = json.loads(jnodos)
            mnodos = tuple(listanodos)
        ruta = os.path.join(tempfile.gettempdir(), "jlineas")
        # Verificar si el archivo existe antes de intentar cargarlo
        if os.path.exists(ruta):
            with open(ruta, "r") as a:
                jlineas = a.read()
            # Analizar el contenido JSON en un objeto Python
            listalineas = json.loads(jlineas)
            mlineas = tuple(listalineas)
        #anulamos las lineas para eliminar loops
        for k in range (0, len(lineas_abiertas)):
            #QMessageBox.information(None, "Mensaje", "Linea abierta " + str(lineas_abiertas[k]))
            for n in range (0, len(mlineas)):
                if mlineas[n][1] == lineas_abiertas[k]:
                    #la saco de proximos nodos
                    for m in range(0, len(mnodos)):
                        for j in range(5, 37):
                            if mnodos[m][j] == mlineas[n][0]:
                                #resto uno a la cantidad de lineas
                                mnodos[m][4]=mnodos[m][4]-1
                                #corro las lineas asociadas
                                for l in range(j, 31):
                                    mnodos[m][l]=mnodos[m][l+1]
                                mnodos[m][32]=0
                    #anulo la linea
                    #QMessageBox.information(None, "Mensaje", "Anulo linea " + str(mlineas[n][1]))
                    mlineas[n][0]=0
                    #corto el for
                    break #n=len(mlineas)
        #--------------------------------------------
        buscar_loops(self, mnodos, mlineas)
        #--------------------------------------------
        for n in range(0, len(mnodos)):
            if mnodos[n][45] == 1:
                #si encontre loop tengo que seguir
                b_proceso=True
                #guardo los nodos en loops (aux)
                b_existe=False
                for m in range(0,len(nodos_en_loops)):
                    if nodos_en_loops[m]==mnodos[n][0]:
                        b_existe=True
                if b_existe==False:
                    nodos_en_loops.append(mnodos[n][0])
                #guardo los seccionadores en loops
                if mnodos[n][2] == 2:
                    b_existe=False
                    for m in range(0,len(seccionadores_en_loops)):
                        if seccionadores_en_loops[m]==mnodos[n][1]:
                            b_existe=True
                    if b_existe==False:
                        seccionadores_en_loops.append(mnodos[n][1])
        #tengo que elegir una linea del loop relacionada a un nodo del loop
        for l in range (0, len(mlineas)):
            if mlineas[l][12] == 1:
                #elijo la primer linea para abrir
                desde=False
                hasta=False
                #tiene que ser una linea relacionada a dos nodos del loop
                for k in range (0, len(nodos_en_loops)):
                    if nodos_en_loops[k]==mlineas[l][2]:
                        desde = True
                    if nodos_en_loops[k]==mlineas[l][3]:
                        hasta = True
                if desde==True and hasta==True:
                    b_existe=False
                    for m in range(0,len(lineas_abiertas)):
                        if lineas_abiertas[m]==mlineas[l][1]:
                            b_existe=True
                    if b_existe==False:
                        lineas_abiertas.append(mlineas[l][1])
                    #corto el for
                    break
    #-----------------------------
    #-----REDUCCION DE SPURS------
    #-----------------------------
    ruta = os.path.join(tempfile.gettempdir(), "jnodos")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jnodos = a.read()
        # Analizar el contenido JSON en un objeto Python
        listanodos = json.loads(jnodos)
        mnodos2 = tuple(listanodos)
    ruta = os.path.join(tempfile.gettempdir(), "jlineas")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jlineas = a.read()
        # Analizar el contenido JSON en un objeto Python
        listalineas = json.loads(jlineas)
        mlineas2 = tuple(listalineas)
    for k in range (0, len(lineas_abiertas)):
        for n in range (0, len(mlineas2)):
            if mlineas2[n][1] == lineas_abiertas[k]:
                #QMessageBox.information(None, "Mensaje", "Anulo linea: " + str(mlineas2[n][1]))
                #la saco de proximos nodos
                for m in range(0, len(mnodos2)):
                    for j in range(5, 37):
                        if mnodos2[m][j] == mlineas2[n][0]:
                            #resto uno a la cantidad de lineas
                            #QMessageBox.information(None, "Mensaje", "resto uno al nodo " + str(mnodos2[m][1]))
                            mnodos2[m][4]=mnodos2[m][4]-1
                            #QMessageBox.information(None, "Mensaje", "quedo en " + str(mnodos2[m][4]))
                            #corro las lineas asociadas
                            for l in range(j, 31):
                                mnodos2[m][l]=mnodos2[m][l+1]
                            mnodos2[m][32]=0
                            #corto el for
                            break
                #anulo la linea
                #QMessageBox.information(None, "Mensaje", "La anulo : " + str(mlineas2[n][1]))
                mlineas2[n][0]=0
                #corto el for
                break
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    #armo un array vacio con una columna por nodo para alojar a los nodos asociados a cada uno
    for n in range (0, len(mnodos2)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos2[n][1])
    #Arranque
    cant_spurs = 1
    #Se seguirá siempre y cuando existan spurs
    while cant_spurs != 0:
        #QMessageBox.information(None, "Mensaje", str(cant_spurs) + " spurs")
        #Blanqueo cantidad de spurs
        cant_spurs = 0
        #QMessageBox.information(None, "Mensaje", str(len(mnodos2)) + " nodos en nodos2")
        #Se recorre el array de nodos tratando de agrupar para este nivel todos los nodos hacia la salida
        for n in range (0, len(mnodos2)):
            #si es aislado lo desmarco
            if mnodos2[n][4]==0:
                mnodos2[n][45] = 0
            else:
                #Marco el nodo que analizo en posicion 45
                mnodos2[n][45] = 1
            #Si no esta borrado y (es spur o es SA) y no es fuente
            if mnodos2[n][1]!=0 and (mnodos2[n][4]==1 or mnodos2[n][39]==3) and mnodos2[n][2]!=1:
                #Si no está en la lista de nodos del camino a la fuente:
                if not n in nodos_camino:
                    #sumo uno a la lista de spurs para continuar intentando reducir
                    cant_spurs = cant_spurs + 1
                    #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
                    na = nodos_asociados[n]
                    #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
                    na.append(mnodos2[n][1])
                    #Ahora el listado de asociados a este nodo es la lista total
                    nodos_asociados[n] = na
                    #Busco LA LINEA del nodo
                    cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos2, mlineas2, n)
                    for i in range (0, cant_lineas_del_nodo):
                        #Para cada una de las lineas del nodo, obtenemos desde y hasta
                        id = lineas_del_nodo[i]
                        pf = mlineas2[id][2]
                        pt = mlineas2[id][3]
                        #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                        #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                        #Si el nodo desde es n, el proximo setá el hasta
                        if pf==n:
                            #El nodo a asociar es el hasta
                            p = pt
                        elif pt==n:
                            #El nodo a asociar es el desde
                            p = pf
                        else: #Si no encuentro desde ni hasta hay un error
                            QMessageBox.information(None, "Mensaje", "Error 1 en línea : " + str(mlineas2[id][1]) + " (" + str(id) +")")
                        if mnodos2[p][0]!=0:
                            na = nodos_asociados[p]
                            for j in range (0, len(nodos_asociados[n])):
                                na.append(nodos_asociados[n][j])
                            nodos_asociados[p] = na
                        #Borro existencia de la linea
                        mlineas2[id][1] = 0
                        mlineas2[id][2] = 0
                        mlineas2[id][3] = 0
                        mlineas2[id][4] = 0
                        mlineas2[id][5] = 0
                        mlineas2[id][6] = 0
                        mlineas2[id][12] = 0
                        #Al proximo nodo le quito a n como proximo nodo
                        mnodos2[p][4] = mnodos2[p][4] - 1
                        for v in range (1, 32):
                            if mnodos2[p][4 + v] == id:
                                for m in range (v, 31):
                                    mnodos2[p][4 + m] = mnodos2[p][4 + m + 1]
                                mnodos2[p][4 + 32] = 0
                                break #v = 32
                    #Anulo el nodo que ya navegué
                    mnodos2[n][1] = 0
                    mnodos2[n][45] = 0
    return nodos_asociados

def buscar_desconectados(self, mnodos, mlineas):
    #----------------
    #-----LOOPS------
    #----------------
    nodos_en_loops = []
    seccionadores_en_loops = []
    lineas_abiertas = []
    b_proceso=True
    pasada = 0
    mnodos = []
    mnodos2 = []
    mlineas = []
    mlineas2 = []
    while b_proceso==True:
        b_proceso=False
        pasada = pasada + 1
        #QMessageBox.information(None, "Mensaje", "pasada : " + str(pasada))
        #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
        #anulamos las lineas para eliminar loops
        for k in range (0, len(lineas_abiertas)):
            #QMessageBox.information(None, "Mensaje", "Linea abierta " + str(lineas_abiertas[k]))
            for n in range (0, len(mlineas)):
                if mlineas[n][1] == lineas_abiertas[k]:
                    #la saco de proximos nodos
                    for m in range(0, len(mnodos)):
                        for j in range(5, 37):
                            if mnodos[m][j] == mlineas[n][0]:
                                #resto uno a la cantidad de lineas
                                mnodos[m][4]=mnodos[m][4]-1
                                #corro las lineas asociadas
                                for l in range(j, 31):
                                    mnodos[m][l]=mnodos[m][l+1]
                                mnodos[m][32]=0
                    #anulo la linea
                    #QMessageBox.information(None, "Mensaje", "Anulo linea " + str(mlineas[n][1]))
                    mlineas[n][0]=0
                    #corto el for
                    break #n=len(mlineas)
        #--------------------------------------------
        buscar_loops(self, mnodos, mlineas)
        #--------------------------------------------
        for n in range(0, len(mnodos)):
            if mnodos[n][45] == 1:
                #si encontre loop tengo que seguir
                b_proceso=True
                #guardo los nodos en loops (aux)
                b_existe=False
                for m in range(0,len(nodos_en_loops)):
                    if nodos_en_loops[m]==mnodos[n][0]:
                        b_existe=True
                if b_existe==False:
                    nodos_en_loops.append(mnodos[n][0])
                #guardo los seccionadores en loops
                if mnodos[n][2] == 2:
                    b_existe=False
                    for m in range(0,len(seccionadores_en_loops)):
                        if seccionadores_en_loops[m]==mnodos[n][1]:
                            b_existe=True
                    if b_existe==False:
                        seccionadores_en_loops.append(mnodos[n][1])
        #tengo que elegir una linea del loop relacionada a un nodo del loop
        for l in range (0, len(mlineas)):
            if mlineas[l][12] == 1:
                #elijo la primer linea para abrir
                desde=False
                hasta=False
                #tiene que ser una linea relacionada a dos nodos del loop
                for k in range (0, len(nodos_en_loops)):
                    if nodos_en_loops[k]==mlineas[l][2]:
                        desde = True
                    if nodos_en_loops[k]==mlineas[l][3]:
                        hasta = True
                if desde==True and hasta==True:
                    b_existe=False
                    for m in range(0,len(lineas_abiertas)):
                        if lineas_abiertas[m]==mlineas[l][1]:
                            b_existe=True
                    if b_existe==False:
                        lineas_abiertas.append(mlineas[l][1])
                        #QMessageBox.information(None, "Mensaje", "Agrego linea " + str(mlineas[l][1]))
                    #corto el for
                    break
    #QMessageBox.information(None, "Mensaje", "Lineas abiertas " + str(lineas_abiertas))
    #-----------------------------
    #-----REDUCCION DE SPURS------
    #-----------------------------
    #QMessageBox.information(None, "Mensaje", "reduccion")
    ruta = os.path.join(tempfile.gettempdir(), "jnodos")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jnodos = a.read()
        # Analizar el contenido JSON en un objeto Python
        listanodos = json.loads(jnodos)
        mnodos2 = tuple(listanodos)

    ruta = os.path.join(tempfile.gettempdir(), "jlineas")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jlineas = a.read()
        # Analizar el contenido JSON en un objeto Python
        listalineas = json.loads(jlineas)
        mlineas2 = tuple(listalineas)
    for k in range (0, len(lineas_abiertas)):
        for n in range (0, len(mlineas2)):
            if mlineas2[n][1] == lineas_abiertas[k]:
                #QMessageBox.information(None, "Mensaje", "Anulo linea: " + str(mlineas2[n][1]))
                #la saco de proximos nodos
                for m in range(0, len(mnodos2)):
                    for j in range(5, 37):
                        if mnodos2[m][j] == mlineas2[n][0]:
                            #resto uno a la cantidad de lineas
                            #QMessageBox.information(None, "Mensaje", "resto uno al nodo " + str(mnodos2[m][1]))
                            mnodos2[m][4]=mnodos2[m][4]-1
                            #QMessageBox.information(None, "Mensaje", "quedo en " + str(mnodos2[m][4]))
                            #corro las lineas asociadas
                            for l in range(j, 31):
                                mnodos2[m][l]=mnodos2[m][l+1]
                            mnodos2[m][32]=0
                            #corto el for
                            break
                #anulo la linea
                #QMessageBox.information(None, "Mensaje", "La anulo : " + str(mlineas2[n][1]))
                mlineas2[n][0]=0
                #corto el for
                break
    #reduccion de matrices de nodos y lineas
    nodos_asociados = [[]]
    nodos_geoname = []
    #armo un array vacio con una columna por nodo para alojar a los nodos asociados a cada uno
    for n in range (0, len(mnodos2)):
        nodos_asociados.append([])
        nodos_geoname.append(mnodos2[n][1])
    #Eliminamos los seccionadores abiertos
    for n in range (0, len(mnodos2)):
        if mnodos2[n][2]==3:
            #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
            na = nodos_asociados[n]
            #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
            na.append(mnodos2[n][0])
            #Ahora el listado de asociados a este nodo es la lista total
            nodos_asociados[n] = na
            #Busco las lineas del nodo
            cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos2, mlineas2, n)
            for i in range (0, cant_lineas_del_nodo):
                #Para cada una de las lineas del nodo, obtenemos desde y hasta
                id = lineas_del_nodo[i]
                pf = mlineas2[id][2]
                pt = mlineas2[id][3]
                #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                #Si el nodo desde es n, el proximo setá el hasta
                if pf==n:
                    #El nodo a asociar es el hasta
                    p = pt
                elif pt==n:
                    #El nodo a asociar es el desde
                    p = pf
                else: #Si no encuentro desde ni hasta hay un error
                    QMessageBox.information(None, "Mensaje", "Error 1 en línea : " + str(mlineas2[id][1]) + " (" + str(id) +")")
                if mnodos2[p][0]!=0:
                    na = nodos_asociados[p]
                    for j in range (0, len(nodos_asociados[n])):
                        na.append(nodos_asociados[n][j])
                    nodos_asociados[p] = na
                #Borro existencia de la linea
                mlineas2[id][1] = 0
                mlineas2[id][2] = 0
                mlineas2[id][3] = 0
                mlineas2[id][4] = 0
                mlineas2[id][5] = 0
                mlineas2[id][6] = 0
                mlineas2[id][12] = 0
                #Al proximo nodo le quito a n como proximo nodo
                mnodos2[p][4] = mnodos2[p][4] - 1
                for v in range (1, 32):
                    if mnodos2[p][4 + v] == id:
                        for m in range (v, 31):
                            mnodos2[p][4 + m] = mnodos2[p][4 + m + 1]
                        mnodos2[p][4 + 32] = 0
                        break #v = 32

                mnodos2[n][1]=0
    #Reduccion de Red
    #Se recorre el array de nodos, se le va asignando geoname=0 para anularlos
    #Arranque
    cant_spurs = 1
    #Se seguirá siempre y cuando existan spurs
    while cant_spurs != 0:
        #Blanqueo cantidad de spurs
        cant_spurs = 0
        #Se recorre el array de nodos tratando de agrupar todos los nodos hacia la fuente
        for n in range (0, len(mnodos2)):
            #si es aislado lo desmarco
            if mnodos2[n][4]==0:
                mnodos2[n][45] = 0
            else:
                #Marco el nodo que analizo en posicion 45
                mnodos2[n][45] = 1
            #Si no esta borrado y (es spur o es SA)
            if mnodos2[n][1]!=0 and mnodos2[n][4]==1 and mnodos2[n][2]!=1:
                #El listado de asociaciones inicial es el que tenia el nodo al momento de consultarlo
                na = nodos_asociados[n]
                #Al listado de asociados que posee este nodo (que ahora es spur) le agrego este mismo
                na.append(mnodos2[n][0])
                #Ahora el listado de asociados a este nodo es la lista total
                nodos_asociados[n] = na
                #Busco LA LINEA del nodo
                cant_lineas_del_nodo, lineas_del_nodo, proximos_nodos = buscar_lineas_segun_nodo(self, mnodos2, mlineas2, n)
                for i in range (0, cant_lineas_del_nodo):
                    #Para cada una de las lineas del nodo, obtenemos desde y hasta
                    id = lineas_del_nodo[i]
                    pf = mlineas2[id][2]
                    pt = mlineas2[id][3]
                    #Detecto el próximo nodo asi le puedo pasar los nodos asociados del actual
                    #Tienen que ser nodos aguas arriba, o sea que no tienen que estar marcados
                    #Si el nodo desde es n, el proximo setá el hasta
                    if pf==n:
                        #El nodo a asociar es el hasta
                        p = pt
                    elif pt==n:
                        #El nodo a asociar es el desde
                        p = pf
                    else: #Si no encuentro desde ni hasta hay un error
                        QMessageBox.information(None, "Mensaje", "Error 2 en línea : " + str(mlineas2[id][1]) + " (" + str(id) +")")
                        break
                    if mnodos2[p][0]!=0:
                        na = nodos_asociados[p]
                        for j in range (0, len(nodos_asociados[n])):
                            na.append(nodos_asociados[n][j])
                        nodos_asociados[p] = na

                        #al spur le borramos sus asociados
                        nodos_asociados[n]=[]
                    #Borro existencia de la linea
                    mlineas2[id][1] = 0
                    mlineas2[id][2] = 0
                    mlineas2[id][3] = 0
                    mlineas2[id][4] = 0
                    mlineas2[id][5] = 0
                    mlineas2[id][6] = 0
                    mlineas2[id][12] = 0
                    #Al proximo nodo le quito a n como proximo nodo
                    mnodos2[p][4] = mnodos2[p][4] - 1
                    for v in range (1, 32):
                        if mnodos2[p][4 + v] == id:
                            for m in range (v, 31):
                                mnodos2[p][4 + m] = mnodos2[p][4 + m + 1]
                            mnodos2[p][4 + 32] = 0
                            break #v = 32

                #Anulo el nodo que ya navegué
                mnodos2[n][1] = 0
                mnodos2[n][45] = 0
        for n in range (0, len(mnodos2)):
            #Si no esta borrado y (es spur o es SA)
            if mnodos2[n][1]!=0 and mnodos2[n][4]==1 and mnodos2[n][2]!=1:
                #sumo uno a la lista de spurs para continuar intentando reducir
                cant_spurs = 1
                break
    #al terminar la reducción, quedan fuentes con sus nodos acumulados
    #y nodos acumulados con los
    ruta = os.path.join(tempfile.gettempdir(), "jnodos")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jnodos = a.read()
        # Analizar el contenido JSON en un objeto Python
        listanodos = json.loads(jnodos)
        mnodos = tuple(listanodos)
    ruta = os.path.join(tempfile.gettempdir(), "jlineas")
    # Verificar si el archivo existe antes de intentar cargarlo
    if os.path.exists(ruta):
        with open(ruta, "r") as a:
            jlineas = a.read()
        # Analizar el contenido JSON en un objeto Python
        listalineas = json.loads(jlineas)
        mlineas = tuple(listalineas)
    resultado_n=[]
    resultado_l=[]
    lineas=[]
    for n in range (0, len(mnodos)):
        if mnodos[n][2]!=1 and mnodos[n][2]!=3:
            if len(nodos_asociados[n])>0:
                resultado_n.append(mnodos[n][1])
                for v in range (1, 32):
                    if mnodos[n][4 + v]==0:
                        mnodos
                    else:
                        lineas.append(mnodos[n][4 + v])
                for j in range (0, len(nodos_asociados[n])):
                    resultado_n.append(mnodos[nodos_asociados[n][j]][1])
                    for v in range (1, 32):
                        if mnodos[nodos_asociados[n][j]][4 + v]==0:
                            break
                        else:
                            lineas.append(mnodos[nodos_asociados[n][j]][4 + v])
    for l in range (0, len(lineas)):
        if mnodos[mlineas[lineas[l]][2]][1] in resultado_n and mnodos[mlineas[lineas[l]][3]][1] in resultado_n:
            resultado_l.append(mlineas[lineas[l]][1])
    return resultado_n, resultado_l
