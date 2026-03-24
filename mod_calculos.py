# encoding: utf-8
#-----------------------------------------------------------
# Copyright (C) 2025 Juan Messina
#-----------------------------------------------------------
# Licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#---------------------------------------------------------------------

from PyQt6.QtWidgets import QMessageBox
import math
import cmath

def __init__(self):
    pass

def newton_raphson(self):
    import numpy as np

    Yii=[]
    f = open('c:/gis/energis6/Yii.txt','r')
    for elemento in f:
        lista = elemento.strip('\n').split(', ')
        Yii.append(lista)
    f.close()

    Yij=[]
    f = open('c:/gis/energis6/Yij.txt','r')
    for elemento in f:
        lista = elemento.strip('\n').split(', ')
        Yij.append(lista)
    f.close()

    Bus=[]
    f = open('c:/gis/energis6/Bus.txt','r')
    for elemento in f:
        lista = elemento.strip('\n').split(', ')
        Bus.append(lista)
    f.close()
    j = 0
    k = 0
    n = 0
    f = open('c:/gis/energis6/newton_raphson.txt','w')
    import traceback
    try:
        npq = 0
        npv = 0
        nns = 0
        nsc = 0
        for n1 in range(1, len(Bus)):
            if n1 != 0:
                tipo = Bus[n1][2]
                if tipo=='SL':
                    pass
                if tipo=='PQ':
                    npq = npq + 1
                if tipo=='PV':
                    npv = npv + 1
                if tipo=='NS':
                    nns = nns + 1
                if tipo=='NC':
                    nsc = nsc + 1
                if tipo=='NA':
                    pass
        #matriz J
        filas_j = 2 * npq + 2 * nns + 2 * nsc + npv
        columnas_j =  2 * npq + 2 * nns + 2 * nsc + npv
        J = np.zeros((filas_j, columnas_j))

        QMessageBox.information(None, 'EnerGis 6', '[J] ' + str(filas_j) + ' x ' + str(columnas_j))
        #return

        #f.writelines('\n')
        #f.writelines('Flujo' + '\n')
        error_maximo = 0.00001
        for j in range(1, 200):
            #f.writelines('Iteracion ' + str(j) + '\n')
            #f.writelines('------------' + '\n')
            #-------------------------------
            #vector de potencias para calular los residuos
            DS = np.zeros(filas_j, dtype=float)
            #vector de resultados
            DR = np.zeros(filas_j, dtype=float)
            #-------------------------------
            error = 0
            #----------------------
            #armado de las matrices
            #----------------------
            filH = - 1
            filN = - 1
            filM = npq + nns + nsc + npv - 1
            filL = npq + nns + nsc + npv - 1

            for n1 in range(1, len(Bus)):
                #-------------------------------
                #geoname = Bus[n1][0]
                #aux = Bus[n1][1]
                tipo = Bus[n1][2]
                #-------------------------------
                #      | H  N |
                #  J = |      |
                #      | M  L |
                #-------------------------------
                if tipo!='SL' and tipo!='NA':
                    filH = filH + 1
                    filN = filN + 1
                    if tipo!='PV':
                        filM = filM + 1
                        filL = filL + 1
                #-------------------------------
                #vuelvo las columnas al inicio
                #-------------------------------
                colH = 0
                colN = npq + nns + npv
                colM = 0
                colL = npq + nns + npv
                #-------------------------------
                if tipo!='SL' and tipo!='NA':
                    #dado un nodo n1:
                    vi = float(Bus[n1][3])
                    di = float(Bus[n1][4])
                    y = complex(float(Yii[n1][35]), float(Yii[n1][36]))
                    yii = abs(y)
                    tii = math.degrees(cmath.phase(y))
                    sumyijvjc = 0
                    sumyijvjs = 0
                    cant_lineas=int(Yii[n1][2])
                    for i in range(3, 3 + cant_lineas):
                        lij = int(Yii[n1][i])
                        if int(Yij[lij][2])==n1:
                            nj=int(Yij[lij][3])
                        else:
                            nj=int(Yij[lij][2])
                        #si el proximo nodo es un NA no le sumo Y*V
                        if int(Yii[nj][38])!=3:
                            vj = float(Bus[nj][3])
                            dj = float(Bus[nj][4])
                            y = complex(float(Yij[lij][4]), float(Yij[lij][5]))
                            yij = abs(y)
                            tij = math.degrees(cmath.phase(y))
                            sumyijvjc = sumyijvjc + yij * vj * math.cos(di-dj-tij)
                            sumyijvjs = sumyijvjs + yij * vj * math.sin(di-dj-tij)
                    p = float(Bus[n1][15]) - float(Bus[n1][9])
                    #calculo las potencias
                    pi = vi*sumyijvjc
                    qi = vi*sumyijvjs
                    #guardo para la proxima iteración
                    Bus[n1][15] = pi
                    Bus[n1][16] = qi

                    #calculo el error
                    dp = p - pi
                    #voy calculando el máximo (error)
                    if abs(dp)>error:
                        error = abs(dp)
                    #      | H  N |
                    #  J = |      |
                    #      | M  L |
                    #saco el unico Hii (J1)
                    Hii = - qi - (vi**2)*yii*math.sin(tii)
                    #saco el unico Nii (J2)
                    Nii = (vi**2)*yii*math.cos(tii) + pi
                    #saco el unico Mii (J3)
                    Mii = pi - (vi**2)*yii*math.cos(tii)
                    #saco el unico Lii (J4)
                    Lii = qi - (vi**2)*yii*math.sin(tii)
                    #-------------------------------

                    #vector de potencias para calular los residuos
                    DS[filH] = pi
                    #vector de resultados
                    DR[filH] = 0

                    DS[filM] = qi
                    #vector de resultados
                    DR[filM] = 0

                    for n2 in range(1, len(Bus)):
                        tipo2 = Bus[n2][2]
                        #-------------------------------
                        #      | H  N |
                        #  J = |      |
                        #      | M  L |
                        #-------------------------------
                        if tipo!='SL' and tipo2!='NA':
                            colH = colH + 1
                            colN = colN + 1
                            colM = colM + 1
                            colL = colL + 1
                        #-------------------------------
                        if tipo2!='SL' and tipo2!='NA':
                            if n2==n1:
                                J[filH][colH] = Hii
                                if tipo!='PV':
                                    J[filN][colN] = Nii
                                    J[filM][colM] = Mii
                                    J[filL][colL] = Lii
                            else:
                                vj = float(Bus[n2][3])
                                dj = float(Bus[n2][4])
                                yij = 0
                                tij = 0
                                cant_lineas=int(Yii[n2][2])
                                for i in range(3, 3 + cant_lineas):
                                    lij = int(Yii[n2][i])
                                    if int(Yij[lij][2])==n1:
                                        y = complex(float(Yij[lij][4]), float(Yij[lij][5]))
                                        yij = abs(y)
                                        tij = math.degrees(cmath.phase(y))
                                    else:
                                        y = complex(float(Yij[lij][4]), float(Yij[lij][5]))
                                        yij = abs(y)
                                        tij = math.degrees(cmath.phase(y))
                                #-------------------------------
                                Hij = vi*vj*yij*math.sin(di-dj-tij)
                                Nij = vi*vj*yij*math.cos(di-dj-tij)
                                Mij = -vi*vj*yij*math.cos(di-dj-tij)
                                Lij = vi*vj*yij*math.sin(di-dj-tij)
                                #-------------------------------

                                J[filH][colH] = Hij
                                #-------------------------------
                                if tipo!='PV':

                                    J[filN][colN] = Nij
                                    J[filM][colM] = Mij
                                    J[filL][colL] = Lij

                                #-------------------------------


            f.writelines('J' + '\n')
            #exporto los arrays
            for elemento in J:
                try:
                    f.writelines(str(elemento).strip('[]') + '\n')
                except:
                    pass

            J_1 = np.linalg.pinv(J)
            #producto = np.dot(matriz_a, matriz_b)

            f.writelines('J-1' + '\n')
            #exporto los arrays
            for elemento in J_1:
                try:
                    f.writelines(str(elemento).strip('[]') + '\n')
                except:
                    pass

            if error <= error_maximo:
                #f.writelines('\n')

                f.close()
                return 'Calculado. Iteración ' + str(j) + '. Error ' + str(error)

            #f.writelines('Resultado iteración ' + str(j) + '\n')
            #f.writelines('-----------------------' + '\n')
            #for n in range(1, len(Bus)):
            #    elemento = Bus[n]
            #    if elemento[0]!='0':
            #        f.writelines(str(elemento).strip('[]') + '\n')
            #f.writelines('' + '\n')

            #f.writelines('Error ' + str(error))
            #f.writelines('' + '\n')

    except Exception as e:

        #numero_de_linea = e.__traceback__.tb_lineno
        traceback_info = traceback.format_exc()

        QMessageBox.information(None, 'EnerGis 6', 'Se produjo una excepción: ' + str(e) + ' ' + traceback_info + '\n' + ' j=' + str(j) + ' k=' + str(k) + ' n=' + str(n))

    f.close()

    return 'El flujo no converge'
    #except:
    #    return 'Calcular - Error'






















































































































































































def gauss_seidel(self):

    #from decimal import Decimal

    monodos=[]
    f = open('c:/gis/energis6/moNodos.txt','r')
    for elemento in f:
        monodos.append(elemento)
    f.close()

    Yii=[]
    f = open('c:/gis/energis6/Yii.txt','r')
    for elemento in f:
        lista = elemento.strip('\n').split(', ')
        Yii.append(lista)
    f.close()

    Yij=[]
    f = open('c:/gis/energis6/Yij.txt','r')
    for elemento in f:
        lista = elemento.strip('\n').split(', ')
        Yij.append(lista)
    f.close()

    Bus=[]
    f = open('c:/gis/energis6/Bus.txt','r')
    for elemento in f:
        lista = elemento.strip('\n').split(', ')
        Bus.append(lista)
    f.close()

    #try:
    #geoname,aux,tipo,V,delta,TAPmim,TAPmax,TAPpaso,tap,Pg,Qg,Qgmin,Qgmax,Pc,Qc

    j = 0
    k = 0
    n = 0

    f = open('c:/gis/energis6/gauss_seidel.txt','w')

    import traceback
    try:
        #f.writelines('Yii' + '\n')
        #exporto los arrays
        #for elemento in Yii:
        #    f.writelines(str(elemento).strip('[]') + '\n')

        #f.writelines('\n')
        #f.writelines('Orden' + '\n')
        #exporto los arrays
        #for elemento in monodos:
        #    f.writelines(str(elemento))

        f.writelines('\n')
        f.writelines('Flujo' + '\n')
        error_maximo = 0.00001
        for j in range(1, 200):
            #f.writelines('Iteracion ' + str(j) + '\n')
            #f.writelines('------------' + '\n')
            error = 0
            for k in range(1, len(monodos)):
                n = int(monodos[k])
                if n != 0:
                    #geoname = Bus[n][0]
                    #aux = Bus[n][1]
                    tipo = Bus[n][2]
                    V = float(Bus[n][3])
                    Vinicial = V

                    D = float(Bus[n][4])
                    TAPmin = float(Bus[n][5])
                    TAPmax = float(Bus[n][6])
                    TAPpaso = float(Bus[n][7])
                    TAP = float(Bus[n][8])
                    Pg = float(Bus[n][9])
                    Qg = float(Bus[n][10])
                    Qgmin = float(Bus[n][11])
                    Qgmax = float(Bus[n][12])
                    Pc = float(Bus[n][13])
                    Qc = float(Bus[n][14])
                    #--------------------------------------
                    yii = complex(float(Yii[n][35]), float(Yii[n][36]))
                    vi = cmath.rect(V, math.radians(D))

                    ci = complex(-Pc, -Qc)
                    pi = complex(Pg, Qg)

                    #--------------------------------------
                    #Armo la suma de los Yij de todas las lineas vinculadas + Vj
                    sumyv = complex(0, 0)

                    cant_lineas=int(Yii[n][2])

                    for i in range(3, 3 + cant_lineas):
                        lij = int(Yii[n][i])
                        if int(Yij[lij][2])==n:
                            nj=int(Yij[lij][3])
                        else:
                            nj=int(Yij[lij][2])

                        #si el proximo nodo es un NA no le sumo Y*V
                        if int(Yii[nj][38])!=3:
                            vj = cmath.rect(float(Bus[nj][3]), math.radians(float(Bus[nj][4])))
                            yij = complex(float(Yij[lij][4]), float(Yij[lij][5]))
                            sumyv = sumyv + yij * vj

                    #--------------------------------------

                    #f.writelines('Bus:' + str(Bus[n][0]) + ' V = ' + str(vi) + ' ; C=' + str(ci) + ' ; P=' + str(pi) + ' ; Sum Yij.Vj=' + str(sumyv) + '\n')

                    if tipo=='SL':

                        si = vi.conjugate() * (vi * yii +    sumyv)

                        Bus[n][9] = si.real
                        Bus[n][10] = -si.imag

                    if tipo=='PV':

                        #Si tiene pg es generador
                        if Pg!=0:
                            Qg = -1 * (vi.conjugate() * sumyv).imag
                            pi = -1 * complex(Pg, -Qg)
                            if Qg < Qgmin:
                                Qg = Qgmin
                                #En estos casos se fija Q y el nodo pasa a ser PQ -> Se calcula el voltaje
                                #Bus[n][2] = 'PQ'
                                V = ((-pi.conjugate())/vi.conjugate() - sumyv) / yii
                                D = math.degrees(cmath.phase(V))
                                Bus[n][3] = abs(V)
                                Bus[n][4] = D
                                Bus[n][10] = Qg
                            elif Qg > Qgmax:
                                Qg = Qgmax
                                #En estos casos se fija Q y el nodo pasa a ser PQ -> Se calcula el voltaje
                                #Bus[n][2] = 'PQ'
                                V = ((-pi.conjugate())/vi.conjugate() - sumyv) / yii
                                D = math.degrees(cmath.phase(V))
                                Bus[n][3] = abs(V)
                                Bus[n][4] = D
                                Bus[n][10] = Qg
                            else:
                                vn = ((-pi.conjugate())/vi.conjugate() - sumyv) / yii
                                D = math.degrees(cmath.phase(vn))
                                #Bus[n][3] queda el valor del generador, por estar dentro de los limites
                                V = cmath.rect(float(Bus[n][3]), math.radians(D))
                                Bus[n][4] = D
                                Bus[n][10] = Qg

                        #Si tiene tapmin y tapmax es regulacion

                    if tipo=='TP':

                        V = -sumyv/yii
                        D = math.degrees(cmath.phase(V))
                        Bus[n][3] = abs(V)
                        Bus[n][4] = D

                    if tipo=='TR':

                        V = -sumyv/yii
                        D = math.degrees(cmath.phase(V))
                        Bus[n][3] = abs(V)
                        Bus[n][4] = D
                        #for t in range(TAPmim, TAPmax, TAPpaso):
                        #    if abs(v1) < 1 - t:
                        #       Bus[n][8] = TAP
                        #    if abs(v1) > 1 + t:
                        #       Bus[n][8] = TAP

                    if tipo=='NS' or tipo=='NC':

                        V = -sumyv/yii
                        D = math.degrees(cmath.phase(V))
                        Bus[n][3] = abs(V)
                        Bus[n][4] = D

                    if tipo=='PQ':

                        V = ((ci.conjugate()-pi.conjugate())/vi.conjugate()-sumyv)/yii
                        D = math.degrees(cmath.phase(V))
                        Bus[n][3] = abs(V)
                        Bus[n][4] = D

                    #f.writelines(tipo + '(' + str(Bus[n][0]) + ') ; V=' + str(abs(V)) + ' ' + str(V) + '\n')

                    diferencia = float(Vinicial) - float(abs(V))
                    if abs(diferencia) > error:
                        error = abs(diferencia)

                    #f.writelines('\n')

            if error <= error_maximo and j > 10:
                for k in range(1, len(monodos)):
                    n = int(monodos[k])
                    if n != 0:
                        V = float(Bus[n][3])
                        D = float(Bus[n][4])
                        #f.writelines('Bus:' + str(Bus[n][0]) + ' ; V=' + str(abs(V)) + ' ' + str(V) + '\n')
                #f.writelines('\n')

                #calculo corrientes (comentado mas arriba)

                for k in range(1, len(Yij)):

                    ni=int(Yij[k][2])
                    nj=int(Yij[k][3])

                    yij = complex(float(Yij[k][4]), float(Yij[k][5]))

                    vi = cmath.rect(float(Bus[ni][3]), float(Bus[ni][4]))
                    vj = cmath.rect(float(Bus[nj][3]), float(Bus[nj][4]))

                    iij = (vj - vi) * yij
                    iji = - iij

                    Yij[k][9] = abs(iij)
                    Yij[k][10] = math.degrees(cmath.phase(iij))

                    #potencia en la linea ij en el extremo del nodo i
                    sij = vi * iij.conjugate()
                    #potencia en la linea ij en el extremo del nodo j
                    sji = vj * iji.conjugate()

                    #para etiquetar las potencias de cada tramo, se deben tomar las positivas (sij <> -sji) y a su vez eso determina la dirección del flujo
                    ppij = sij + sji

                    if sij.real>0:
                        Yij[k][11] = abs(sij.real)
                        Yij[k][12] = abs(sij.imag)
                        #origen del sentido del flujo
                        Yij[k][13] = ni
                    else:
                        Yij[k][11] = abs(sji.real)
                        Yij[k][12] = abs(sji.imag)
                        #origen del sentido del flujo
                        Yij[k][13] = nj

                    Yij[k][14] = abs(ppij.real)
                    Yij[k][15] = abs(ppij.imag)

                    #si sumo las perdidas en todas las lineas de las fuentes + las cargas, tengo lo que inyectó el SLACKS

                #--------------------------------------

                f.writelines('error <= error_maximo' + '\n')
                f.writelines('' + '\n')
                f.writelines('Resultado' + '\n')
                f.writelines('---------' + '\n')

                for k in range(1, len(monodos)):
                    n = int(monodos[k])
                    elemento = Bus[n]
                    if elemento[0]!='0':
                        f.writelines(str(elemento).strip('[]')   + '\n')
                f.writelines('' + '\n')

                f.writelines('Error ' + str(error) + '\n')

                #f.writelines('Yij' + '\n')
                #exporto los arrays
                #for elemento in Yij:
                #    f.writelines(str(elemento).strip('[]') + '\n')

                f.close()
                return 'Calculado. Iteración ' + str(j) + '. Error ' + str(error)

            f.writelines('Resultado iteración ' + str(j) + '\n')
            f.writelines('-----------------------' + '\n')
            for k in range(1, len(monodos)):
                n = int(monodos[k])
                elemento = Bus[n]
                if elemento[0]!='0':
                    f.writelines(str(elemento).strip('[]') + '\n')
            f.writelines('' + '\n')

            f.writelines('Error ' + str(error))
            f.writelines('' + '\n')

    except Exception as e:

        #numero_de_linea = e.__traceback__.tb_lineno
        traceback_info = traceback.format_exc()

        QMessageBox.information(None, 'EnerGis 6', 'Se produjo una excepción: ' + str(e) + ' ' + traceback_info + '\n' + ' j=' + str(j) + ' k=' + str(k) + ' n=' + str(n))

    f.close()

    return 'El flujo no converge'
    #except:
    #    return 'Calcular - Error'
