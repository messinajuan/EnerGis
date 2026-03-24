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

import pyodbc
from PyQt6.QtWidgets import QMessageBox, QApplication, QProgressDialog, QInputDialog

def __init__(self):
    pass

def importar_access(self, conn, database_path):

    #----------------------------------------------------------------------------
    progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    QApplication.processEvents()
    #----------------------------------------------------------------------------

    cnn = self.conn
    cursor = cnn.cursor()
    cursor.execute("DELETE FROM Lineas")
    cursor.execute("DELETE FROM Elementos_Lineas")
    cursor.execute("DELETE FROM Suministros")
    cursor.execute("DELETE FROM Medidores")
    cursor.execute("DELETE FROM Usuarios")
    cursor.execute("DELETE FROM Tarifas")
    cursor.execute("DELETE FROM Transformadores_Parametros")
    cursor.execute("DELETE FROM Transformadores")
    cursor.execute("DELETE FROM Ct")
    cursor.execute("DELETE FROM Nodos")
    cursor.execute("DELETE FROM Elementos_Postes")
    cursor.execute("DELETE FROM Estructuras")
    cursor.execute("DELETE FROM Postes")
    cursor.execute("DELETE FROM Niveles_Tension")
    cursor.execute("TRUNCATE TABLE Logs")
    cursor.execute("TRUNCATE TABLE Lineas_Borradas")
    cursor.execute("TRUNCATE TABLE Nodos_Borrados")
    self.conn.commit()
    srid = "22195"
    items = ["22184", "22185", "22186", "22194", "22195", "22196"]
    item, ok = QInputDialog.getItem(None, "Selecciona un SRID", "Opciones:", items, 0, False)
    if ok and item:
        srid = str(item)
    else:
        return
    iid = 0
    # Cadena de conexión para Access (.accdb)
    str_conexion_access = ('DRIVER={Microsoft Access Driver (*.mdb, *.accdb)}; DBQ=' + database_path)
    cnn_access = pyodbc.connect(str_conexion_access)
    # importacion de niveles de tension
    cursor = cnn_access.cursor()
    cursor.execute("SELECT tension FROM Niveles_Tension")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        try:
            cursor.execute("INSERT INTO Niveles_Tension (Tension) VALUES (" + str(rs[i][0]) + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pueden insertar el Nivel de Tensión ' + str(rs[i][0]) + ' en la Base de Datos')
    #----------------------------------------------------------------------------
    progress.setValue(5)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de nodos
    cursor = cnn_access.cursor()
    cursor.execute("SELECT geoname,nombre,descripcion,elmt,xcoord,ycoord,estilo,val1,val2,val3,val4,val5, nivel,tension,zona,alimentador,aux,modificacion,subzona,estado,localidad,uucc FROM Nodos")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", " #geoname
        if rs[i][0]>iid:
            iid=rs[i][0]
        if rs[i][1]==None:
            str_valores = str_valores + "'', " #nombre
        else:
            str_valores = str_valores + "'" + rs[i][1] + "', " #nombre
        if rs[i][2]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][2].replace("'","") + "', "
        str_valores = str_valores + str(rs[i][3]) + ", " #elmt
        str_valores = str_valores + str(rs[i][4]) + ", " #x
        str_valores = str_valores + str(rs[i][5]) + ", " #y
        if rs[i][6]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][6] + "', "
        if rs[i][7]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][7] + "', "
        if rs[i][8]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][8] + "', "
        if rs[i][9]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][9] + "', "
        if rs[i][10]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][10] + "', "
        if rs[i][11]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][11] + "', "
        if rs[i][12]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + str(rs[i][12]) + ", "
        str_valores = str_valores + str(rs[i][13]) + ", " #tension
        if rs[i][14]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][14] + "', "
        if rs[i][15]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][15] + "', "
        str_valores = str_valores + str(rs[i][16]) + ", " #aux
        str_valores = str_valores + rs[i][17].strftime("'%Y-%m-%d %H:%M:%S'").replace('-','') + ", " #fecha
        str_valores = str_valores + "'" + str(rs[i][18]) + "', "
        str_valores = str_valores + str(rs[i][19]) + ", " #estado
        str_valores = str_valores + str(rs[i][20]) + ", "
        str_valores = str_valores + "'" + str(rs[i][21]) + "', "
        str_valores = str_valores + "geometry::Point(" + str(rs[i][4]) + ',' + str(rs[i][5]) + ',' + srid + ")"
        #----------------------------------------------------------------------------
        progress.setValue(5 + int(10*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        try:
            cursor.execute("INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pueden insertar Nodos en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Nodos (Geoname, Nombre, Descripcion, Elmt, XCoord, YCoord, Estilo, Val1, Val2, Val3, Val4, Val5, Nivel, Tension, Zona, Alimentador, Aux, Modificacion, Subzona, Estado, Localidad, UUCC, obj) VALUES (" + str_valores + ")")
            return
    #----------------------------------------------------------------------------
    progress.setValue(15)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de elementos_lineas
    cursor = cnn_access.cursor()
    cursor.execute("SELECT id,descripcion,estilo,val1,val2,val3,val4,val5,val6,val7,val8,val9,val10,val11,val12,val13,val14,val15,val16,val17,val18,uso FROM Elementos_Lineas")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", " #geoname
        str_valores = str_valores + "'" + rs[i][1] + "', "
        str_valores = str_valores + "'" + rs[i][2] + "', "
        str_valores = str_valores + "'" + rs[i][3] + "', " #val1
        str_valores = str_valores + "'" + rs[i][4] + "', "
        if rs[i][5]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][5] + "', "
        if rs[i][6]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][6] + "', "
        if rs[i][7]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][7] + "', "
        if rs[i][8]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][8] + "', " #val6
        if rs[i][9]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][9] + "', "
        if rs[i][10]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][10] + "', "
        if rs[i][11]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][11] + "', "
        if rs[i][12]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][12] + "', "
        if rs[i][13]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][13] + "', " #val11
        if rs[i][14]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][14] + "', "
        if rs[i][15]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][15] + "', "
        if rs[i][16]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][16] + "', "
        if rs[i][17]==None:
            str_valores = str_valores + "'N', "
        else:
            str_valores = str_valores + "'" + rs[i][17] + "', "
        if rs[i][18]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][18] + "', " #val16
        if rs[i][19]==None:
            str_valores = str_valores + "'N', "
        else:
            str_valores = str_valores + "'" + rs[i][19] + "', "
        if rs[i][20]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + "'" + rs[i][20] + "', "
        if rs[i][21]==None:
            str_valores = str_valores + "1"
        else:
            str_valores = str_valores + str(rs[i][21])
        try:
            cursor.execute("INSERT INTO Elementos_Lineas (id,descripcion,estilo,val1,val2,val3,val4,val5,val6,val7,val8,val9,val10,val11,val12,val13,val14,val15,val16,val17,val18,uso) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Elementos de Lineas en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Elementos_Lineas (id,descripcion,estilo,val1,val2,val3,val4,val5,val6,val7,val8,val9,val10,val11,val12,val13,val14,val15,val16,val17,val18,uso) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(15 + int(5*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(20)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de lineas
    cursor = cnn_access.cursor()
    cursor.execute("SELECT Geoname,Fase,Elmt,Desde,Hasta,Quiebres,Longitud,Estilo,Tension,Zona,Alimentador,Aux,Modificacion,Exp,Disposicion,Conservacion,Ternas,UUCC,Acometida FROM Lineas")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", " #geoname
        if rs[i][0]>iid:
            iid=rs[i][0]
        str_valores = str_valores + "'" + rs[i][1] + "', "
        str_valores = str_valores + str(rs[i][2]) + ", "
        str_valores = str_valores + str(rs[i][3]) + ", "
        str_valores = str_valores + str(rs[i][4]) + ", "
        if rs[i][5]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][5] + "', "
        str_valores = str_valores + str(rs[i][6]) + ", "
        str_valores = str_valores + "'" + rs[i][7] + "', " #estilo
        str_valores = str_valores + str(rs[i][8]) + ", "
        str_valores = str_valores + "'" + rs[i][9] + "', "
        str_valores = str_valores + "'" + rs[i][10] + "', " #alimentador
        str_valores = str_valores + str(rs[i][11]) + ", "
        str_valores = str_valores + rs[i][12].strftime("'%Y-%m-%d %H:%M:%S'").replace('-','') + ", "
        if rs[i][13]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][13] + "', "
        if rs[i][14]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][14] + "', "
        if rs[i][15]==None:
            str_valores = str_valores + "'N', "
        else:
            str_valores = str_valores + "'" + rs[i][15] + "', "
        if rs[i][16]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][16] + "', "
        if rs[i][17]==None:
            str_valores = str_valores + "'N', "
        else:
            str_valores = str_valores + "'" + rs[i][17] + "', "
        if rs[i][18]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores  + str(rs[i][18])
        try:
            cursor.execute("INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, UUCC, Acometida) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieronm insertar Líneas en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Lineas (Geoname, Fase, Elmt, Desde, Hasta, Quiebres, Longitud, Estilo, Tension, Zona, Alimentador, Aux, Modificacion, Exp, Disposicion, Conservacion, Ternas, UUCC, Acometida) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(20 + int(10*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(30)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    cursor.execute("EXEC V4aV5")
    cnn.commit()
    #----------------------------------------------------------------------------
    progress.setValue(35)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de elementos_postes
    cursor = cnn_access.cursor()
    cursor.execute("SELECT id,descripcion,estilo,Value1,Value2,Value3,Value4,Value5,Value6,Value7,Value8,Value9,Value10 FROM Elementos_Postes")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", "
        str_valores = str_valores + "'" + rs[i][1] + "', "
        str_valores = str_valores + "'" + rs[i][2] + "', "
        if rs[i][3]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][3] + "', " #val1
        if rs[i][4]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][4] + "', "
        if rs[i][5]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][5] + "', "
        if rs[i][6]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][6] + "', "
        if rs[i][7]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][7] + "', "
        if rs[i][8]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][8] + "', " #val6
        if rs[i][9]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][9] + "', "
        if rs[i][10]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][10] + "', "
        if rs[i][11]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][11] + "', "
        if rs[i][12]==None:
            str_valores = str_valores + "''"
        else:
            str_valores = str_valores + "'" + rs[i][12] + "'"
        try:
            cursor.execute("INSERT INTO Elementos_Postes (id,descripcion,estilo,Value1,Value2,Value3,Value4,Value5,Value6,Value7,Value8,Value9,Value10) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Elementos de Postes en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Elementos_Postes (id,descripcion,estilo,Value1,Value2,Value3,Value4,Value5,Value6,Value7,Value8,Value9,Value10) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(35 + int(5*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    # importacion de estructureas
    cursor = cnn_access.cursor()
    cursor.execute("SELECT id,descripcion,estilo FROM Estructuras")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", "
        str_valores = str_valores + "'" + rs[i][1] + "', "
        str_valores = str_valores + "'" + rs[i][2] + "'"
        try:
            cursor.execute("INSERT INTO Estructuras (id,descripcion,estilo) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Estructuras de Postes en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Estructuras (id,descripcion,estilo) VALUES (" + str_valores + ")")
            return
    #----------------------------------------------------------------------------
    progress.setValue(40)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de postes
    cursor = cnn_access.cursor()
    cursor.execute("SELECT Geoname,Id_Nodo,XCoord,YCoord,Elmt,Estilo,Estructura,Rienda,Altura,Nivel,Zona,Tension,Tipo,Aislacion,Fundacion,Comparte,Ternas,Modificacion,Pat,Descargadores FROM Postes")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", " #geoname
        if rs[i][0]>iid:
            iid=rs[i][0]
        str_valores = str_valores + str(rs[i][1]) + ", "
        str_valores = str_valores + str(rs[i][2]) + ", "
        str_valores = str_valores + str(rs[i][3]) + ", "
        str_valores = str_valores + str(rs[i][4]) + ", "
        str_valores = str_valores + "'" + rs[i][5].replace("'","") + "', "
        str_valores = str_valores + str(rs[i][6]) + ", "
        str_valores = str_valores + str(rs[i][7]) + ", "
        str_valores = str_valores + str(rs[i][8]) + ", "
        str_valores = str_valores + str(rs[i][9]) + ", "
        str_valores = str_valores + "'" + rs[i][10].replace("'","") + "', "
        str_valores = str_valores + str(rs[i][11]) + ", "
        str_valores = str_valores + "'" + rs[i][12].replace("'","") + "', "
        str_valores = str_valores + "'" + rs[i][13].replace("'","") + "', "
        str_valores = str_valores + str(rs[i][14]) + ", "
        str_valores = str_valores + "'" + rs[i][15].replace("'","") + "', "
        str_valores = str_valores + "'" + rs[i][16].replace("'","") + "', "
        str_valores = str_valores + rs[i][17].strftime("'%Y-%m-%d %H:%M:%S'").replace('-','') + ", "
        str_valores = str_valores + str(rs[i][18]) + ", "
        str_valores = str_valores + str(rs[i][19]) + ", "
        str_valores = str_valores + "geometry::Point(" + str(rs[i][2]) + ',' + str(rs[i][3]) + ',' + srid + ")"
        try:
            cursor.execute("INSERT INTO Postes (Geoname,id_nodo,XCoord,YCoord,elmt,estilo,estructura,rienda,altura,nivel,zona,tension,tipo,aislacion,fundacion,comparte,ternas,modificacion,pat,descargadores,obj) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Postes en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Postes (Geoname,id_nodo,XCoord,YCoord,elmt,estilo,estructura,rienda,altura,nivel,zona,tension,tipo,aislacion,fundacion,comparte,ternas,modificacion,pat,descargadores,obj) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(40 + int(10*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(50)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    cursor = cnn.cursor()
    cursor.execute("UPDATE iid SET iid=" + str(iid))
    self.conn.commit()
    #----------------------------------------------------------------------------
    progress.setValue(55)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de Cts
    cursor = cnn_access.cursor()
    cursor.execute("SELECT id_ct,ubicacion,mat_plataf,tipo_ct,obs,es,caeis,caeies,caees,caeees,casis,casies,cases,casees,exp,tipo_oceba,direccion,localidad,partido,fecha_alta,fecha_baja,conservacion,descargadores FROM Ct")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = "'" + rs[i][0].replace("'","") + "', "
        if rs[i][1]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][1].replace("'","") + "', "
        if rs[i][2]==None:
            str_valores = str_valores + "'Hormigón', "
        else:
            str_valores = str_valores + "'" + rs[i][2].replace("'","") + "', "
        if rs[i][3]==None:
            str_valores = str_valores + "'Monoposte', "
        else:
            str_valores = str_valores + "'" + rs[i][3].replace("'","") + "', "
        if rs[i][4]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][4].replace("'","") + "', "
        str_valores = str_valores + str(rs[i][5]) + ", "
        if rs[i][6]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][6]) + ", "
        if rs[i][7]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][7]) + ", "
        if rs[i][8]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][8]) + ", "
        if rs[i][9]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][9]) + ", "
        if rs[i][10]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][10]) + ", "
        if rs[i][11]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][11]) + ", "
        if rs[i][12]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][12]) + ", "
        if rs[i][13]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][13]) + ", "
        if rs[i][14]==None:
            str_valores = str_valores + "'1111/2001', "
        else:
            str_valores = str_valores + "'" + rs[i][14].replace("'","") + "', "
        if rs[i][15]==None:
            str_valores = str_valores + "'SAMsp', "
        else:
            str_valores = str_valores + "'" + rs[i][15].replace("'","") + "', "
        if rs[i][16]==None:
            str_valores = str_valores + "'<SD>', "
        else:
            str_valores = str_valores + "'" + rs[i][16].replace("'","") + "', "
        if rs[i][17]==None:
            str_valores = str_valores + "'<SD>', "
        else:
            str_valores = str_valores + "'" + rs[i][17].replace("'","") + "', "
        if rs[i][18]==None:
            str_valores = str_valores + "'<SD>', "
        else:
            str_valores = str_valores + "'" + rs[i][18].replace("'","") + "', "
        if rs[i][19]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + rs[i][19].strftime("'%Y-%m-%d %H:%M:%S'").replace('-','') + ", "
        if rs[i][20]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + rs[i][20].strftime("'%Y-%m-%d %H:%M:%S'").replace('-','') + ", "
        str_valores = str_valores + "'" + rs[i][21].replace("'","") + "', "
        if rs[i][22]==None:
            str_valores = str_valores + "NULL"
        else:
            str_valores = str_valores + str(rs[i][22]) + ""
        try:
            cursor.execute("INSERT INTO Ct (id_ct,ubicacion,mat_plataf,tipo_ct,obs,es,caeis,caeies,caees,caeees,casis,casies,cases,casees,exp,tipo_oceba,direccion,localidad,partido,fecha_alta,fecha_baja,conservacion,descargadores) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Cts en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Ct (id_ct,ubicacion,mat_plataf,tipo_ct,obs,es,caeis,caeies,caees,caeees,casis,casies,cases,casees,exp,tipo_oceba,direccion,localidad,partido,fecha_alta,fecha_baja,conservacion,descargadores) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(55 + int(5*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(60)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de Transformadores
    cursor = cnn_access.cursor()
    cursor.execute("SELECT Id_Trafo,Id_Ct,Potencia,Conexionado,Marca,N_chapa,Tension_1,Tension_2,Tipo,Anio_fabricacion,Obs,Kit,Cromatografia,Anomalia,Fecha_norm,Certificado,Obs_pcb,aceite,Prop_usuario,Aislacion,Peso FROM Transformadores")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", "  #Id_Trafo
        str_valores = str_valores + "'" + str(rs[i][1]) + "', "  #Id_Ct
        str_valores = str_valores + str(rs[i][2]) + ", " #Potencia
        str_valores = str_valores + "'" + rs[i][3] + "', " #Conexionado
        if rs[i][4]==None:
            str_valores = str_valores + "'<SD>', "
        else:
            str_valores = str_valores + "'" + rs[i][4].replace("'","") + "', " #Marca
        if rs[i][5]==None:
            str_valores = str_valores + "'<SD>', "
        else:
            str_valores = str_valores + "'" + rs[i][5] + "', " #N_chapa
        str_valores = str_valores + str(rs[i][6]) + ", " #Tension_1
        str_valores = str_valores + str(rs[i][7]) + ", " #Tension_2
        str_valores = str_valores + str(rs[i][8]) + ", " #Tipo
        if rs[i][9]==None or not rs[i][9].isnumeric():
            str_valores = str_valores + "1999, "
        else:
            str_valores = str_valores + str(rs[i][9]) + ", " #Anio_fabricacion
        if rs[i][10]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][10].replace("'","") + "', " #Obs
        if rs[i][11]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][11].replace("'","") + "', " #Kit
        if rs[i][12]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'"  + str(rs[i][12]) + "', " #Cromatografia
        if rs[i][13]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores  + "'" +  str(rs[i][13]) + "', " #Anomalia
        if rs[i][14]==None:
            str_valores = str_valores + "NULL, "
        else:
            str_valores = str_valores + rs[i][14].strftime("'%Y-%m-%d %H:%M:%S'").replace('-','') + ", " #Fecha_norm
        if rs[i][15]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + str(rs[i][15]).replace("'","") + "', " #Certificado
        if rs[i][16]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][16].replace("'","") + "', " #Obs_pcb
        if rs[i][17]==None:
            str_valores = str_valores + "0, "
        else:
            str_valores = str_valores + str(rs[i][17]) + ", " #aceite
        if rs[i][18]==None:
            str_valores = str_valores + "'0', "
        else:
            str_valores = str_valores + "'" + str(rs[i][18]) + "', " #Prop_usuario
        if rs[i][19]==None:
            str_valores = str_valores + "'Aceite', "
        else:
            str_valores = str_valores + str(rs[i][19]) + ", " #Aislacion
        if rs[i][20]==None:
            str_valores = str_valores + "'0'"
        else:
            str_valores = str_valores + str(rs[i][20]) #Peso
        try:
            cursor.execute("INSERT INTO Transformadores (Id_Trafo,Id_Ct,Potencia,Conexionado,Marca,N_chapa,Tension_1,Tension_2,Tipo,Anio_fabricacion,Obs,Kit,Cromatografia,Anomalia,Fecha_norm,Certificado,Obs_pcb,aceite,Prop_usuario,Aislacion,Peso) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Transformadores en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Transformadores (Id_Trafo,Id_Ct,Potencia,Conexionado,Marca,N_chapa,Tension_1,Tension_2,Tipo,Anio_fabricacion,Obs,Kit,Cromatografia,Anomalia,Fecha_norm,Certificado,Obs_pcb,aceite,Prop_usuario,Aislacion,Peso) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(60 + int(10*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(70)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de Tarifas
    cursor = cnn_access.cursor()
    cursor.execute("SELECT Tarifa,Descripcion,Nivel_Tension,id_oceba,tipo FROM Tarifas")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = "'" + rs[i][0] + "', "
        str_valores = str_valores + "'" + rs[i][1] + "', "
        str_valores = str_valores + "'" + rs[i][2] + "', "
        str_valores = str_valores + "'" + rs[i][3] + "', "
        if rs[i][4]==None:
            str_valores = str_valores + "''"
        else:
            str_valores = str_valores + "'" + rs[i][4] + "'"
        try:
            cursor.execute("INSERT INTO Tarifas (Tarifa,Descripcion,Nivel_Tension,id_oceba,tipo) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Tarifas en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Tarifas (Tarifa,Descripcion,Nivel_Tension,id_oceba,tipo) VALUES (" + str_valores + ")")
            return
    #----------------------------------------------------------------------------
    progress.setValue(80)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de  Usuarios
    cursor = cnn_access.cursor()
    cursor.execute("SELECT id_usuario,tipo,nombre,calle,altura,altura_ex,zona,id_suministro,tarifa,fase,ES,subzona,electrodependiente,fae,prosumidor FROM Usuarios")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = "'" + str(rs[i][0]) + "', "
        str_valores = str_valores + str(rs[i][1]) + ", "
        if rs[i][2]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][2].replace("'","") + "', " #nombre
        if rs[i][3]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][3].replace("'","") + "', " #calle
        if rs[i][4]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][4] + "', "
        if rs[i][5]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][5] + "', "
        if rs[i][6]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][6] + "', "
        if rs[i][7]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][7] + "', "
        if rs[i][8]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][8] + "', "
        if rs[i][9]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + str(rs[i][9]) + ", " #fase
        if rs[i][10]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + str(rs[i][10]) + ", " #es
        if rs[i][11]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][11] + "', "
        if rs[i][12]==None:
            str_valores = str_valores + "'N', "
        else:
            str_valores = str_valores + "'" + rs[i][12] + "', "
        if rs[i][13]==None:
            str_valores = str_valores + "'', "
        else:
            str_valores = str_valores + "'" + rs[i][13] + "', "
        if rs[i][14]==None:
            str_valores = str_valores + "''"
        else:
            str_valores = str_valores + "'" + rs[i][14] + "'"
        try:
            cursor.execute("INSERT INTO Usuarios (id_usuario,tipo,nombre,calle,altura,altura_ex,zona,id_suministro,tarifa,fase,ES,subzona,electrodependiente,fae,prosumidor) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Usuarios en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Usuarios (id_usuario,tipo,nombre,calle,altura,altura_ex,zona,id_suministro,tarifa,fase,ES,subzona,electrodependiente,fae,prosumidor) VALUES (" + str_valores + ")")
            return
        #----------------------------------------------------------------------------
        progress.setValue(80 + int(10*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(90)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de  Medidores
    cursor = cnn_access.cursor()
    cursor.execute("SELECT nro_medidor,id_usuario,marca,modelo,anio,relacion,fases,tipo FROM Medidores")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = "'" + rs[i][0] + "', "
        str_valores = str_valores + "'" + str(rs[i][1]) + "', "
        if rs[i][2]==None:
            str_valores = str_valores +  "'', "
        else:
            str_valores = str_valores +  "'" + rs[i][2] + "', "
        if rs[i][3]==None:
            str_valores = str_valores +  "'', "
        else:
            str_valores = str_valores + "'" + rs[i][3] + "', "
        if rs[i][4]==None:
            str_valores = str_valores +  "'', "
        else:
            str_valores = str_valores + "'" + rs[i][4] + "', "
        if rs[i][5]==None:
            str_valores = str_valores +  "'', "
        else:
            str_valores = str_valores + "'" + rs[i][5] + "', "
        if rs[i][6]==None:
            str_valores = str_valores +  "'', "
        else:
            str_valores = str_valores + "'" + rs[i][6] + "', "
        if rs[i][7]==None or rs[i][7]=='':
            str_valores = str_valores + "'Monotarifa'"
        else:
            str_valores = str_valores + "'" + rs[i][7] + "'"
        try:
            cursor.execute("INSERT INTO Medidores (nro_medidor,id_usuario,marca,modelo,anio,relacion,fases,tipo) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Medidores en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Medidores (nro_medidor,id_usuario,marca,modelo,anio,relacion,fases,tipo) VALUES (" + str_valores + ")")
            #return
        #----------------------------------------------------------------------------
        progress.setValue(90 + int(5*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(95)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    # importacion de  Suministros
    cursor = cnn_access.cursor()
    cursor.execute("SELECT id_nodo,id_suministro FROM Suministros WHERE id_nodo IN (SELECT geoname FROM Nodos)")
    rs = cursor.fetchall()
    cursor.close()
    cursor = cnn.cursor() #escribo en sql
    for i in range (0, len(rs)):
        str_valores = str(rs[i][0]) + ", "
        str_valores = str_valores + "'" + rs[i][1] + "'"
        try:
            cursor.execute("INSERT INTO Suministros (id_nodo,id_suministro) VALUES (" + str_valores + ")")
            cnn.commit()
        except:
            cnn.rollback()
            QMessageBox.critical(None, 'EnerGis 6', 'No se pudieron insertar Suministros en la Base de Datos')
            QMessageBox.critical(None, 'EnerGis 6', "INSERT INTO Suministros (id_nodo,id_suministro) VALUES (" + str_valores + ")")
            #return
        #----------------------------------------------------------------------------
        progress.setValue(95 + int(5*i/len(rs)))
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    progress.setValue(100)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    cnn_access.close()

    cnn = self.conn
    cursor = cnn.cursor()
    try:
        cursor.execute("crear_red")
        cnn.commit()
    except:
        cnn.rollback()
        QMessageBox.warning(None, 'EnerGis 6', "No se pudo crear la Red !")
    QMessageBox.information(None, 'EnerGis 6', 'Importado !')
