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
from .mod_coordenadas import convertir_coordenadas
from PyQt6.QtWidgets import QMessageBox, QApplication, QProgressDialog

#esta es la direccion del proyecto
basepath = os.path.dirname(os.path.realpath(__file__))

def __init__(self):
    pass

def exportar_usuarios(self, conn, srid):
    #actualizo suministros_ubicaciones
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE Suministros_Ubicaciones")
    conn.commit()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT Suministros.id_suministro, Nodos.XCoord, Nodos.YCoord FROM Usuarios INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro COLLATE SQL_Latin1_General_CP1_CI_AS = Suministros.id_suministro COLLATE SQL_Latin1_General_CP1_CI_AS WHERE Suministros.id_suministro COLLATE SQL_Latin1_General_CP1_CI_AS NOT IN (SELECT id_suministro COLLATE SQL_Latin1_General_CP1_CI_AS FROM Suministros_Ubicaciones)")
    #convierto el cursor en array
    suministros = tuple(cursor)
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Procesando Suministros ...", "Cancelar", 0, len(suministros))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    cursor.close()
    for i in range (0, len(suministros)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(i)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        coords = convertir_coordenadas(self, suministros[i][1], suministros[i][2], srid, 4326)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Suministros_Ubicaciones (id_suministro,Lat,Lon) VALUES ('" + str(suministros[i][0]) + "'," + str(coords[0]) + "," + str(coords[1]) + ")")
        conn.commit()        

    cursor = conn.cursor()
    cursor.execute("SELECT A.Sucursal, A.Id_Usuario, CASE WHEN NOT C.Fecha_Baja IS NULL THEN '0' ELSE ISNULL(B.Nro_Medidor, 0) END AS Nro_Medidor, C.Apellido, C.Nombre, C.DNI, C.CUIT, C.Direccion_Postal, C.Calle, C.Numero, C.Piso, C.Dto, C.Entre, C.Localidad, C.Partido, C.Codigo_Postal, C.Telefono, C.E_Mail, A.Tarifa_Oceba, C.Tarifa_Especial, C.Ruta, C.Tension, C.Potencia_Declarada, C.Nomenclatura_Catastral, A.Latitud, A.Longitud, CONVERT(VARCHAR, ISNULL(C.Fecha_Alta,'1980-01-01'), 103), CONVERT(VARCHAR, C.Fecha_Baja, 103) FROM ((SELECT '0' AS Sucursal, Usuarios.Id_Usuario, Tarifas.id_OCEBA AS Tarifa_Oceba, ISNULL (Suministros_Ubicaciones.Lat, 0) AS Latitud, ISNULL(Suministros_Ubicaciones.Lon, 0) AS Longitud FROM (Suministros_Ubicaciones RIGHT JOIN Usuarios ON Suministros_Ubicaciones.id_suministro = Usuarios.id_suministro) INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa) AS A LEFT JOIN (SELECT id_usuario,nro_medidor FROM Medidores) AS B ON A.Id_Usuario = B.id_usuario) LEFT JOIN (SELECT id_usuario, Nombre, Apellido, DNI, CUIT, Calle, Numero, Piso, Dto, Entre, Localidad, Codigo_Postal, Partido, Direccion_Postal, Telefono, E_Mail, Tarifa_Especial, Ruta, Tension_Suministro AS Tension, Potencia_Declarada, Nomenclatura_Catastral, Fecha_Alta, Fecha_Baja FROM VW_CCDATOSCOMERCIALES) AS C ON A.Id_Usuario = C.id_usuario WHERE NOT Tarifa_Especial IS NULL")
    #convierto el cursor en array
    usuarios = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Procesando Usuarios ...", "Cancelar", 0, len(usuarios))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    cursor = conn.cursor()
    cursor.execute("SELECT Codigo FROM Empresa")
    #convierto el cursor en array
    empresa = tuple(cursor)
    cursor.close()
    str_codigo_empresa = empresa[0][0]
    if os.path.isdir('c:/gis/energis6/OCEBA/')==False:
        os.mkdir('c:/gis/energis6/OCEBA/')
    f = open('c:/gis/energis6/OCEBA/usuarios_oceba.txt','w')
    f.writelines("Distribuidora;Sucursal;Id_Usuario;Nro_Medidor;Apellido;Nombre;DNI;CUIT;Direccion_Postal;Calle;Numero;Piso;Dto;Entre;Localidad;Partido;Codigo_Postal;Telefono;E_Mail;Tarifa_Oceba;Tarifa_Especial;Ruta;Tension;Potencia_Declarada;Nomenclatura_Catastral;Latitud;Longitud;Fecha_Alta;Fecha_Baja" + "\n")
    for i in range (0, len(usuarios)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(i)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_linea = str_codigo_empresa + ";"
        for j in range (0, len(usuarios[0])):
            if usuarios[i][j]==None:
                str_linea = str_linea + ";"
            else:
                if j==21 or j==22 or j==24 or j==25:
                    str_linea = str_linea + str(usuarios[i][j]).replace('.',',') + ";"
                else:
                    str_linea = str_linea + str(usuarios[i][j]).strip() + ";"
        f.writelines(str_linea[:-1] + "\n")
    f.close()
    # Forzar el cierre del QProgressDialog
    progress.close()
    QMessageBox.warning(None, 'EnerGis 6', "Exportado en C:/GIS/EnerGis6/OCEBA/usuarios_oceba.txt")

def exportar_cts(self, conn, srid):
    cursor = conn.cursor()
    cursor.execute("SELECT Codigo FROM Empresa")
    #convierto el cursor en array
    empresa = tuple(cursor)
    cursor.close()
    str_codigo_empresa = empresa[0][0]
    #actualizo cts_ubicaciones
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE Cts_Ubicaciones")
    conn.commit()
    cursor = conn.cursor()
    cursor.execute("SELECT Ct.id_ct, Nodos.XCoord, Nodos.YCoord FROM Ct INNER JOIN Nodos ON Ct.id_ct COLLATE SQL_Latin1_General_CP1_CI_AS = Nodos.Nombre COLLATE SQL_Latin1_General_CP1_CI_AS WHERE Nodos.elmt=4 AND Ct.id_ct COLLATE SQL_Latin1_General_CP1_CI_AS NOT IN (SELECT id_ct COLLATE SQL_Latin1_General_CP1_CI_AS FROM Cts_Ubicaciones)")
    #convierto el cursor en array
    cts = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Procesando...", "Cancelar", 0, len(cts))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    for i in range (0, len(cts)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(i)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        coords = convertir_coordenadas(self, cts[i][1], cts[i][2], srid, 4326)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Cts_Ubicaciones (id_ct,XCoord,YCoord) VALUES ('" + str(cts[i][0]) + "'," + str(coords[1]) + "," + str(coords[0]) + ")")
        conn.commit()
    cursor = conn.cursor()
    cursor.execute("SELECT '0' AS Sucursal, Ct.Id_ct AS Centro_Transformacion, ISNULL(Ct.Ubicacion,'<SD>') AS Direccion, Ct.Tipo_OCEBA AS Tipo, SUM(Transformadores.Potencia) AS Potencia, CAST(Transformadores.Tension_1 AS varchar) + '/' + CAST(Transformadores.Tension_2 AS varchar) AS Relacion, LEFT(Nodos.Zona, 1) AS UR, Ct.localidad, Ct.partido, Cts_Ubicaciones.YCoord AS Latitud, Cts_Ubicaciones.XCoord AS Longitud, CONVERT(VARCHAR, Ct.Fecha_Alta, 103), CONVERT(VARCHAR, Ct.Fecha_Baja, 103) FROM Cts_Ubicaciones INNER JOIN Nodos INNER JOIN Transformadores INNER JOIN Ct ON Transformadores.Id_ct COLLATE SQL_Latin1_General_CP1_CI_AS = Ct.Id_ct COLLATE SQL_Latin1_General_CP1_CI_AS ON Nodos.Nombre COLLATE SQL_Latin1_General_CP1_CI_AS = Ct.Id_ct COLLATE SQL_Latin1_General_CP1_CI_AS ON Cts_Ubicaciones.id_ct COLLATE SQL_Latin1_General_CP1_CI_AS = Ct.Id_ct COLLATE SQL_Latin1_General_CP1_CI_AS WHERE (Nodos.Elmt = 4) GROUP BY Ct.Id_ct, Ct.Ubicacion, Ct.Tipo_OCEBA, CAST(Transformadores.Tension_1 AS varchar) + '/' + CAST(Transformadores.Tension_2 AS varchar), LEFT(Nodos.Zona, 1), Ct.localidad, Ct.partido, Cts_Ubicaciones.YCoord,Cts_Ubicaciones.XCoord, CONVERT(VARCHAR, Ct.Fecha_Alta, 103), CONVERT(VARCHAR, Ct.Fecha_Baja, 103)")
    #convierto el cursor en array
    cts = tuple(cursor)
    cursor.close()
    if os.path.isdir('c:/gis/energis6/OCEBA/')==False:
        os.mkdir('c:/gis/energis6/OCEBA/')
    f = open('c:/gis/energis6/OCEBA/cts_oceba.txt','w')
    f.writelines("Distribuidora;Sucursal;Centro_Transformacion;Direccion;Tipo;Potencia;Relacion;UR;localidad;partido;Latitud;Longitud;Fecha_Alta;Fecha_Baja" + "\n")
    for i in range (0, len(cts)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(i)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_linea = str_codigo_empresa + ";"
        for j in range (0, len(cts[0])):
            if cts[i][j]==None:
                str_linea = str_linea + ";"
            else:
                if j==4 or j==9 or j==10:
                    str_linea = str_linea + str(cts[i][j]).replace('.',',') + ";"
                else:
                    str_linea = str_linea + str(cts[i][j]) + ";"
        f.writelines(str_linea[:-1] + "\n")
    f.close()
    # Forzar el cierre del QProgressDialog
    progress.close()
    QMessageBox.warning(None, 'EnerGis 6', "Exportado en C:/GIS/EnerGis6/OCEBA/cts_oceba.txt")

def exportar_cadena1(self, conn, tipo_navegacion):
    cursor = conn.cursor()
    cursor.execute("SELECT id_semestre,Fecha_Desde,Fecha_Hasta,numero FROM Semestre")
    #convierto el cursor en array
    semestre = tuple(cursor)
    cursor.close()
    str_semestre = str(semestre[0][3])
    cursor = conn.cursor()
    cursor.execute("SELECT Codigo FROM Empresa")
    #convierto el cursor en array
    empresa = tuple(cursor)
    cursor.close()
    str_codigo_empresa = empresa[0][0]
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    if tipo_navegacion==0:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        listanodos = [list(nodo) for nodo in self.mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        listalineas = [list(linea) for linea in self.mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)
        #----------------------------------------------------------------------------
        progress.setValue(30)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        from .mod_navegacion_ant import nodos_por_transformador
        nodos_por_transformador(self, conn)
        #----------------------------------------------------------------------------
        progress.setValue(70)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    else:
        import clr
        from System import Int64
        #----------------------------------------------------------------------------
        cursor = self.conn.cursor()
        cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
        fuentes = cursor.fetchall()
        cursor.close()
        #----------------------------------------------------------------------------
        # Cargar el ensamblado
        clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
        from EnerGis6.NavRed7 import NavRed
        # Instanciar la clase NavRed
        navred_instance = NavRed()
        for fuente in fuentes:
            #----------------------------------------------------------------------------
            progress.setValue(int(100/len(fuentes)))
            QApplication.processEvents()
            if progress.wasCanceled():
                return
            #----------------------------------------------------------------------------
            # Preparar los valores de entrada
            fuentenavegada = Int64(fuente[0])
            # Llamar a la función
            resultado = navred_instance.Navegar_compilar_red(self.monodos,self.amnodos,self.amlineas,fuentenavegada)
            if resultado[0]!="Ok":
                QMessageBox.critical(None, 'EnerGis 6', resultado[0])
                #----------------------------------------------------------------------------
                progress.setValue(100)
                #----------------------------------------------------------------------------
                return
        #----------------------------------------------------------------------------
        progress.setValue(100)
        #----------------------------------------------------------------------------
        self.red_verificada=True
        #trafos_nodos=['-1']*self.amnodos.GetLength(0)
        trafos_suministros=['-1']*self.amnodos.GetLength(0)
        for n in range(self.amnodos.GetLength(0)):
            if self.amnodos.GetValue(n,44)!=0:
                #trafos_nodos[self.amnodos.GetValue(n,44)]=trafos_nodos[self.amnodos.GetValue(n,44)] + ',' + str(self.amnodos.GetValue(n,1))
                if self.amnodos.GetValue(n,2)==6:
                    trafos_suministros[self.amnodos.GetValue(n,44)]=trafos_suministros[self.amnodos.GetValue(n,44)] + ',' + str(self.amnodos.GetValue(n,1))
        try:
            cursor = self.conn.cursor()
            cursor.execute("TRUNCATE TABLE Suministros_Trafos")
            #cursor.execute("TRUNCATE TABLE Nodos_Transformador")
            self.conn.commit()
        except:
            QMessageBox.critical(None, 'EnerGis 6', 'No se puede borrar la tabla Suministros_Trafos')
            self.conn.rollback()
        for n in range(len(trafos_suministros)):
            if trafos_suministros[n]!='-1':
                try:
                    cursor = self.conn.cursor()
                    cursor.execute("INSERT INTO Suministros_Trafos SELECT geoname, " + str(self.amnodos.GetValue(n,1)) + " FROM Nodos WHERE Tension>0 AND geoname IN (" + str(trafos_suministros[n]) + ")")
                    self.conn.commit()
                except:
                    QMessageBox.critical(None, 'EnerGis 6', 'No se puede insertar en la tabla Suministros_Trafos')
                    self.conn.rollback()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT '0' AS Sucursal, Usuarios.id_usuario AS Codigo_Suministro, Tarifas.id_OCEBA AS Tarifa, Cadena_Electrica.[Alimentador BT], Cadena_Electrica.[Centro MTBT], Cadena_Electrica.[Centro Distribucion], Cadena_Electrica.[Alimentador MT], Cadena_Electrica.SSEE, Usuarios.Fase, 0 AS Consumo, CONVERT(VARCHAR, GETDATE(), 103) AS Fecha FROM Usuarios INNER JOIN Cadena_Electrica ON Usuarios.id_usuario = Cadena_Electrica.id_usuario INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa WHERE Usuarios.ES=1")
    #convierto el cursor en array
    cadena = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress.setValue(50)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    if os.path.isdir('c:/gis/energis6/OCEBA/')==False:
        os.mkdir('c:/gis/energis6/OCEBA/')
    f = open('c:/gis/energis6/OCEBA/semestre_' + str_semestre + '_cadena_1.txt','w')
    f.writelines('Semestre;Distribuidora;Sucursal;Codigo_Suministro;Tarifa;Alimentador BT;Centro MTBT;Centro Distribucion;Alimentador MT;SSEE;fase;Consumo;Fecha' + '\n')
    for i in range (0, len(cadena)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(50 + int(i/2))
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_linea = str_semestre + ";" + str_codigo_empresa + ";"
        for j in range (0, len(cadena[0])):
            if cadena[i][j]==None:
                str_linea = str_linea + ";"
            else:
                str_linea = str_linea + str(cadena[i][j]) + ";"
        f.writelines(str_linea[:-1] + "\n")
    f.close()
    # Forzar el cierre del QProgressDialog
    progress.close()
    QMessageBox.warning(None, 'EnerGis 6', "Exportado en C:/GIS/EnerGis6/OCEBA/semestre_" + str_semestre + "_cadena_1.txt")

def exportar_cadena2(self, conn, tipo_navegacion):
    if tipo_navegacion==0:
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mNodos ORDER BY Aux")
        #convierto el cursor en array
        self.mnodos = tuple(cursor)
        cursor.close()
        listanodos = [list(nodo) for nodo in self.mnodos]
        jnodos = json.dumps(listanodos)
        with open(os.path.join(tempfile.gettempdir(), "jnodos"), "w") as a:
            a.write(jnodos)
        #----------------------------------------------------------------------------
        progress.setValue(25)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mLineas ORDER BY Aux")
        #convierto el cursor en array
        self.mlineas = tuple(cursor)
        cursor.close()
        listalineas = [list(linea) for linea in self.mlineas]
        jlineas = json.dumps(listalineas)
        with open(os.path.join(tempfile.gettempdir(), "jlineas"), "w") as a:
            a.write(jlineas)
        #----------------------------------------------------------------------------
        progress.setValue(50)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        from .mod_navegacion_ant import nodos_por_transformador
        nodos_por_transformador(self, conn)
        #----------------------------------------------------------------------------
        progress.setValue(100)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
    from .frm_elegir_semestre import frmElegirSemestre
    self.dialogo = frmElegirSemestre(conn)
    self.dialogo.show()

def exportar_811(self, conn, srid):
    cursor = conn.cursor()
    cursor.execute("SELECT Empresa, Codigo, Lon, Lat FROM Empresa")
    #convierto el cursor en array
    empresa = tuple(cursor)
    cursor.close()
    str_nombre_empresa = empresa[0][0]
    str_codigo_empresa = empresa[0][1]
    str_lon = str(empresa[0][2]).replace('.',',')
    str_lat = str(empresa[0][3]).replace('.',',')
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 1 Partido FROM Ciudades ORDER BY Ciudad")
    #convierto el cursor en array
    partido = tuple(cursor)
    cursor.close()
    str_partido = partido[0][0]
    if os.path.isdir('c:/gis/energis6/OCEBA/')==False:
        os.mkdir('c:/gis/energis6/OCEBA/')
    f = open('c:/gis/energis6/OCEBA/res811.txt','w')
    f.writelines("Organismo de Control de la Energia de la Pcia de Buenos Aires" + "\n")
    f.writelines("							RESOLUCION 811/02" + "\n")
    f.writelines("INFORME DE REVISION CUATRIMESTRAL DE TRANSFORMADORES" + "\n")
    f.writelines("" + "\n")
    f.writelines("DISTRIBUIDORA:	" + str_nombre_empresa + "\n")
    f.writelines("CODIGO:	" + chr(9) + str_codigo_empresa + "\n")
    f.writelines("LOCALIDAD:	" + chr(9) + str_partido + "\n")
    f.writelines("" + "\n")
    f.writelines("Nota: Guiarse por el instructivo. (*) Son los campos obligatorios" + "\n")
    f.writelines("" + "\n")
    f.writelines("Codigo: Distribuidora Provincial:  Codigo de Sucursal, Distribuidora Municipal: Codigo de Cooperativa							Kit:  (+) Positivo o (-) Negativo" + "\n")
    f.writelines("Area: (U)rbano, (R)ural, (D)ep¢sito, (S)ub-urbana.							Certificado de Fabricacion (SI) o (NO)" + "\n")
    f.writelines("TipoSE: (M)onoposte, (P)lataforma, (S)ubterranea, (AN) Anivel" + "\n")
    f.writelines("Cod. Anomalia:  (OCD) Obra Civil Defectuosa, (EO) Emanacion de Olores,(PA) Perdida Aceite,(CA) Contaminacion Auditiva,(SA) Sin Anomalia, (CV)  Contaminacion Visual" + "\n")
    f.writelines("" + "\n")
    f.writelines("%Area (*)	Ubicacion	TipoSE	Pot. (*)	KV (*)	Marca (*)	A¤o	N§ Serie (*)	Kit	Cromatografia	Certificado (*)	Cod. Anomalia (*)	Fecha de Normaliz.	Observ.	Volumen	Lat.Sur	Long.Oeste	Codigo(*)" + "\n")
    cursor = conn.cursor()
    cursor.execute("SELECT ISNULL(LEFT(Nodos.Zona,1),'R') AS Zona, Transformadores.id_trafo, Transformadores.id_ct, Ct.Ubicacion, Ct.Tipo_ct, ISNULL(Transformadores.Potencia, 5) AS Potencia, ISNULL(Transformadores.Tension_1/1000, '13.2') AS Tension, ISNULL(Transformadores.Marca, 'SD') AS Marca, ISNULL(Transformadores.Anio_fabricacion, '1900') AS Anio, ISNULL(Transformadores.N_chapa, 'S/N') AS Chapa, Transformadores.Kit, ISNULL(Transformadores.Cromatografia, '0.1') AS Cromatogafia, Transformadores.Certificado, Transformadores.Anomalia, CONVERT(VARCHAR, ISNULL(Transformadores.Fecha_norm, '1900-01-01'), 103), Transformadores.Obs_pcb, Transformadores.Aceite, Nodos.XCoord, Nodos.YCoord FROM Nodos INNER JOIN (Ct INNER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct) ON Nodos.Nombre = Ct.Id_ct WHERE Nodos.Elmt=4 ORDER BY zona, id_trafo")
    #convierto el cursor en array
    transformadores_red = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Transformadores en la Red...", "Cancelar", 0, len(transformadores_red))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    for i in range (0, len(transformadores_red)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(i)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_zona = transformadores_red[i][0].upper()
        str_ubicacion = transformadores_red[i][1]
        if transformadores_red[i][2] != None:
            str_ubicacion = transformadores_red[i][2]
        if transformadores_red[i][3] != None:
            str_ubicacion = transformadores_red[i][3]
        str_tipo_se = "P"
        if transformadores_red[i][4] == "Monoposte":
            str_tipo_se = "M"
        if transformadores_red[i][4] == "Biposte":
            str_tipo_se = "P"
        if transformadores_red[i][4] == "Plataforma":
            str_tipo_se = "P"
        if transformadores_red[i][4] == "A Nivel":
            str_tipo_se = "AN"
        if transformadores_red[i][4] == "Cámara":
            str_tipo_se = "AN"
        if transformadores_red[i][4] == "Cámara Nivel":
            str_tipo_se = "AN"
        if transformadores_red[i][4] == "Cámara Subterránea":
            str_tipo_se = "S"
        if transformadores_red[i][4] == "Centro Compacto":
            str_tipo_se = "AN"
        if transformadores_red[i][4] == "Cámara Elevada":
            str_tipo_se = "P"
        str_potencia = str(transformadores_red[i][5]).replace('.',',')
        str_tension = str(round(transformadores_red[i][6],1)).replace('.',',')
        str_marca = str(transformadores_red[i][7])
        str_anio = str(transformadores_red[i][8])
        if transformadores_red[i][9]=="0":
            str_chapa="S/N"
        else:
            str_chapa = transformadores_red[i][9]
        str_kit = "-"
        if transformadores_red[i][10]=="+":
            str_kit = "+"
        if transformadores_red[i][10]!=None:
            j = transformadores_red[i][10].find('+')
            if j>0:
                str_kit = "+"
            j = transformadores_red[i][10].find('osit')
            if j>0:
                str_kit = "+"
            if transformadores_red[i][10].strip()=="":
                str_kit = "-"
        str_cromatografia = "0.1"
        if str(transformadores_red[i][11]) != "0":
            str_cromatografia = transformadores_red[i][11].replace(',','.')
        str_certificado = "SI"
        if str(transformadores_red[i][12]) == "0":
            str_certificado = "NO"
        str_anomalia = "SA"
        if transformadores_red[i][13] != None:
            j = transformadores_red[i][13].upper().find('RDIDA')
            if j>0:
                str_anomalia = "PA"
            j = transformadores_red[i][13].upper().find('OLOR')
            if j>0:
                str_anomalia = "EO"
            j = transformadores_red[i][13].upper().find('VISU')
            if j>0:
                str_anomalia = "CV"
            j = transformadores_red[i][13].upper().find('AUD')
            if j>0:
                str_anomalia = "CA"
            if str(transformadores_red[i][13]) == 'Pérdida de Aceite':
                str_anomalia = "PA"
            if str(transformadores_red[i][13]) == 'Emanación de Olores':
                str_anomalia = "EO"
            if str(transformadores_red[i][13]) == 'Contaminación Visual':
                str_anomalia = "CV"
            if str(transformadores_red[i][13]) == 'Contaminación Auditiva':
                str_anomalia = "CA"
            if str(transformadores_red[i][13]) == 'Obra Civil Defectuosa':
                str_anomalia = "OCD"
        if transformadores_red[i][14] != None:
            str_fecha_normalizacion = str(transformadores_red[i][14])
        str_observaciones = ""
        if transformadores_red[i][15] != None:
            str_observaciones = transformadores_red[i][15].replace(chr(13),'. ').replace(chr(10),'')
        str_aceite = "0"
        if transformadores_red[i][16] != None:
            str_aceite = str(transformadores_red[i][16]).replace('.',',')
        coords = convertir_coordenadas(self, transformadores_red[i][17], transformadores_red[i][18], srid, 4326)
        f.writelines(str_zona + chr(9) + str_ubicacion + chr(9) + str_tipo_se + chr(9) + str_potencia + chr(9) + str_tension + chr(9) + str_marca + chr(9) + str_anio + chr(9) + str_chapa + chr(9) + str_kit + chr(9) + str_cromatografia + chr(9) + str_certificado + chr(9) + str_anomalia + chr(9) + str_fecha_normalizacion + chr(9) + str_observaciones + chr(9) + str_aceite + chr(9) + str(coords[1]).replace('.',',') + chr(9) + str(coords[0]).replace('.',',') + chr(9) + str_codigo_empresa + "\n")
    cursor = conn.cursor()
    cursor.execute("SELECT ISNULL(Transformadores.Potencia, 5) AS Potencia, ISNULL(Transformadores.Tension_1/1000, '13.2') AS Tension, ISNULL(Transformadores.Marca, 'SD') AS Marca, ISNULL(Transformadores.Anio_fabricacion, '1900') AS Anio, ISNULL(Transformadores.N_chapa, 'S/N') AS Chapa, Transformadores.Kit, ISNULL(Transformadores.Cromatografia, '0.1') AS Cromatogafia, Transformadores.Certificado, Transformadores.Anomalia, CONVERT(VARCHAR, ISNULL(Transformadores.Fecha_norm, '1980-01-01'), 103), Transformadores.Obs_pcb, Transformadores.Aceite, Transformadores.id_trafo FROM Transformadores WHERE Transformadores.Usado=1")
    #convierto el cursor en array
    transformadores_almacen = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Transformadores en Almacen...", "Cancelar", 0, len(transformadores_almacen))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    for i in range (0, len(transformadores_almacen)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(i)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_zona = "D"
        str_ubicacion = str(transformadores_almacen[i][12]) + "-Depósito"
        str_tipo_se = ""
        str_potencia = str(transformadores_almacen[i][0]).replace('.',',')
        str_tension = str(round(transformadores_almacen[i][1],1)).replace('.',',')
        str_marca = str(transformadores_almacen[i][2])
        str_anio = str(transformadores_almacen[i][3])
        if transformadores_almacen[i][4]=="0":
            str_chapa="S/N"
        else:
           str_chapa = transformadores_almacen[i][4]
        str_kit = "-"
        if transformadores_almacen[i][5]=="+":
            str_kit = "+"
        if transformadores_almacen[i][5] != None:
            j = transformadores_almacen[i][5].find('+')
            if j>0:
                str_kit = "+"
            j = transformadores_almacen[i][5].find('osit')
            if j>0:
                str_kit = "+"
            if transformadores_almacen[i][5].strip()=="":
                str_kit = "-"
        str_cromatografia = "0.1"
        if str(transformadores_almacen[i][6]) != "0":
            str_cromatografia = transformadores_almacen[i][6].replace(',','.')
        str_certificado = "SI"
        if str(transformadores_almacen[i][7]) == "0":
            str_certificado = "NO"
        str_anomalia = "SA"
        if transformadores_almacen[i][8] != None:
            j = transformadores_almacen[i][8].upper().find('RDIDA')
            if j>0:
                str_anomalia = "PA"
            j = transformadores_almacen[i][8].upper().find('OLOR')
            if j>0:
                str_anomalia = "EO"
            j = transformadores_almacen[i][8].upper().find('VISU')
            if j>0:
                str_anomalia = "CV"
            j = transformadores_almacen[i][8].upper().find('AUD')
            if j>0:
                str_anomalia = "CA"
            if str(transformadores_almacen[i][8]) == 'Pérdida de Aceite':
                str_anomalia = "PA"
            if str(transformadores_almacen[i][8]) == 'Emanación de Olores':
                str_anomalia = "EO"
            if str(transformadores_almacen[i][8]) == 'Contaminación Visual':
                str_anomalia = "CV"
            if str(transformadores_almacen[i][8]) == 'Contaminación Auditiva':
                str_anomalia = "CA"
            if str(transformadores_almacen[i][8]) == 'Obra Civil Defectuosa':
                str_anomalia = "OCD"
        if transformadores_almacen[i][9] != None:
            str_fecha_normalizacion = str(transformadores_almacen[i][9])
        if transformadores_almacen[i][10] != None:
            str_observaciones = transformadores_almacen[i][10].replace(chr(13),'. ').replace(chr(10),'')
        str_aceite = "0"
        if transformadores_almacen[i][11] != None:
            str_aceite = str(transformadores_almacen[i][11]).replace('.',',')
        f.writelines(str_zona + chr(9) + str_ubicacion + chr(9) + str_tipo_se + chr(9) + str_potencia + chr(9) + str_tension + chr(9) + str_marca + chr(9) + str_anio + chr(9) + str_chapa + chr(9) + str_kit + chr(9) + str_cromatografia + chr(9) + str_certificado + chr(9) + str_anomalia + chr(9) + str_fecha_normalizacion + chr(9) + str_observaciones + chr(9) + str_aceite + chr(9) + str_lon + chr(9) + str_lat + chr(9) + str_codigo_empresa + "\n")
    f.close()
    # Forzar el cierre del QProgressDialog
    progress.close()
    QMessageBox.warning(None, 'EnerGis 6', "Exportado en C:/GIS/EnerGis6/OCEBA/res811.txt")

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
        f.writelines(str(nodos[n][0]) + ', ' + nodos[n][1].replace('\n',' ').replace(',',' ').strip() + ', ' + nodos[n][2].replace('\n',' ').replace(',',' ').strip() + ', ' + nodos[n][3].replace(',',' ') + ', ' + str(nodos[n][6]) + ', ' + nodos[n][7].replace(',',' ') + ', ' + nodos[n][8] + ', ' + str(coords[1]) + ', ' + str(coords[0]) + '\n')
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
            str_linea = str_linea + str(coords[1]) + ' ' + str(coords[0]) + ', '
        f.writelines(str(lineas[l][0]) + ', ' + str(lineas[l][1]) + ', ' + str(lineas[l][2]) + ', ' + lineas[l][3] + ', ' + lineas[l][4].replace(',',' ') + ', ' + str(lineas[l][5]) + ', ' + lineas[l][6].replace(',',' ') + ', (' + str_linea[:-2] + ')' + '\n')
    f.close()
    return 'Exportado en ' + str_archivo
    #except:
    #    return 'No se pudo exportar'

def exportar_google(self, mapCanvas, conn, srid, nombre_modelo):
    #try:
    if os.path.isdir('c:/gis/energis6/Google/')==False:
        os.mkdir('c:/gis/energis6/Google/')
    if nombre_modelo == None or nombre_modelo == '':
        nombre_modelo = 'EnerGis6'
    str_archivo = 'c:/gis/energis6/Google/' + nombre_modelo + '.kml'
    f = open(str_archivo,'w')
    f.writelines('<?xml version=' + '"' + '1.0' + '"' + ' encoding=' + '"' + 'UTF-8' + '"' + '?>' + '\n')
    f.writelines('<kml xmlns=' + '"' + 'http://earth.google.com/kml/2.2' + '"' + '>' + '\n')
    f.writelines('<Document>' + '\n')
    #nombre del documento
    f.writelines('<name></name>' + '\n')
    f.writelines('<description></description>' + '\n')
    f.close()
    #---------------------------------------
    f = open(str_archivo,'a')
    #estilos de nodos
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM Elementos_Nodos')
    #convierto el cursor en array
    elementos = tuple(cursor)
    cursor.close()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Elementos...", "Cancelar", 0, len(elementos))
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    #----------------------------------------------------------------------------
    for e in range (0, len(elementos)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(e)
        if progress.wasCanceled():
            break
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        str_elemento = str(elementos[e][0])
        #Icono del elemento
        f.writelines('<Style id="' + str_elemento + '">' + '\n')
        f.writelines(' <IconStyle>' + '\n')
        f.writelines('  <Icon>' + '\n')
        f.writelines('   <href>https://www.servimap.com.ar/images/' + str_elemento + '.png</href>' + '\n')
        f.writelines('  </Icon>' + '\n')
        f.writelines(' </IconStyle>' + '\n')
        f.writelines('</Style>' + '\n')
        #Estilo del elemento
        f.writelines('<StyleMap id="' + str_elemento + 's' + '">' + '\n') #la 's' es para definir trafos a partir de trafo, etc
        f.writelines(' <Pair>' + '\n')
        f.writelines('  <key>normal</key>' + '\n')
        f.writelines('  <styleUrl>#' + str_elemento + '</styleUrl>' + '\n')
        f.writelines(' </Pair>' + '\n')
        f.writelines(' <Pair>' + '\n')
        f.writelines('  <key>highlight</key>' + '\n')
        f.writelines('  <styleUrl>#' + str_elemento + '</styleUrl>' + '\n')
        f.writelines(' </Pair>' + '\n')
        f.writelines('</StyleMap>' + '\n')
    f.close()
    #---------------------------------------
    f = open(str_archivo,'a')
    #estilos de líneas
    f.writelines('<Style id="default">' + '\n')
    f.writelines(' <LineStyle>' + '\n')
    f.writelines('  <color>FF00FF00</color>' + '\n') #verde
    f.writelines('  <width>2</width>' + '\n')
    f.writelines(' </LineStyle>' + '\n')
    f.writelines(' <PolyStyle>' + '\n')
    f.writelines('  <color>FF00FF00</color>' + '\n')
    f.writelines('  <width>2</width>' + '\n')
    f.writelines(' </PolyStyle>' + '\n')
    f.writelines('</Style>' + '\n')
    n = mapCanvas.layerCount()
    layers = [mapCanvas.layer(i) for i in range(n)]
    for lyr in layers:
        if lyr.name()[:6] == 'Lineas' and lyr.name() != 'Lineas_Proyecto':
            if lyr.name() [7 - len(lyr.name()):].isnumeric():
                str_tension = lyr.name() [7 - len(lyr.name()):]
                # Obtengo los estilos de los alimentadores
                estilos = obtener_estilos_de_linea(lyr)
                for estilo in estilos:
                    alimentador = estilo['label'].replace('<','').replace('>','')
                    #Ancho = estilo['width']
                    #tengo que pasar de #AABBCC a FFCCAABB
                    color = estilo['color'].replace('#','')
                    color = color[-4:] + color[:2]
                    color = 'ff' + color
                    if int(str_tension)>1000:
                        f.writelines('<Style id="' + alimentador + '2">' + '\n')
                        f.writelines(' <LineStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>2</width>' + '\n')
                        f.writelines(' </LineStyle>' + '\n')
                        f.writelines(' <PolyStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>2</width>' + '\n')
                        f.writelines(' </PolyStyle>' + '\n')
                        f.writelines('</Style>' + '\n')
                        #---------------------------------------
                        f.writelines('<Style id="' + alimentador + '3">' + '\n')
                        f.writelines(' <LineStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>3</width>' + '\n')
                        f.writelines(' </LineStyle>' + '\n')
                        f.writelines(' <PolyStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>3</width>' + '\n')
                        f.writelines(' </PolyStyle>' + '\n')
                        f.writelines('</Style>' + '\n')
                    else:
                        f.writelines('<Style id="' + alimentador + '1">' + '\n')
                        f.writelines(' <LineStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>1</width>' + '\n')
                        f.writelines(' </LineStyle>' + '\n')
                        f.writelines(' <PolyStyle>' + '\n')
                        f.writelines('  <color>' + color + '</color>' + '\n')
                        f.writelines('  <width>1</width>' + '\n')
                        f.writelines(' </PolyStyle>' + '\n')
                        f.writelines('</Style>' + '\n')
    f.close()
    #---------------------------------------
    #Tensiones
    cursor = conn.cursor()
    cursor.execute('SELECT Tension FROM Niveles_Tension WHERE Tension<>0 ORDER BY Tension DESC')
    #convierto el cursor en array
    tensiones = tuple(cursor)
    cursor.close()
    for t in range (0, len(tensiones)):
        str_tension = str(tensiones[t][0])
        #---------------------------------------
        f = open(str_archivo,'a')
        f.writelines('<Folder>' + '\n')
        f.writelines('<name>' + str_tension + '</name>' + '\n')
        f.close()
        #---------------------------------------
        f = open(str_archivo,'a')
        #Nodos
        cursor = conn.cursor()
        cursor.execute('SELECT geoname, nombre, elmt, val1, descripcion, xcoord, ycoord FROM Nodos WHERE elmt<>0 AND Tension=' + str_tension)
        #convierto el cursor en array
        nodos = tuple(cursor)
        cursor.close()
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Nodos " + str_tension + "...", "Cancelar", 0, len(nodos))
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        for n in range (0, len(nodos)):
            #----------------------------------------------------------------------------
            # Actualiza el progreso
            progress.setValue(n)
            if progress.wasCanceled():
                break
            # Permitir que la GUI se actualice (similar a DoEvents)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            str_nombre = ''
            str_descripcion = ''
            if nodos[n][2] == 6:
                f.writelines('  <Folder>' + '\n')
                f.writelines('   <name></name>' + '\n')
            else: #en los suministros, el placemark va despues
                f.writelines('  <Placemark id="' + str(nodos[n][0]) + '">' + '\n')
                if nodos[n][1] != None:
                    str_nombre = nodos[n][1]
                    str_nombre = str_nombre.replace('<','*')
                    str_nombre = str_nombre.replace('>','*')
                    str_nombre = str_nombre.replace('+','*')
                    str_nombre = str_nombre.replace('','')
                    str_nombre = str_nombre.replace('&','Y')
                    f.writelines('   <name>' + str_nombre + '</name>' + '\n')
                    f.writelines('   <styleUrl>#' + str(nodos[n][2]) + 's</styleUrl>' + '\n') #notese que tiene la 's'
            if nodos[n][2] == 2 or nodos[n][2] == 3:
                f.writelines('   <description>' + '\n')
                if nodos[n][3] != None:
                    str_descripcion = nodos[n][3]
                    str_descripcion = str_descripcion.replace('ï¿½','-')
                    str_descripcion = str_descripcion.replace('<','*')
                    str_descripcion = str_descripcion.replace('>','*')
                    str_descripcion = str_descripcion.replace('+','*')
                    str_descripcion = str_descripcion.replace('','')
                    str_descripcion = str_descripcion.replace('&','Y')
                    f.writelines('    ' + str_descripcion + '\n')
                f.writelines('   </description>' + '\n')
            if nodos[n][2] == 4 :
                f.writelines('   <description>' + '\n')
                str_descripcion = ''
                if nodos[n][3] != None:
                    str_descripcion = nodos[n][3]
                    if nodos[n][4] != None:
                        str_descripcion = nodos[n][4] + ' - ' + nodos[n][3] + ' kVA'
                str_descripcion = str_descripcion.replace('ï¿½','-')
                str_descripcion = str_descripcion.replace('<','*')
                str_descripcion = str_descripcion.replace('>','*')
                str_descripcion = str_descripcion.replace('+','*')
                str_descripcion = str_descripcion.replace('','')
                str_descripcion = str_descripcion.replace('&','Y')
                f.writelines('    ' + str_descripcion + '\n')
                f.writelines('   </description>' + '\n')
            if nodos[n][2] == 8:
                f.writelines('   <description>' + '\n')
                if nodos[n][4] != None:
                    str_descripcion = nodos[n][3]
                    str_descripcion = 'Salida ' + str_descripcion
                    str_descripcion = str_descripcion.replace('<','*')
                    str_descripcion = str_descripcion.replace('>','*')
                    str_descripcion = str_descripcion.replace('+','*')
                    str_descripcion = str_descripcion.replace('','')
                    str_descripcion = str_descripcion.replace('&','Y')
                    f.writelines('    ' + str_descripcion + '\n')
                f.writelines('   </description>' + '\n')
            coords = convertir_coordenadas(self, nodos[n][5], nodos[n][6], srid, 4326)
            if nodos[n][2]!= 6: #para suministros, son 1 punto por usuario
                f.writelines('    <Point>' + '\n')
                f.writelines('     <coordinates>' + str(coords[1]) + ',' + str(coords[0]) + ',0</coordinates>' + '\n')
                f.writelines('    </Point>' + '\n')
                f.writelines('  </Placemark>' + '\n')
            else:
                f.writelines('   <description></description>' + '\n')
                #f.writelines('   <open>1</open>' + '\n')
                cursor = conn.cursor()
                cursor.execute('SELECT id_usuario, usuarios.nombre FROM Usuarios INNER JOIN Suministros ON Usuarios.id_suministro=Suministros.id_suministro INNER JOIN Nodos ON Suministros.id_nodo=Nodos.geoname WHERE geoname=' + str(nodos[n][0]) + ' AND Tension=' + str_tension)
                #convierto el cursor en array
                usuarios = tuple(cursor)
                cursor.close()
                if len(usuarios)==0:
                    f.writelines('   <Placemark>' + '\n')
                    f.writelines('     <name></name>' + '\n')
                    f.writelines('     <description></description>' + '\n')
                    f.writelines('     <styleUrl>#6s</styleUrl>' + '\n')
                    f.writelines('     <Point>' + '\n')
                    f.writelines('     <coordinates>' + str(coords[1]) + ',' + str(coords[0]) + ',0</coordinates>' + '\n')
                    f.writelines('     </Point>' + '\n')
                    f.writelines('   </Placemark>' + '\n')
                else:
                    for u in range (0, len(usuarios)):
                        str_descripcion = str(usuarios[u][0]) + ' - ' + usuarios[u][1]
                        str_descripcion = str_descripcion.replace('<', '*')
                        str_descripcion = str_descripcion.replace('>', '*')
                        str_descripcion = str_descripcion.replace('+', '*')
                        str_descripcion = str_descripcion.replace('', '')
                        str_descripcion = str_descripcion.replace('&','Y')
                        f.writelines('   <Placemark>' + '\n')
                        f.writelines('     <name></name>' + '\n')
                        f.writelines('     <description>' + str_descripcion + '</description>' + '\n')
                        f.writelines('     <styleUrl>#6s</styleUrl>' + '\n')
                        f.writelines('     <Point>' + '\n')
                        f.writelines('     <coordinates>' + str(coords[1]) + ',' + str(coords[0]) + ',0</coordinates>' + '\n')
                        f.writelines('     </Point>' + '\n')
                        f.writelines('   </Placemark>' + '\n')
                f.writelines('  </Folder>' + '\n')
        f.close()
        #---------------------------------------
        f = open(str_archivo,'a')
        #Lineas
        cursor = conn.cursor()
        cursor.execute('SELECT geoname, fase, descripcion, tension, alimentador, obj.ToString() FROM Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id WHERE Tension=' + str_tension)
        #convierto el cursor en array
        lineas = tuple(cursor)
        cursor.close()
        #----------------------------------------------------------------------------
        progress = QProgressDialog("Lineas " + str_tension + "...", "Cancelar", 0, len(lineas))
        progress.setWindowTitle("Progreso")
        progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
        progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
        progress.setValue(0)  # Inicia el progreso en 0
        #----------------------------------------------------------------------------
        for l in range (0, len(lineas)):
            #----------------------------------------------------------------------------
            # Actualiza el progreso
            progress.setValue(l)
            if progress.wasCanceled():
                break
            # Permitir que la GUI se actualice (similar a DoEvents)
            QApplication.processEvents()
            #----------------------------------------------------------------------------
            f.writelines('  <Placemark id="' + str(lineas[l][0]) + '">' + '\n')
            f.writelines('  <name>' + str(lineas[l][0]) + '</name>' + '\n')
            str_descripcion = lineas[l][2]
            str_descripcion = str_descripcion.replace('<','*')
            str_descripcion = str_descripcion.replace('>','*')
            str_descripcion = str_descripcion.replace('+','*')
            str_descripcion = str_descripcion.replace('','')
            f.writelines('  <description>' + str_descripcion + '</description>' + '\n')
            alimentador = lineas[l][4].replace('<','').replace('>','')
            if alimentador=='' or alimentador=='SD' or alimentador=='desc.':
                f.writelines('  <styleUrl>#default</styleUrl>' + '\n')
            else:
                if lineas[l][3] < 1000:
                    f.writelines('  <styleUrl>#' + alimentador + '1</styleUrl>' + '\n')
                else:
                    if str(lineas[l][1])=='123':
                        f.writelines('  <styleUrl>#' + alimentador + '3</styleUrl>' + '\n')
                    else:
                        f.writelines('  <styleUrl>#' + alimentador + '2</styleUrl>' + '\n')
            f.writelines('  <LineString>' + '\n')
            f.writelines('   <extrude>1</extrude>' + '\n')
            f.writelines('   <tessellate>1</tessellate>' + '\n')
            f.writelines('   <altitudeMode>RelativeToGround</altitudeMode>' + '\n')
            f.writelines('    <coordinates>' + '\n')
            str_polilinea = lineas[l][5].replace('LINESTRING (','').replace(')','')
            coordenadas = str_polilinea.split(', ')
            for coordenada in coordenadas:
                x, y = coordenada.split(' ')
                coords = convertir_coordenadas(self, x, y, srid, 4326)
                f.writelines(str(coords[1]) + ',' + str(coords[0]) + ',0' + '\n')
            f.writelines('    </coordinates>' + '\n')
            f.writelines('  </LineString>' + '\n')
            f.writelines(' </Placemark>' + '\n')
        f.writelines('</Folder>' + '\n')
        f.close()
    #Pie
    f = open(str_archivo,'a')
    f.writelines('</Document>' + '\n')
    f.writelines('</kml>' + '\n')
    f.close()
    QMessageBox.information(None, 'EnerGis 6', 'Exportado en ' + str_archivo)

def obtener_estilos_de_linea(capa):
    estilos = []
    # Obtener el renderer de la capa
    renderer = capa.renderer()
    # Obtener los símbolos del renderer
    # Iterar sobre todas las categorías
    for category in renderer.categories():
        label = category.label()
        value = category.value()
        symbol = category.symbol()
        color = symbol.color().name()
        width = symbol.width()
        estilos.append({
            'value': value,
            'label': label,
            'color': color,
            'width': width
        })
    return estilos

def exportar_gis_dpe(self, conn, srid):
    #verificacion seccion fase
    #SELECT DISTINCT Descripcion FROM [Elementos_Lineas] INNER JOIN Lineas ON Lineas.Elmt=Elementos_Lineas.id WHERE CAST([Val2] AS FLOAT) NOT IN (SELECT Seccion FROM Secciones WHERE Tipo='F')
    #verificacion seccion neutro
    #SELECT DISTINCT Descripcion FROM [Elementos_Lineas] INNER JOIN Lineas ON Lineas.Elmt=Elementos_Lineas.id WHERE CAST([Val13] AS FLOAT) NOT IN (SELECT Seccion FROM Secciones WHERE Tipo='N')

    cursor = conn.cursor()
    cursor.execute('UPDATE Nodos SET Elmt=0 WHERE Geoname IN (SELECT Nodos.Geoname FROM (Nodos LEFT JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro WHERE (nodos.Elmt = 6) GROUP BY Nodos.Geoname HAVING (Count(Usuarios.id_usuario) = 0))')
    cursor.execute('UPDATE Lineas SET Acometida=1 WHERE Acometida=0 AND Geoname IN (SELECT Lineas.Geoname FROM (Nodos INNER JOIN Spurs ON Nodos.Geoname = Spurs.nodo) INNER JOIN Lineas ON Spurs.linea = Lineas.Geoname WHERE (((Nodos.Elmt)=6) AND ((Lineas.Longitud)<30)))')
    cursor.execute('UPDATE Lineas SET Acometida=0 WHERE Acometida=1 AND Geoname NOT IN (SELECT Lineas.Geoname FROM (Nodos INNER JOIN Spurs ON Nodos.Geoname = Spurs.nodo) INNER JOIN Lineas ON Spurs.linea = Lineas.Geoname WHERE (((Nodos.Elmt)=6) AND ((Lineas.Longitud)<30)))')
    cursor.execute("UPDATE Nodos SET Alimentador='<desc.>' WHERE Alimentador IS NULL OR Alimentador=''")
    cursor.execute("UPDATE Lineas SET Alimentador='<desc.>' WHERE Alimentador IS NULL OR Alimentador=''")
    conn.commit()
    #----------------------------------------------------------------------------
    progress = QProgressDialog("Procesando...", "Cancelar", 0, 100)
    progress.setWindowTitle("Progreso")
    progress.setWindowModality(True)  # Hace que la ventana de progreso sea modal
    progress.setMinimumDuration(0)  # Muestra inmediatamente la ventana de progreso
    progress.setValue(0)  # Inicia el progreso en 0
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    #compilo para sacar nodos por trafo
    #----------------------------------------------------------------------------
    #----------------------------------------------------------------------------
    cursor = self.conn.cursor()
    cursor.execute("SELECT aux, geoname FROM mNodos WHERE estado=1")
    fuentes = cursor.fetchall()
    cursor.close()
    #----------------------------------------------------------------------------
    import clr
    # Cargar el ensamblado
    clr.AddReference(os.path.join(basepath, 'NavRed7.dll'))
    from EnerGis6.NavRed7 import NavRed

    from System import Int64, Array
    # Crear arreglos
    monodos = Array.CreateInstance(Int64, len(self.mnodos))
    mnodos = Array.CreateInstance(Int64, len(self.mnodos), len(self.mnodos[0]))
    mlineas = Array.CreateInstance(Int64, len(self.mlineas), len(self.mlineas[0]))
    # Copiar valores a mnodos
    for i in range(len(self.mnodos)):
        for j in range(len(self.mnodos[0])):
            mnodos[i, j] = self.mnodos[i][j]
    # Copiar valores a mlineas
    for i in range(len(self.mlineas)):
        for j in range(len(self.mlineas[0])):
            mlineas[i, j] = self.mlineas[i][j]

    # Instanciar la clase NavRed
    navred_instance = NavRed()
    for fuente in fuentes:
        # Preparar los valores de entrada
        fuentenavegada = Int64(fuente[0])
        # Llamar a la función
        resultado = navred_instance.Navegar_compilar_red(monodos,mnodos,mlineas,fuentenavegada)
        if resultado[0]!="Ok":
            QMessageBox.critical(None, 'EnerGis 6', resultado[0])
            return
    self.red_verificada=True

    trafos_nodos=['-1']*mnodos.GetLength(0)

    for n in range(mnodos.GetLength(0)):
        if mnodos.GetValue(n,44)!=0:
            trafos_nodos[mnodos.GetValue(n,44)]=trafos_nodos[mnodos.GetValue(n,44)] + ',' + str(mnodos.GetValue(n,1))

    cursor = self.conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE Nodos_Transformador")
        self.conn.commit()
    except:
        self.conn.rollback()

    for n in range(len(trafos_nodos)):
        if trafos_nodos[n]!='-1':
            try:
                cursor.execute("INSERT INTO Nodos_Transformador SELECT geoname, " + str(mnodos.GetValue(n,1)) + " FROM Nodos WHERE Tension>0 AND geoname IN (" + str(trafos_nodos[n]) + ")")
                self.conn.commit()
            except:
                self.conn.rollback()
    #----------------------------------------------------------------------------
    progress.setValue(5)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    if os.path.isdir('c:/gis/energis6/DPE/')==False:
        os.mkdir('c:/gis/energis6/DPE/')
    str_archivo = 'c:/gis/energis6/DPE/nodos.txt'
    f = open(str_archivo,'w')
    progress.setWindowTitle("Exportando Nodos MT ...")
    cursor = conn.cursor()
    cursor.execute('SELECT geoname, Nodos.Descripcion, Nodos.tension, Alimentadores.ssee, Nodos.alimentador, Nodos.XCoord, Nodos.YCoord FROM Nodos LEFT JOIN Alimentadores ON Nodos.Alimentador = Alimentadores.Id_Alim WHERE Nodos.Tension>=1000')
    #convierto el cursor en array
    nodos = tuple(cursor)
    cursor.close()
    for i in range (0, len(nodos)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(5 + 5 * int(i/len(nodos)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        coords = convertir_coordenadas(self, nodos[i][5], nodos[i][6], srid, 4326)
        if nodos[i][3]==None:
            #descripcion = ""
            #if nodos[i][1]!=None:
            #    descripcion = nodos[i][1].replace("-", "")
            f.writelines(str(nodos[i][0]) + ',' + str(nodos[i][2]) + '-ssee-alim' + ',,' + str(coords[1]) + ',' + str(coords[0]) + ',' + str(nodos[i][2]) + ',N,,' + '\n')
        else:
            f.writelines(str(nodos[i][0]) + ',' + str(nodos[i][2]) + '-' + nodos[i][3].replace('-','') + '-' + nodos[i][4].replace('-','') + ',,' + str(coords[1]) + ',' + str(coords[0]) + ',' + str(nodos[i][2]) + ',N,,' + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(10)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle("Exportando Nodos BT ...")
    cursor = conn.cursor()
    cursor.execute("SELECT Nodos.Geoname, Nodos.elmt, Nodos.Tension, ISNULL(Nodos_1.Tension, 13200) AS tensionmt, Nodos.XCoord, Nodos.YCoord, ISNULL(Alimentadores.ssee,'SSEE') AS ssee, Nodos.Alimentador AS alimmt, ISNULL(Nodos_1.Nombre, 'CT') AS ct FROM Nodos AS Nodos_1 RIGHT JOIN ((Nodos LEFT JOIN Alimentadores ON Nodos.Alimentador = Alimentadores.Id_Alim) LEFT JOIN Nodos_Transformador ON Nodos.Geoname = Nodos_Transformador.Geoname) ON Nodos_1.Geoname = Nodos_Transformador.Id WHERE Nodos.Tension>0 AND Nodos.Tension<1000")
    #convierto el cursor en array
    nodos = tuple(cursor)
    cursor.close()
    seccionadores_abiertos=[]
    for i in range (0, len(nodos)):
        #0 Geoname
        #1 elmt
        #2 Tension
        #3 tensionmt
        #4 XCoord
        #5 YCoord
        #6 ssee
        #7 alimmt
        #8 ct
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(10 + 5 * int(i/len(nodos)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        if nodos[i][6]==None:
            ssee = "SSEE"
        else:
            ssee = nodos[i][6]
        if nodos[i][3]==None:
            tensionmt = 13200
        else:
            tensionmt = nodos[i][3]
        if nodos[i][8]==None:
            ssee = "CT"
        else:
            ssee = nodos[i][8]
        coords = convertir_coordenadas(self, nodos[i][4], nodos[i][5], srid, 4326)
        if nodos[i][0] not in seccionadores_abiertos:
            f.writelines(str(nodos[i][0]) + ',' + str(tensionmt) + '-' + ssee.replace('-', '_') + '-' + nodos[i][7].replace('-', '_') + ',' + str(nodos[i][2]) + '-' + nodos[i][8].replace('-', '_') + '-' + nodos[i][8].replace('-', '_') + ',' + str(coords[1]) + ',' + str(coords[0]) + ',' + str(nodos[i][2]) + ',N,,' + nodos[i][8].replace('-', '_') + '\n')
            if nodos[i][1]==3:
                seccionadores_abiertos.append(nodos[i][0])
        #mandamos un CT generico para todo lo desconectado
        #Print #1, "CT,CT,Buenos Aires,Coop,Coop,Coop,Coop,0,0,Aereo,En Servicio,2000/01/01,1111/2001,CT,,13200,0,0,1,0,400,0,0,1,0"
    f.close()
    #----------------------------------------------------------------------------
    progress.setValue(15)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle("Datos de lineas ...")
    alimentadores = []
    cursor = conn.cursor()
    cursor.execute('SELECT Alimentador, Zona, SUM(Longitud) AS m FROM Lineas WHERE Tension>=1000 GROUP BY Alimentador, Zona ORDER BY Alimentador')
    #convierto el cursor en array
    alim = tuple(cursor)
    cursor.close()
    str_alimentador = ""
    for i in range (0, len(alim)):
        km_rural=0
        km_urbano=0
        if alim[i][0]!='Rural':
            km_rural=alim[i][2]
        else:
            km_urbano=alim[i][2]
        if alim[i][0]!=str_alimentador:
            alimentadores.append([alim[i][0],0.0,0.0])
            str_alimentador = alim[i][0]
        else:
            alimentadores[-1][1]=alimentadores[-1][1]+km_rural
            alimentadores[-1][2]=alimentadores[-1][2]+km_urbano
    #----------------------------------------------------------------------------
    progress.setValue(20)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    postes = []
    cursor = conn.cursor()
    cursor.execute('SELECT Lineas.Geoname, Elementos_Postes.Value2 AS Tipo, Elementos_Postes.Value1 AS Material, Postes.Aislacion, Postes.Fundacion, Postes.Ternas, Postes.Comparte, Postes.tipo AS Estructura, COUNT(Postes.Geoname) AS Cantidad FROM Lineas INNER JOIN Lineas_Postes ON Lineas.Geoname = Lineas_Postes.id_linea INNER JOIN Postes ON Lineas_Postes.id_poste = Postes.Geoname INNER JOIN Elementos_Postes ON Postes.Elmt = Elementos_Postes.Id INNER JOIN Estructuras ON Postes.Estructura = Estructuras.Id WHERE (Lineas.Tension >= 1000) GROUP BY Lineas.Geoname, Postes.tipo, Elementos_Postes.Value2, Elementos_Postes.Value1, Postes.Aislacion, Postes.Fundacion, Postes.Ternas, Postes.Comparte ORDER BY Lineas.Geoname')
    #convierto el cursor en array
    lineas_postes = tuple(cursor)
    cursor.close()
    geoname_linea = 0
    for i in range (0, len(lineas_postes)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(20 + 5 * int(i/len(lineas_postes)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #0 Geoname
        #1 Tipo
        #2 Material
        #3 Aislacion
        #4 Fundacion
        #5 Ternas
        #6 Comparte
        #7 Estructura
        #8 Cantidad
        if lineas_postes[i][0]!=geoname_linea:
            postes.append([lineas_postes[i][0],lineas_postes[i][1],lineas_postes[i][2],lineas_postes[i][3],lineas_postes[i][4],lineas_postes[i][5],lineas_postes[i][6],lineas_postes[i][7],lineas_postes[i][8],0])
            geoname_linea = lineas_postes[i][0]
        else:
            #si la linea ya la tengo en el array, comparo la cantidad, y tomo los valores mas predominantes
            #postes[9] tiene el total de postes
            if lineas_postes[i][8]>postes[-1][9]:
                postes[-1][1]=lineas_postes[i][1]
                postes[-1][2]=lineas_postes[i][2]
                postes[-1][3]=lineas_postes[i][3]
                postes[-1][4]=lineas_postes[i][4]
                postes[-1][5]=lineas_postes[i][5]
                postes[-1][6]=lineas_postes[i][6]
                postes[-1][7]=lineas_postes[i][7]
                postes[-1][8]=lineas_postes[i][8]
                postes[-1][9]=lineas_postes[i][8]+postes[-1][9] #el valor anterior para a estructura especial
            else:
                postes[-1][9]=postes[-1][9]+lineas_postes[i][8]
    #----------------------------------------------------------------------------
    progress.setValue(25)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    str_archivo = 'c:/gis/energis6/DPE/lineas.txt'
    f = open(str_archivo,'w')
    progress.setWindowTitle("Exportando Lineas MT ...")
    cursor = conn.cursor()
    cursor.execute('SELECT Lineas.Geoname, Lineas.Desde, Lineas.Hasta, Lineas.Tension, Lineas.Longitud, Lineas.Elmt, Lineas.Acometida, Lineas.obj.ToString() AS Obj, Lineas.Modificacion AS Instalacion, Lineas.Exp AS Expediente, Lineas.UUCC, Lineas.Alimentador, Elementos_Lineas.Descripcion, Elementos_Lineas.Val8 AS Tipo, Lineas.Disposicion, Lineas.Fase, Elementos_Lineas.Val9 AS Material_Fase, Elementos_Lineas.Val2 AS Seccion_Fase, Elementos_Lineas.Val11 AS Neutro, Elementos_Lineas.Val12 AS Material_Neutro, Elementos_Lineas.Val13 AS Seccion_Neutro, Elementos_Lineas.Val14 AS Subconductores, Elementos_Lineas.Val15 AS Material_HG, Elementos_Lineas.Val16 AS Seccion_HG, Alimentadores.ssee FROM  Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id LEFT OUTER JOIN Alimentadores ON Lineas.Alimentador = Alimentadores.Id_Alim WHERE (Lineas.Tension >= 1000)')
    #convierto el cursor en array
    lineas = tuple(cursor)
    cursor.close()
    for i in range (0, len(lineas)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(25 + 5 * int(i/len(lineas)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #0 Geoname
        #1 Desde
        #2 Hasta
        #3 Tension
        #4 Longitud
        #5 Elmt
        #6 Acometida
        #7 Obj
        #8 Instalacion
        #9 Expediente
        #10 UUCC
        #11 Alimentador
        #12 Descripcion
        #13 Tipo
        #14 Disposicion
        #15 Fase
        #16 Material_Fase
        #17 Seccion_Fase
        #18 Neutro
        #19 Material_Neutro
        #20 Seccion_Neutro
        #21 Subconductores
        #22 Material_HG
        #23 Seccion_HG
        #24 ssee
        longitud = lineas[i][4]
        if longitud==0:
            longitud=1
        str_linea = str(lineas[i][0]) + "," +  str(lineas[i][1]) + "," +  str(lineas[i][2]) + "," +  str(lineas[i][5])
        if lineas[i][24]==None:
            ssee = 'SSEE'
        else:
            ssee = lineas[i][24].replace('-','')
        str_linea = str_linea + ',' + str(lineas[i][3]) + '-' + ssee + '-' + str(lineas[i][11]).replace('-', '_') + ',,' + str(lineas[i][3])
        str_linea = str_linea + ',' + str(longitud) + ','
        str_polilinea = lineas[i][7].replace('LINESTRING (','').replace(')','')
        coordenadas = str_polilinea.split(', ')
        for coordenada in coordenadas:
            x, y = coordenada.split(' ')
            coords = convertir_coordenadas(self, x, y, srid, 4326)

            str_linea = str_linea + str(coords[1]) + ';' + str(coords[0]) + ';'

        str_linea = str_linea[:-1] + ',' + lineas[i][8].strftime('%Y-%m-%d').replace("'","")
        if lineas[i][9]==None:
            str_linea = str_linea + ',1111/2001'
        elif lineas[i][9] == '00000/2001':
            str_linea = str_linea + ',1111/2001'
        elif lineas[i][9] == '00000/2000':
            str_linea = str_linea + ',1111/2001'
        else:
            str_linea = str_linea + ',' + lineas[i][9]
        if lineas[i][6]==1:
            str_linea = str_linea + ',' + 'Acometida,,'
        else:
            if lineas[i][13]=='A':
                str_linea = str_linea + ',' + 'Aerea Convencional'
                if lineas[i][14]==None:
                    str_linea = str_linea + ',' + 'Horizontal,'
                elif lineas[i][14]=='Horizontal' or lineas[i][14]=='Vertical' or lineas[i][14]=='Triangular':
                    str_linea = str_linea + ',' + lineas[i][14] + ','
                else:
                    str_linea = str_linea + ',' + 'Horizontal,'
            if lineas[i][13]=='S':
                str_linea = str_linea + ',' + 'Subterranea'
                if lineas[i][13].find('3x')>-1 and lineas[i][13].find('+')>-1:
                    str_linea = str_linea + ',,Tetrapolar'
                elif lineas[i][13].find('3x')>-1:
                    str_linea = str_linea + ',,Tripolar'
                else:
                    str_linea = str_linea + ',,Unipolar'
            if lineas[i][13]=='P':
                str_linea = str_linea + ',' + 'Aerea Preensamblado,,'
            if lineas[i][13]=='L':
                str_linea = str_linea + ',' + 'Aerea Compacta,,'
                #Subterránea Aceite
                #Barra Ría
                #Barra Flexible
        str_linea = str_linea + ',' + lineas[i][10].replace(',', '') + ',' #La ultima coma es por un campo de reserva
        str_linea = str_linea + ',' + 'Distribucion'
        str_fase = lineas[i][15]
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        if lineas[i][16]=='Cu':
            str_linea = str_linea + ',' + 'Cobre'
        elif lineas[i][16]=='Al':
            str_linea = str_linea + ',' + 'Aluminio'
        elif lineas[i][16]=='Al/Al':
            str_linea = str_linea + ',' + 'Aleacion de Aluminio'
        elif lineas[i][16]=='Ac':
            str_linea = str_linea + ',' + 'Acero'
        elif lineas[i][16]=='Al/Ac':
            str_linea = str_linea + ',' + 'Aluminio / Acero'
        elif lineas[i][16]=='AcZn':
            str_linea = str_linea + ',' + 'Acero Recubierto Zn'
        elif lineas[i][16]=='AcCu':
            str_linea = str_linea + ',' + 'Acero Recubierto Cu'
        elif lineas[i][16]=='AcAl':
            str_linea = str_linea + ',' + 'Acero Recubierto Al'
        else:
            str_linea = str_linea + ',' + 'Aleacion de Aluminio'
        str_linea = str_linea + ',' + str(lineas[i][17])
        if lineas[i][21]==None:
            str_linea = str_linea + ',1'
        elif lineas[i][21]=='':
            str_linea = str_linea + ',1'
        else:
            str_linea = str_linea + ',' + lineas[i][21]
        if lineas[i][18]==None:
            str_linea = str_linea + ',' + 'N,,'
        elif lineas[i][18]=='0':
            str_linea = str_linea + ',' + 'N,,'
        else:
            str_linea = str_linea + ',' + 'S'
            if lineas[i][19]=='Cu':
                str_linea = str_linea + ',' + 'Cobre'
            elif lineas[i][19]=='Al':
                str_linea = str_linea + ',' + 'Aluminio'
            elif lineas[i][19]=='Al/Al':
                str_linea = str_linea + ',' + 'Aleacion de Aluminio'
            elif lineas[i][19]=='Ac':
                str_linea = str_linea + ',' + 'Acero'
            elif lineas[i][19]=='Al/Ac':
                str_linea = str_linea + ',' + 'Aluminio / Acero'
            else:
                str_linea = str_linea + ',' + 'Aleacion de Aluminio'
            str_linea = str_linea + "," + str(lineas[i][20])
        if lineas[i][21]==None:
            str_linea = str_linea + ',N,'
        elif lineas[i][21]=='N':
            str_linea = str_linea + ',N,'
        else:
            str_linea = str_linea + "," + lineas[i][22]
            str_linea = str_linea + "," + str(lineas[i][23])
        #Alumbrado en MT:
        str_linea = str_linea + ',N,,'
        s_urbana = 0
        for n in range (0, len(alimentadores)):
            if lineas[i][11]==alimentadores[n][0]:
                if alimentadores[n][2]==0:
                    s_urbana = 0
                else:
                    s_urbana = 100 * round(alimentadores[n][1]/(alimentadores[n][1]+alimentadores[n][2]))
                break
        s_rural = 100 - s_urbana
        str_linea = str_linea + ',' + 'URBANO:' + str(s_urbana) + ';RURAL:' + str(s_rural)
        b_existe = False
        for n in range (0, len(postes)):
            if postes[n][0]==lineas[i][0]:
                j=n
                b_existe = True
                break
        if b_existe==False:
            str_linea = str_linea + ',Ninguno,'
        else:
            if postes[j][1]=='Mensula': #Podrían ser también : Grampa o Portico
                str_linea = str_linea + ',Mensula,'
            else:
                str_linea = str_linea + ',Poste,Resumida:'
                #material,aislacion,fundacion,ternas,comparte,estructura,cantidad_predominantes,cantidad_especiales
                str_linea = str_linea + postes[j][2].replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
                if postes[j][3]=='':
                    postes[j][3]='Suspension'
                str_linea = str_linea + '-' + postes[j][3].replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
                if postes[j][4]=='1':
                    str_linea = str_linea + '-S'
                else:
                    str_linea = str_linea + '-N'
                if postes[j][5]=='Simple Terna':
                    str_linea = str_linea + '-0'
                elif postes[j][5]=='2 Ternas':
                    str_linea = str_linea + '-1'
                elif postes[j][5]=='3 Ternas':
                    str_linea = str_linea + '-2'
                elif postes[j][5]=='4 Ternas':
                    str_linea = str_linea + '-3'
                elif postes[j][5]=='Alumbrado':
                    str_linea = str_linea + '-A'
                else:
                    str_linea = str_linea + '-0'
                if postes[j][6]=='No':
                    str_linea = str_linea + '-N'
                else:
                    str_linea = str_linea + '-S'
                str_linea = str_linea + '-' + str(postes[j][8])
                str_linea = str_linea + '-' + str(postes[j][9])
        f.writelines(str_linea + '\n')

    #----------------------------------------------------------------------------
    progress.setValue(30)
    QApplication.processEvents()
    #----------------------------------------------------------------------------

    cursor = conn.cursor()
    cursor.execute('TRUNCATE TABLE Lineas_Trafos')
    cursor.execute('INSERT INTO Lineas_Trafos SELECT DISTINCT Geoname_l, Geoname_t FROM (SELECT Nodos_Transformador.Id AS Geoname_t, Lineas.Geoname AS Geoname_l FROM Nodos_Transformador INNER JOIN Lineas ON Nodos_Transformador.Geoname = Lineas.Desde WHERE Lineas.Tension>0 AND Lineas.Tension<1000 UNION SELECT Nodos_Transformador.Id AS Geoname_t, Lineas.Geoname AS Geoname_l FROM Nodos_Transformador INNER JOIN Lineas ON Nodos_Transformador.Geoname = Lineas.Hasta WHERE Lineas.Tension>0 AND Lineas.Tension<1000) L')
    conn.commit()

    cts_sin_trafo = []
    cursor = conn.cursor()
    cursor.execute('SELECT Nodos.Geoname FROM Nodos LEFT OUTER JOIN Transformadores ON Nodos.Nombre = Transformadores.Id_ct WHERE (Nodos.Elmt = 4) AND (Transformadores.Id_trafo IS NULL)')
    #convierto el cursor en array
    cts = tuple(cursor)
    cursor.close()
    for i in range (0, len(cts)):
        cts_sin_trafo.append(cts[i][0])

    progress.setWindowTitle("Exportando Lineas BT ...")
    cursor = conn.cursor()
    cursor.execute('SELECT Lineas.Geoname, Lineas.Desde, Lineas.Hasta, Lineas.Tension, Lineas.Longitud, Lineas.elmt, Lineas.Acometida, Lineas.obj.ToString() AS Obj, Lineas.Modificacion AS Instalacion, Lineas.Exp AS Expediente, Lineas.UUCC, Lineas.Alimentador, Elementos_Lineas.Descripcion, Elementos_Lineas.Val8 AS Tipo, Lineas.Disposicion, Lineas.Fase, Elementos_Lineas.Val9 AS Material_Fase, Elementos_Lineas.Val2 AS Seccion_Fase, Elementos_Lineas.Val11 AS Neutro, Elementos_Lineas.Val12 AS Material_Neutro, Elementos_Lineas.Val13 AS Seccion_Neutro, Elementos_Lineas.Val14 AS Subconductores, Elementos_Lineas.Val17 AS Material_AL, Elementos_Lineas.Val18 AS Seccion_AL, Nodos_2.Tension AS tensionmt, Alimentadores.ssee, Nodos_2.Alimentador AS alimmt, Nodos_2.Nombre AS ct FROM (((Nodos INNER JOIN ((Lineas INNER JOIN Elementos_Lineas ON Lineas.Elmt = Elementos_Lineas.Id) INNER JOIN Nodos AS Nodos_1 ON Lineas.Hasta = Nodos_1.Geoname) ON Nodos.Geoname = Lineas.Desde) LEFT JOIN Alimentadores ON Lineas.Alimentador = Alimentadores.Id_Alim) INNER JOIN Lineas_Trafos ON Lineas.Geoname = Lineas_Trafos.Geoname_l) INNER JOIN Nodos AS Nodos_2 ON Lineas_Trafos.Geoname_t = Nodos_2.Geoname WHERE Lineas.Tension>0 AND Lineas.Tension<1000')
    #convierto el cursor en array
    lineas = tuple(cursor)
    cursor.close()
    for i in range (0, len(lineas)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(30 + 10 * int(i/len(lineas)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #salteo las lineas de bt de cts sin trafos:
        if not lineas[i][1] in cts_sin_trafo and not lineas[i][2] in cts_sin_trafo:
            #0 Geoname
            #1 Desde
            #2 Hasta
            #3 Tension
            #4 Longitud
            #5 elmt
            #6 Acometida
            #7 Obj
            #8 Instalacion
            #9 Expediente
            #10 UUCC
            #11 Alimentador
            #12 Descripcion
            #13 Tipo
            #14 Disposicion
            #15 Fase
            #16 Material_Fase
            #17 Seccion_Fase
            #18 Neutro
            #19 Material_Neutro
            #20 Seccion_Neutro
            #21 Subconductores
            #22 Material_AL
            #23 Seccion_AL
            #24 tensionmt
            #25 ssee
            #26 alimmt
            #27 ct
            longitud = lineas[i][4]
            if longitud==0:
                longitud=1
            #Id,ID_Nodo Inicial,ID_Nodo Final,Nivel de Tensión,Longitud
            str_linea = str(lineas[i][0]) + ',' + str(lineas[i][1]) + ',' + str(lineas[i][2]) + ',' + str(lineas[i][5])
            if lineas[i][17]==None:
                CT = 'CT'
            else:
                CT = lineas[i][27]
            str_linea = str_linea + ',' + str(lineas[i][24]) + '-' + str(lineas[i][25]).replace('-','') + '-' + lineas[i][26].replace('-','') + ',' + str(lineas[i][3]) + '-' + CT.replace('-','') + '-' + CT.replace('-','') + ',' + str(lineas[i][3])
            str_linea = str_linea + ',' + str(longitud) + ','
            str_polilinea = lineas[i][7].replace('LINESTRING (','').replace(')','')
            coordenadas = str_polilinea.split(', ')
            for coordenada in coordenadas:
                x, y = coordenada.split(' ')
                coords = convertir_coordenadas(self, x, y, srid, 4326)

                str_linea = str_linea + str(coords[1]) + ';' + str(coords[0]) + ';'

                #,Fecha Instalación,Nro Acto Administrativo según Res 477/00,Tipo de Línea,Disposición
            str_linea = str_linea[:-1] + ',' + lineas[i][8].strftime('%Y-%m-%d').replace("'","")
            if lineas[i][9]==None:
                str_linea = str_linea + ',1111/2001'
            elif lineas[i][9] == '00000/2001':
                str_linea = str_linea + ',1111/2001'
            elif lineas[i][9] == '00000/2000':
                str_linea = str_linea + ',1111/2001'
            else:
                str_linea = str_linea + ',' + lineas[i][9]
            if lineas[i][6]==1:
                str_linea = str_linea + ',' + 'Acometida,,'
            else:
                if lineas[i][13]=='A':
                    str_linea = str_linea + ',' + 'Aerea Convencional'
                    if lineas[i][14]==None:
                        str_linea = str_linea + ',' + 'Horizontal,'
                    elif lineas[i][14]=='Horizontal' or lineas[i][14]=='Vertical' or lineas[i][14]=='Triangular':
                        str_linea = str_linea + ',' + lineas[i][14] + ','
                    else:
                        str_linea = str_linea + ',' + 'Horizontal,'
                if lineas[i][13]=='S':
                    str_linea = str_linea + ',' + 'Subterranea'
                    if lineas[i][13].find('3x')>-1 and lineas[i][13].find('+')>-1:
                        str_linea = str_linea + ',,Tetrapolar'
                    elif lineas[i][13].find('3x')>-1:
                        str_linea = str_linea + ',,Tripolar'
                    else:
                        str_linea = str_linea + ',,Unipolar'
                if lineas[i][13]=='P':
                    str_linea = str_linea + ',' + 'Aerea Preensamblado,,'
            str_linea = str_linea + ',' + lineas[i][10].replace(',', '') + ',' #La ultima coma es por un campo de reserva
            if lineas[i][22]==None:
                str_linea = str_linea + ',' + 'Distribucion'
            elif lineas[i][22]=='N':
                str_linea = str_linea + ',' + 'Distribucion'
            else:
                str_linea = str_linea + ',' + 'Mixto'
            str_fase = lineas[i][15]
            str_fase = str_fase.replace('1', 'R')
            str_fase = str_fase.replace('2', 'S')
            str_fase = str_fase.replace('3', 'T')
            str_linea = str_linea + ',' + str_fase
            if lineas[i][16]=='Cu':
                str_linea = str_linea + ',' + 'Cobre'
            elif lineas[i][16]=='Al':
                str_linea = str_linea + ',' + 'Aluminio'
            elif lineas[i][16]=='Al/Al':
                str_linea = str_linea + ',' + 'Aleacion de Aluminio'
            elif lineas[i][16]=='Ac':
                str_linea = str_linea + ',' + 'Acero'
            elif lineas[i][16]=='Al/Ac':
                str_linea = str_linea + ',' + 'Aluminio / Acero'
            elif lineas[i][16]=='AcZn':
                str_linea = str_linea + ',' + 'Acero Recubierto Zn'
            elif lineas[i][16]=='AcCu':
                str_linea = str_linea + ',' + 'Acero Recubierto Cu'
            elif lineas[i][16]=='AcAl':
                str_linea = str_linea + ',' + 'Acero Recubierto Al'
            else:
                str_linea = str_linea + ',' + 'Aleacion de Aluminio'
            str_linea = str_linea + ',' + str(lineas[i][17])
            if lineas[i][21]==None:
                str_linea = str_linea + ',1'
            elif  lineas[i][21]=='':
                str_linea = str_linea + ',1'
            else:
                str_linea = str_linea + ',' + lineas[i][21]
            if lineas[i][18]==None:
                str_linea = str_linea + ',' + 'N,,'
            elif lineas[i][18]=='0':
                str_linea = str_linea + ',' + 'N,,'
            else:
                str_linea = str_linea + ',' + 'S'
                if lineas[i][19]=='Cu':
                    str_linea = str_linea + ',' + 'Cobre'
                elif lineas[i][19]=='Al':
                    str_linea = str_linea + ',' + 'Aluminio'
                elif lineas[i][19]=='Al/Al':
                    str_linea = str_linea + ',' + 'Aleacion de Aluminio'
                elif lineas[i][19]=='Ac':
                    str_linea = str_linea + ',' + 'Acero'
                elif lineas[i][19]=='Al/Ac':
                    str_linea = str_linea + ',' + 'Aluminio / Acero'
                else:
                    str_linea = str_linea + ',' + 'Aleacion de Aluminio'
                str_linea = str_linea + "," + str(lineas[i][20])
            #Hilo de Guardia en BT:
            str_linea = str_linea + ',N,'
            if lineas[i][22]==None:
                str_linea = str_linea + ',N,,'
            elif lineas[i][22]=='N':
                str_linea = str_linea + ',N,,'
            else:
                str_linea = str_linea + ',S'
                if lineas[i][22]=='Cu':
                    str_linea = str_linea + ',' + 'Cobre'
                elif lineas[i][22]=='Al':
                    str_linea = str_linea + ',' + 'Aluminio'
                elif lineas[i][22]=='Al/Al':
                    str_linea = str_linea + ',' + 'Aleacion de Aluminio'
                elif lineas[i][22]=='Ac':
                    str_linea = str_linea + ',' + 'Acero'
                elif lineas[i][22]=='Al/Ac':
                    str_linea = str_linea + ',' + 'Aluminio / Acero'
                else:
                    str_linea = str_linea + ',' + 'Aleacion de Aluminio'

                if lineas[i][23]==None:
                    str_linea = str_linea + ',25'
                else:
                    str_linea = str_linea + ',' + str(lineas[i][23])
            s_urbana = 0
            for n in range (0, len(alimentadores)):
                if lineas[i][11]==alimentadores[n][0]:
                    if alimentadores[n][2]==0:
                        s_urbana = 0
                    else:
                        s_urbana = 100 * round(alimentadores[n][1]/(alimentadores[n][1]+alimentadores[n][2]))
                    break
            s_rural = 100 - s_urbana
            str_linea = str_linea + ',' + 'URBANO:' + str(s_urbana) + ';RURAL:' + str(s_rural)

            b_existe = False
            for n in range (0, len(postes)):
                if postes[n][0]==lineas[i][0]:
                    j=n
                    b_existe = True
                    break
            if b_existe==False:
                str_linea = str_linea + ',Ninguno,'
            else:
                if postes[j][1]=='Mensula': #Podrían ser también : Grampa o Portico
                    str_linea = str_linea + ',Mensula,'
                else:
                    str_linea = str_linea + ',Poste,Resumida:'
                    #material,aislacion,fundacion,ternas,comparte,estructura,cantidad_predominantes,cantidad_especiales
                    str_linea = str_linea + postes[j][2].replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
                    if postes[j][3]=='':
                        postes[j][3]='Suspension'
                    str_linea = str_linea + '-' + postes[j][3].replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
                    if postes[j][4]=='1':
                        str_linea = str_linea + '-S'
                    else:
                        str_linea = str_linea + '-N'
                    if postes[j][5]=='Simple Terna':
                        str_linea = str_linea + '-0'
                    elif postes[j][5]=='2 Ternas':
                        str_linea = str_linea + '-1'
                    elif postes[j][5]=='3 Ternas':
                        str_linea = str_linea + '-2'
                    elif postes[j][5]=='4 Ternas':
                        str_linea = str_linea + '-3'
                    elif postes[j][5]=='Alumbrado':
                        str_linea = str_linea + '-A'
                    else:
                        str_linea = str_linea + '-0'
                    if postes[j][6]=='No':
                        str_linea = str_linea + '-N'
                    else:
                        str_linea = str_linea + '-S'
                    str_linea = str_linea + '-' + str(postes[j][8])
                    str_linea = str_linea + '-' + str(postes[j][9])
            f.writelines(str_linea + '\n')
    f.close()
    #----------------------------------------------------------------------------
    progress.setValue(40)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    str_archivo = 'c:/gis/energis6/DPE/elementos.txt'
    f = open(str_archivo,'w')
    progress.setWindowTitle('Exportando Fuentes ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Geoname, Nombre, Descripcion AS SSEE, Tension, Val4 AS Datos, UUCC, Modificacion FROM Nodos WHERE Elmt=1 AND Tension>=1000')
    #convierto el cursor en array
    fuentes = tuple(cursor)
    cursor.close()
    for i in range (0, len(fuentes)):
        #0 Geoname
        #1 Nombre
        #2 SSEE
        #3 Tension
        #4 Datos
        #5 UUCC
        #6 Modificacion
        str_expediente = '1111/2001'
        if fuentes[i][4]!='':
            datos = fuentes[i][4].split('|')
            if datos[1] == '00000/2001':
                str_expediente = '1111/2001'
            elif datos[1] == '00000/2000':
                str_expediente = '1111/2001'
            else:
                str_expediente = datos[1]
        str_linea = 'FUENTE,' + str(1000000000 + fuentes[i][0]) + ',' + str(fuentes[i][0]) + ',Fuente' + str(fuentes[i][0])
        str_linea = str_linea + ',Punto de Compra,' + fuentes[i][6].strftime('%Y-%m-%d').replace("'","") + ',' + str_expediente
        if fuentes[i][5]==None:
            str_linea = str_linea + ',,,,'
        else:
            str_linea = str_linea + ',' + fuentes[i][5].replace(',', '') + ',,,'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(43)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    cursor = conn.cursor()
    cursor.execute('SELECT Geoname, Nombre, Descripcion AS SSEE, Tension, Val4 AS Datos, UUCC, Modificacion, Val5 AS Tipo FROM Nodos WHERE Elmt=11 AND Tension>=1000')
    #convierto el cursor en array
    generadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(generadores)):
        #0 Geoname
        #1 Nombre
        #2 SSEE
        #3 Tension
        #4 Datos
        #5 UUCC
        #6 Modificacion
        #7 Tipo
        str_expediente = '1111/2001'
        str_clase = 'Combustion Interna'
        str_potencia = '0'
        if generadores[i][4]!='':
            datos = generadores[i][4].split('|')
            if len(datos)>=3:
                str_expediente = datos[1]
                if datos[1] == '00000/2001':
                    str_expediente = '1111/2001'
                elif datos[1] == '00000/2000':
                    str_expediente = '1111/2001'
                else:
                    str_expediente = datos[1]
                str_potencia = str(datos[2])
        str_clase = generadores[i][7]
        str_linea = 'FUENTE,' + str(1000000000 + generadores[i][0]) + ',' + str(generadores[i][0]) + ',Fuente' + str(generadores[i][0])
        str_linea = str_linea + ',Generacion,' + generadores[i][6].strftime('%Y-%m-%d').replace("'","") + ',' + str_expediente + ',' + generadores[i][5].replace(',', '') + ',,' + str_clase + ',' + str_potencia
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(45)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Trafos ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Nodos.Geoname, Max(Nodos.Modificacion) AS Modificacion, Max(Ct.Exp) AS Exp, Nodos.Tension, Max(Transformadores.Tension_1) AS Tension_1, Max(Transformadores.Tension_2) AS Tension_2, Max(Transformadores.Conexionado) AS Conexionado, Max(Transformadores.Tipo) AS Tipo, Sum(Transformadores.Potencia) AS Potencia, Max(Transformadores.id_trafo) AS id_trafo, Max(Nodos.Aux) AS Aux, Max(Nodos.UUCC) AS UUCC, Max([X1]*100) AS xcc, Sum(Transformadores_Parametros.[P01]) AS perdidas, Max([Tap1]-100) AS Tap FROM ((Ct INNER JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct) INNER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre) LEFT JOIN Transformadores_Parametros ON Transformadores.Id_trafo = Transformadores_Parametros.Id_Trafo GROUP BY Nodos.Geoname, Nodos.Tension, Nodos.Elmt HAVING Nodos.Tension>1000 AND Nodos.Elmt=4')
    #convierto el cursor en array
    transformadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(transformadores)):
        #0 Geoname
        #1 Modificacion
        #2 Exp
        #3 Tension
        #4 Tension_1
        #5 Tension_2
        #6 Conexionado
        #7 Tipo
        #8 Potencia
        #9 id_trafo
        #10 Aux
        #11 UUCC
        #12 xcc
        #13 perdidas
        #14 Tap
        if transformadores[i][2]!=None:
            if transformadores[i][2] == '00000/2001':
                str_expediente = '1111/2001'
            elif transformadores[i][2] == '00000/2000':
                str_expediente = '1111/2001'
            else:
                str_expediente = transformadores[i][2]
        uucc = ''
        if transformadores[i][11]!=None:
            uucc = transformadores[i][11].replace(',','.')
        str_linea = 'TRANSFORMADOR,' + str(1000000000 + transformadores[i][0]) + ',' + str(transformadores[i][0]).replace(',','.') + ',' + str(transformadores[i][9]) + ',' + uucc + ',,' + transformadores[i][1].strftime('%Y-%m-%d').replace("'","") + ',' + str_expediente

        if transformadores[i][4] > 50000 or transformadores[i][5] > 50000:
            str_linea = str_linea + ',Distribucion Primaria'
        else:
            str_linea = str_linea + ',Distribucion Secundaria'
        #cantidad_usuarios
        cursor = conn.cursor()
        cursor.execute('SELECT Count(Usuarios.id_usuario) AS CuentaDeid_usuario FROM (Usuarios INNER JOIN Suministros ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Suministros_Trafos ON Suministros.id_nodo = Suministros_Trafos.Geoname_s WHERE Suministros_Trafos.Geoname_t=' + str(transformadores[i][0]) + ' AND ES=1')
        #convierto el cursor en array
        cant_usuarios = tuple(cursor)
        cursor.close()
        if cant_usuarios[0][0]:
            str_linea = str_linea + ',0'
        else:
            str_linea = str_linea + ',' + str(cant_usuarios[0][0])
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(transformadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',N,' #Banco de Transformacion, Formacion del Banco
        str_linea = str_linea + ',' + str(transformadores[i][8])
        str_tension1 = str(int(transformadores[i][4]))
        str_tension2 = str(int(transformadores[i][5]))
        #220000/132000/13200,220000/132000,132000/33000/13200, 132000/66000, 132000/33000, 132000/13200, 66000/33000/13200, 66000/33000, 66000/13200, 33000/13200, 33000/400, 13200/400, 33000/6600, 13200/6600, 6600/400
        if transformadores[i][4] > transformadores[i][5]:
            str_linea = str_linea + ',' + str_tension1 + '/' + str_tension2
        else:
            str_linea = str_linea + ',' + str_tension2 + '/' + str_tension1
        str_linea = str_linea + ',S' #Regulador de Tension Primario
        str_linea = str_linea + ',N' #Regulador de Tension Bajo Carga
        str_linea = str_linea + ',5' #Tap Max
        str_linea = str_linea + ',-5' #Tap Min
        str_linea = str_linea + ',2.5' #Paso Tap
        str_linea = str_linea + ',0' #Posicion Tap
        str_linea = str_linea + ',En Servicio'
        if transformadores[i][4] > 1000 and transformadores[i][5] > 1000:
            str_linea = str_linea + ',N'
            str_linea = str_linea + ',' + str(transformadores[i][8])
            str_linea = str_linea + ',0'
            str_linea = str_linea + ',' + transformadores[i][6]
            str_linea = str_linea + ',N,N,,,,' #Regulador Tensión Secundario
            str_linea = str_linea + ',' + str(transformadores[i][12]) + ',0,0' #Ucc
            if transformadores[i][13]==None:
                str_linea = str_linea + ',' + str(18.276 * transformadores[i][8] ^ 0.689) + ',ONAN'
            else:
                str_linea = str_linea + ',' + str(transformadores[i][13]) + ',ONAN'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(50)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Aparatos de Maniobra ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Geoname, UUCC, Modificacion, elmt, Val1 AS Tipo, Val2 AS Datos, Val5 AS Poder_Corte, Val3 AS Telecomando FROM Nodos WHERE (elmt=2 OR elmt=3) AND Tension>=1000')
    #convierto el cursor en array
    seccionadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(seccionadores)):
        str_linea = 'SWITCH,' + str(1000000000 + seccionadores[i][0]) + ',' + str(seccionadores[i][0]) + ',Sec' + str(seccionadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        #0 Geoname
        #1 UUCC
        #2 Modificacion
        #3 elmt
        #4 Tipo
        #5 Datos
        #6 Poder_Corte
        #7 Telecomando
        if seccionadores[i][1]==None:
            str_linea = str_linea + ',,'
        else:
            str_linea = str_linea + ',' + seccionadores[i][1].replace(',', '') + ','
        str_linea = str_linea + ',' + seccionadores[i][2].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, Celdas.
        if seccionadores[i][3]==2:
            str_linea = str_linea + ',C'
        else:
            str_linea = str_linea + ',A'
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(seccionadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        if seccionadores[i][4]==None:
            str_linea = str_linea + ',Seccionador'
        elif seccionadores[i][4]=='Seccionador':
            str_linea = str_linea + ',' + seccionadores[i][4]
        elif seccionadores[i][4]=='Reconectador':
            str_linea = str_linea + ',' + seccionadores[i][4]
        elif seccionadores[i][4]=='Interruptor':
            str_linea = str_linea + ',' + seccionadores[i][4]
        elif seccionadores[i][4]=='Seccionalizador' :
            str_linea = str_linea + ',' + seccionadores[i][4]
        elif seccionadores[i][4]=='Fusible':
            str_linea = str_linea + ',' + seccionadores[i][4]
        else:
            str_linea = str_linea + ',Seccionador'
        #Corriente
        if seccionadores[i][4]=='Interruptor':
            corriente = 630
        elif seccionadores[i][4]=='Reconectador':
            corriente = 400
        elif seccionadores[i][4]=='Seccionador':
            corriente = 16
            if seccionadores[i][5]!=None:
                modelo = seccionadores[i][5][:15].strip()
                if modelo=='APR':
                    corriente = 160
                if modelo=='Bornera Secc.':
                    corriente = 10
        elif seccionadores[i][4]=='Seccionalizador':
            corriente = 63
        elif seccionadores[i][4]=='Fusible':
            corriente = 25
        if seccionadores[i][5]!=None and seccionadores[i][5]!='':
            corriente = seccionadores[i][5][16:21].strip()
        str_linea = str_linea + ',' + str(corriente)
        #Poder de Corte
        if seccionadores[i][6]!=None and seccionadores[i][6]!='':
            str_linea = str_linea + ',' + seccionadores[i][6]
        else:
            str_linea = str_linea + ',0'
        if seccionadores[i][4]=='Interruptor':
            modelo = seccionadores[i][5][:15].strip()
            if modelo=='':
                str_linea = str_linea + ',DE POTENCIA'
            else:
                str_linea = str_linea + ',' + modelo
            tecnologia = seccionadores[i][5][21:36].strip()
            if tecnologia=='':
                str_linea = str_linea + ',SF6'
            else:
                str_linea = str_linea + ',' + tecnologia
            rele = seccionadores[i][5][-15:].strip()
            if rele=='Con Prot Relé':
                str_linea = str_linea + ',S'
            else:
                str_linea = str_linea + ',N'
        elif seccionadores[i][4]=='Seccionador':
            modelo = seccionadores[i][5][:15].strip()
            if modelo=='Bornera Secc.':
                str_linea = str_linea + ',Bornera Seccionable'
            elif modelo=='Cuch Giratorias':
                str_linea = str_linea + ',Cuchillas Giratorias'
            elif modelo=='Cuch Deslizante':
                str_linea = str_linea + ',Cuchilla Deslizante'
            elif modelo=='Col Giratoria':
                str_linea = str_linea + ',Columna Giratoria'
            else:
                str_linea = str_linea + ',' + modelo
            tecnologia = seccionadores[i][5][21:36].strip()
            if tecnologia=='':
                str_linea = str_linea + ',Otro'
            else:
                str_linea = str_linea + ',' + tecnologia
            pat = seccionadores[i][5][-15:].strip()
            if pat=='Con P.A.T.':
                str_linea = str_linea + ',S'
            else:
                str_linea = str_linea + ',N'
        elif seccionadores[i][4]=='Fusible':
            modelo = 'Otro'
            if seccionadores[i][5]!=None and seccionadores[i][5]!='':
                if seccionadores[i][5][:15].strip()!='':
                    modelo = seccionadores[i][5][:15].strip()
                    if modelo=='HH':
                        corriente = 63
                    if modelo=='NH':
                        corriente = 63
                    if modelo=='DIAZED':
                        corriente = 63
                    if modelo=='NEOZED':
                        corriente = 25
            str_linea = str_linea + ',' + modelo
        #Telecomandado:
        if seccionadores[i][7]!=None:
            if seccionadores[i][7]=='EQ13-TELC':
                str_linea = str_linea + ',S'
            else:
                str_linea = str_linea + ',N'
        else:
            str_linea = str_linea + ',N'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(55)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Capacitores ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Geoname, UUCC, Modificacion, Val1 AS PR, Val2 AS PS, Val3 AS PT FROM Nodos WHERE elmt=5 AND Tension>=1000')
    #convierto el cursor en array
    capacitores = tuple(cursor)
    cursor.close()
    for i in range (0, len(capacitores)):
        str_linea = 'CAPACITOR,' + str(1000000000 + capacitores[i][0]) + ',' + str(capacitores[i][0]) + ',Cap' + str(capacitores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + capacitores[i][1].replace(',', '') + ','
        str_linea = str_linea + ',' + capacitores[i][2].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, Celdas.
        #0 Geoname
        #1 UUCC
        #2 Modificacion
        #3 PR
        #4 PS
        #5 PT
        str_fase = ''
        str_potencia = '0'
        if capacitores[i][3]!=None:
            if capacitores[i][3].isnumeric()==True:
                str_fase = 'R'
                str_potencia = str_potencia + capacitores[i][3]
        if capacitores[i][4]!=None:
            str_fase = str_fase + 'S'
            if capacitores[i][4].isnumeric()==True:
                str_fase = 'S'
                str_potencia = str_potencia + capacitores[i][4]
        if capacitores[i][4]!=None:
            str_fase = str_fase + 'T'
            if capacitores[i][5].isnumeric()==True:
                str_fase = 'T'
                str_potencia = str_potencia + capacitores[i][5]
        str_linea = str_linea + ',' + str_fase + ',' + str_potencia
        str_linea = str_linea + ',AUTOMATICO,PARALELO'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(57)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Reguladores ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Geoname, UUCC, Modificacion, Val1 AS Potencia, Val2 AS Min, Val3 AS Max, Val4 AS Paso FROM Nodos WHERE elmt=9 AND Tension>=1000')
    #convierto el cursor en array
    reguladores = tuple(cursor)
    cursor.close()
    for i in range (0, len(reguladores)):
        #0 Geoname
        #1 UUCC
        #2 Modificacion
        #3 Potencia
        #4 Min
        #5 Max
        #6 Paso
        str_linea = 'REGULADOR,' + str(1000000000 + reguladores[0][0]) + ',' + str(reguladores[0][0]) + ',Reg' + str(reguladores[0][0])
        if reguladores[i][1]==None:
            str_linea = str_linea + ',,'
        else:
            str_linea = str_linea + ',' + reguladores[i][1].replace(',', '') + ','
        str_linea = str_linea + ',' + reguladores[i][2].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(reguladores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_potencia = 100
        if reguladores[i][3]!=None:
            if reguladores[i][3].isnumeric()==True:
                str_potencia = reguladores[i][3]
        str_linea = str_linea + ',' + str_fase + ',' + str_potencia
        str_linea = str_linea + ',AUTOMATICO'
        if reguladores[i][5]!=None:
            if reguladores[i][5].isnumeric()==True:
                str_linea = str_linea + ',' + reguladores[i][5] #Tap Max
            else:
                str_linea = str_linea + ',16'
        if reguladores[i][4]!=None:
            if reguladores[i][4].isnumeric()==True:
                str_linea = str_linea + ',' + reguladores[i][4] #Tap Min
            else:
                str_linea = str_linea + ',-16'
        if reguladores[i][6]!=None:
            if reguladores[i][6].isnumeric()==True:
                str_linea = str_linea + ',' + reguladores[i][6] #Paso Tap
            else:
                str_linea = str_linea + ',1'
        str_linea = str_linea + ',0' #Posicion Tap
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(60)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando TI - TV ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Usuarios.id_usuario, Nodos.Geoname, Nodos.UUCC, Nodos.Modificacion, Bloques.montaje, Bloques.combinado, Nodos.Tension, Bloques.i1, Bloques.i2, Bloques.funcioni, Bloques.tecnologiai, Bloques.v1, Bloques.v2, Bloques.funcionv, Bloques.tecnologiav FROM (Usuarios INNER JOIN (Nodos INNER JOIN Suministros ON Nodos.Geoname = Suministros.id_nodo) ON Usuarios.id_suministro = Suministros.id_suministro) INNER JOIN Bloques ON Usuarios.id_usuario = Bloques.id_usuario')
    #convierto el cursor en array
    bloques = tuple(cursor)
    cursor.close()
    for i in range (0, len(bloques)):
        #0 id_usuario
        #1 Geoname
        #2 UUCC
        #3 Modificacion
        #4 montaje
        #5 combinado
        #6 Tension
        #7 i1
        #8 i2
        #9 funcioni
        #10 tecnologiai
        #11 v1
        #12 v2
        #13 funcionv
        #14 tecnologiav
        if (bloques[i][7] > 0 and bloques[i][8] > 0) or (bloques[i][11] > 0 and bloques[i][12] > 0):
            str_linea = 'TI_TV,' + str(1000000000 + bloques[i][1]) + ',' + str(bloques[i][1]) + ',Me' + str(bloques[i][1])
            str_linea = str_linea + ',' #Maestro Envolvente (no hay)
            if bloques[i][2]==None:
                str_linea = str_linea + ',,'
            else:
                str_linea = str_linea + ',' + bloques[i][2].replace(',', '') + ','
            str_linea = str_linea + ',' + bloques[i][3].strftime('%Y-%m-%d').replace("'","")
            str_linea = str_linea + ',' + bloques[i][4]
            if bloques[i][5]==1:
                str_linea = str_linea + ',S'
            else:
                str_linea = str_linea + ',N'

            str_linea = str_linea + ',' + str(bloques[i][6])
            #fase
            cursor = conn.cursor()
            cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(bloques[i][0]))
            #convierto el cursor en array
            fases = tuple(cursor)
            cursor.close()
            str_fase = str(fases[0][0])
            str_fase = str_fase.replace('1', 'R')
            str_fase = str_fase.replace('2', 'S')
            str_fase = str_fase.replace('3', 'T')
            if bloques[i][7] > 0 and bloques[i][8] > 0:
                str_linea = str_linea + ',S,' + str_fase
                str_linea = str_linea + ',' + str(bloques[i][7])
                str_linea = str_linea + ',' + str(bloques[i][8])
                str_linea = str_linea + ',' + bloques[i][9]
                str_linea = str_linea + ',' + bloques[i][10]
            else:
                str_linea = str_linea + ',N,,,,,'
            if bloques[i][11] > 0 and bloques[i][12] > 0:
                str_linea = str_linea + ',S,' + str_fase
                str_linea = str_linea + ',' + str(bloques[i][11])
                str_linea = str_linea + ',' + str(bloques[i][12])
                str_linea = str_linea + ',' + bloques[i][13]
                str_linea = str_linea + ',' + bloques[i][14]
            else:
                str_linea = str_linea + ',N,,,,,'
            f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(63)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Descargadores ...')
    #13,2kV
    cursor = conn.cursor()
    cursor.execute("SELECT Postes.Id_nodo AS Geoname, Postes.Descargadores, Nodos.Modificacion, 'EQ13-DESC' AS UUCC FROM Nodos INNER JOIN Postes ON Nodos.Geoname = Postes.Id_nodo WHERE Postes.Id_nodo<>0 AND Postes.Descargadores>0 AND Postes.Tension=13200")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Descargadores
        #2 Modificacion
        #3 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeP' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][3].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][2].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',15000,15300,10'
        f.writelines(str_linea + '\n')
    #33kV
    cursor = conn.cursor()
    cursor.execute("SELECT Postes.Id_nodo AS Geoname, Postes.Descargadores, Nodos.Modificacion, 'EQ33-DESC' AS UUCC FROM Nodos INNER JOIN Postes ON Nodos.Geoname = Postes.Id_nodo WHERE Postes.Id_nodo<>0 AND Postes.Descargadores>0 AND Postes.Tension=33000")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Descargadores
        #2 Modificacion
        #3 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeP' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][3].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][2].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',42000,22000,10'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(65)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    #Descargadores de cables
    #13,2kV
    cursor = conn.cursor()
    cursor.execute("SELECT Nodos.Geoname, Nodos.Modificacion, 'EQ13-DESC' AS UUCC FROM Nodos WHERE (Nodos.Elmt=2 Or Nodos.Elmt=3) AND Nodos.Val4='Aereo-Subt' AND Tension=13200")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Modificacion
        #2 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeC' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][2].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][1].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',15000,15300,10'
        f.writelines(str_linea + '\n')
    #33kV
    cursor = conn.cursor()
    cursor.execute("SELECT Nodos.Geoname, Nodos.Modificacion, 'EQ33-DESC' AS UUCC FROM Nodos WHERE (Nodos.Elmt=2 Or Nodos.Elmt=3) AND Nodos.Val4='Aereo-Subt' AND Tension=33000")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Modificacion
        #2 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeC' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][2].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][1].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',42000,22000,10'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(67)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    #Descargadores de cts
    #13,2kV
    cursor = conn.cursor()
    cursor.execute("SELECT Nodos.Geoname, Nodos.Modificacion, Ct.Descargadores, 'EQ13-DESC' AS UUCC FROM Ct INNER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre WHERE Ct.Descargadores=1 AND Nodos.Tension=13200 AND Nodos.Elmt=4")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Modificacion
        #2 Descargadores
        #3 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeC' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][3].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][1].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',15000,15300,10'
        f.writelines(str_linea + '\n')
    #33kV
    cursor = conn.cursor()
    cursor.execute("SELECT Nodos.Geoname, Nodos.Modificacion, Ct.Descargadores, 'EQ33-DESC' AS UUCC FROM Ct INNER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre WHERE Ct.Descargadores=1 AND Nodos.Tension=33000 AND Nodos.Elmt=4")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Modificacion
        #2 Descargadores
        #3 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeC' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][3].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][1].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',42000,22000,10'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(70)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    #Descargadores de reguladores
    #13,2kV
    cursor = conn.cursor()
    cursor.execute("SELECT Geoname, Modificacion, Val5 AS Descargadores, 'EQ13-DESC' AS UUCC FROM Nodos WHERE Val5<>'0' AND Nodos.Tension=13200 AND Elmt=9")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Modificacion
        #2 Descargadores
        #3 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeC' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][3].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][1].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',15000,15300,10'
        f.writelines(str_linea + '\n')
    #33kV
    cursor = conn.cursor()
    cursor.execute("SELECT Geoname, Modificacion, Val5 AS Descargadores, 'EQ33-DESC' AS UUCC FROM Nodos WHERE Val5<>'0' AND Tension=33000 AND Elmt=9")
    #convierto el cursor en array
    descargadores = tuple(cursor)
    cursor.close()
    for i in range (0, len(descargadores)):
        #0 Geoname
        #1 Modificacion
        #2 Descargadores
        #3 UUCC
        str_linea = 'DESCARGADOR,' + str(2000000000 + descargadores[i][0]) + ',' + str(descargadores[i][0]) + ',DeC' + str(descargadores[i][0])
        str_linea = str_linea + ',' #Maestro Envolvente (no hay)
        str_linea = str_linea + ',' + descargadores[i][3].replace(',', '') + ','
        str_linea = str_linea + ',' + descargadores[i][1].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',Intemperie' #Interior, GIS, Celda
        #fase
        cursor = conn.cursor()
        cursor.execute('SELECT fases FROM mNodos WHERE geoname=' + str(descargadores[i][0]))
        #convierto el cursor en array
        fases = tuple(cursor)
        cursor.close()
        str_fase = str(fases[0][0])
        str_fase = str_fase.replace('1', 'R')
        str_fase = str_fase.replace('2', 'S')
        str_fase = str_fase.replace('3', 'T')
        str_linea = str_linea + ',' + str_fase
        str_linea = str_linea + ',42000,22000,10'
        f.writelines(str_linea + '\n')
    #----------------------------------------------------------------------------
    progress.setValue(73)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Suministros ...')
    cursor = conn.cursor()
    cursor.execute('SELECT iid FROM iid')
    #convierto el cursor en array
    iid = tuple(cursor)
    cursor.close()
    k = iid[0][0]
    cursor = conn.cursor()
    cursor.execute("SELECT Nodos.Geoname, Suministros.id_suministro, Min(VW_CCDATOSCOMERCIALES.Calle) AS Calle, Min(VW_CCDATOSCOMERCIALES.Numero) AS Numero, Min(VW_CCDATOSCOMERCIALES.Localidad) AS Localidad, Min(VW_CCDATOSCOMERCIALES.Partido) AS Partido, Max(VW_CCDATOSCOMERCIALES.Tension_Suministro) AS Tension_Suministro, Nodos.Tension AS Tension_Nodo, Min(VW_CCDATOSCOMERCIALES.Fecha_Alta) AS Fecha_Alta, '' AS Fecha_Baja, MIN(Spurs.nodo) AS spur, MAX(VW_CCDATOSCOMERCIALES.Tarifa) AS Tarifa FROM (Nodos INNER JOIN (VW_CCDATOSCOMERCIALES INNER JOIN (Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro) ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario) ON Nodos.Geoname = Suministros.id_nodo) LEFT JOIN Spurs ON Nodos.Geoname = Spurs.Nodo WHERE Nodos.Elmt=6 GROUP BY Nodos.Geoname, Suministros.id_suministro, Nodos.Tension")
    #convierto el cursor en array
    suministros = tuple(cursor)
    cursor.close()
    for i in range (0, len(suministros)):
        #0 Geoname
        #1 id_suministro
        #2 Calle
        #3 Numero
        #4 Localidad
        #5 Partido
        #6 Tension_Suministro
        #7 Tension_Nodo
        #8 Fecha_Alta
        #9 Fecha_Baja
        #10 Spur
        #11 Tarifa
        if suministros[i][11]!=None:
            k = k + 1
            str_linea = 'SUMINISTRO ,' + str(1000000000 + k) + ',' +  str(suministros[i][0]) + ',' +  str(suministros[i][1])
            str_calle = 'SD'
            str_numero = '0'
            str_localidad = 'SD'
            str_partido = 'SD'
            if suministros[i][2]!=None:
                str_calle = suministros[i][2][:50].replace(',', '')
            if suministros[i][3]!=None:
                str_numero = suministros[i][3]
            if str_numero=='':
                str_numero = '0'
            if str_numero.isnumeric()==False:
                str_numero = '0'
            if suministros[i][4]!=None:
                str_localidad = suministros[i][4]
            if suministros[i][5]!=None:
                str_localidad = suministros[i][5]
            if str_localidad=='':
                    str_localidad = 'SD'
            if str_partido=='':
                str_partido = 'SD'
            str_linea = str_linea + ',' + str_calle
            str_linea = str_linea + ',' + str_numero
            str_linea = str_linea + ',' + str_localidad
            str_linea = str_linea + ',' + str_partido
            str_tension = '231'
            if int(suministros[i][6]) >= 231:
                str_tension = '400'
            if int(suministros[i][6]) > 400:
                str_tension = '6600'
            if int(suministros[i][6]) >= 6600:
                str_tension = '7620'
            if int(suministros[i][6]) >= 13200:
                str_tension = '13200'
            if int(suministros[i][6]) >= 19000:
                str_tension = '19000'
            if int(suministros[i][6]) >= 33000:
                str_tension = '33000'
            if int(suministros[i][6]) >= 66000:
                str_tension = '66000'
            if int(suministros[i][6]) >= 132000:
                str_tension = '132000'
            str_linea = str_linea + ',' + str_tension
            str_linea = str_linea + ',' + suministros[i][8].strftime('%Y-%m-%d').replace("'","")
            if suministros[i][9]==None:
                str_linea = str_linea + ','
            elif suministros[i][9]=='':
                str_linea = str_linea + ','
            else:
                str_linea = str_linea + ',' + suministros[i][9].strftime('%Y-%m-%d').replace("'","")
            str_linea = str_linea + ','
            uucc = ''
            if int(suministros[i][6]) <= 300:
                if suministros[i][5][:2]=='T1' or suministros[i][5][:2]=='T4':
                    uucc = 'ABMPE-T1-2X10-CU'
            if int(suministros[i][6]) <= 1000:
                if suministros[i][5][:2]=='T1' or suministros[i][5][:2]=='T4':
                    uucc = 'ABTPE-T1-4X10-CU'
                if suministros[i][5][:2]=='T2':
                    uucc = 'ABTPE-T2-4X16-CU'
                if suministros[i][5][:2]=='T3':
                    uucc = 'ACBTCS-T3-3X70/35-CU'
            else:
                if suministros[i][5][:2]=='T1' or suministros[i][5][:2]=='T4':
                    uucc = 'ABTPE-T1-4X10-CU'
                if suministros[i][5][:2]=='T2':
                    uucc = 'A13STCM-ST-35-CU'
                if suministros[i][5][:2]=='T3':
                    uucc = 'A13STCM-ST-35-CU'
            if suministros[i][10]==None:
                str_linea = str_linea + ',' + uucc + ','
            else:
                str_linea = str_linea + ',,'
            f.writelines(str_linea + '\n')
    f.close()
    #----------------------------------------------------------------------------
    progress.setValue(80)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    progress.setWindowTitle('Exportando Usuarios Comunes ...')
    cursor = conn.cursor()
    cursor.execute("UPDATE medidores SET tipo='Monotarifa' WHERE tipo IS NULL")
    cursor.execute("UPDATE Usuarios SET prosumidor = '' WHERE prosumidor='0' OR prosumidor='N'")
    conn.commit()
    str_archivo = 'c:/gis/energis6/DPE/usuarios.txt'
    f = open(str_archivo,'w')
    cursor = conn.cursor()
    cursor.execute("SELECT Suministros.id_suministro, Tarifas.id_oceba AS Tarifa, VW_CCDATOSCOMERCIALES.Tension_Suministro, VW_CCDATOSCOMERCIALES.Id_Usuario AS NIC, LEFT(VW_CCDATOSCOMERCIALES.Apellido COLLATE SQL_Latin1_General_CP1_CI_AS + ' ' + VW_CCDATOSCOMERCIALES.Nombre COLLATE SQL_Latin1_General_CP1_CI_AS, 80) AS Razon_Social, CASE WHEN ISNUMERIC(VW_CCDATOSCOMERCIALES.Piso) = 1 THEN VW_CCDATOSCOMERCIALES.Piso ELSE '' END AS Piso, CASE WHEN ISNUMERIC(VW_CCDATOSCOMERCIALES.Dto) = 1 THEN VW_CCDATOSCOMERCIALES.Dto ELSE '' END AS Dto, 'DNI' AS Tipo_Documento, VW_CCDATOSCOMERCIALES.DNI AS Nro_Documento, '<SD>' AS CIIU, VW_CCDATOSCOMERCIALES.Fecha_Alta, VW_CCDATOSCOMERCIALES.Fecha_Baja, Medidores.tipo, 'N' AS prosumidor FROM VW_CCDATOSCOMERCIALES INNER JOIN Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa LEFT OUTER JOIN Medidores ON Usuarios.id_usuario = Medidores.id_usuario WHERE Usuarios.prosumidor =''")
    #convierto el cursor en array
    usuarios = tuple(cursor)
    cursor.close()
    for i in range (0, len(usuarios)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(80 + 5 * int(i/len(usuarios)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #0 id_suministro
        #1 Tarifa
        #2 Tension_Suministro
        #3 NIC
        #4 Razon_Social
        #5 Piso
        #6 Dto
        #7 Tipo_Documento
        #8 Nro_Documento
        #9 CIIU
        #10 Fecha_Alta
        #11 Fecha_Baja
        #12 tipo
        #13 prosumidor
        if usuarios[i][11]==None or usuarios[i][11]=='':
            str_linea = usuarios[i][0].strip() + ',' + str(usuarios[i][3])
            str_linea = str_linea + ',' + usuarios[i][4].replace(',', '').strip()
            str_linea = str_linea + ',' + usuarios[i][5].strip()
            str_linea = str_linea + ',' + usuarios[i][6].strip()
            str_linea = str_linea + ',' + usuarios[i][7]
            str_linea = str_linea + ',' + usuarios[i][8].strip()
            str_linea = str_linea + ',' + usuarios[i][9]
            str_linea = str_linea + ',' + usuarios[i][10].strftime('%Y-%m-%d').replace("'","")
            if usuarios[i][11]==None or usuarios[i][11]=='':
                str_linea = str_linea + ','
            else:
                str_linea = str_linea + ',' + usuarios[i][11].strftime('%Y-%m-%d').replace("'","")
            if usuarios[i][1]=='T1AP':
                str_linea = str_linea + ',,'
            elif usuarios[i][1]=='T1GAC':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T1GBC':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T1R':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T4NR':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T4R':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T2BT':
                str_linea = str_linea + ',EQBT-MEDT2TF,'
            elif usuarios[i][1]=='T3BT':
                str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T2MT':
                str_linea = str_linea + ',EQMT-MEDT2TF,'
            elif usuarios[i][1]=='T3MT':
                str_linea = str_linea + ',EQMT-MEDT3TF,'
            elif usuarios[i][1]=='T5MT':
                str_linea = str_linea + ',EQMT-MEDT3TF,'
            elif usuarios[i][1]=='T5BT':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T6BT':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            else:
                str_linea = str_linea + ',,'
            if usuarios[i][12]==None:
                str_linea = str_linea + ',Monotarifa'
            elif usuarios[i][12]=='':
                str_linea = str_linea + ',Monotarifa'
            else:
                str_linea = str_linea + ',' + usuarios[i][12]
            str_linea = str_linea + ',N'
            f.writelines(str_linea + '\n')
    progress.setWindowTitle('Exportando Usuarios Prosumidores ...')
    cursor = conn.cursor()
    cursor.execute("SELECT Suministros.id_suministro, Tarifas.id_oceba AS Tarifa, VW_CCDATOSCOMERCIALES.Tension_Suministro, VW_CCDATOSCOMERCIALES.Id_Usuario AS NIC, LEFT(VW_CCDATOSCOMERCIALES.Apellido COLLATE SQL_Latin1_General_CP1_CI_AS + ' ' + VW_CCDATOSCOMERCIALES.Nombre COLLATE SQL_Latin1_General_CP1_CI_AS, 80) AS Razon_Social, CASE WHEN ISNUMERIC(VW_CCDATOSCOMERCIALES.Piso) = 1 THEN VW_CCDATOSCOMERCIALES.Piso ELSE '' END AS Piso, CASE WHEN ISNUMERIC(VW_CCDATOSCOMERCIALES.Dto) = 1 THEN VW_CCDATOSCOMERCIALES.Dto ELSE '' END AS Dto, 'DNI' AS Tipo_Documento, VW_CCDATOSCOMERCIALES.DNI AS Nro_Documento, '<SD>' AS CIIU, VW_CCDATOSCOMERCIALES.Fecha_Alta, VW_CCDATOSCOMERCIALES.Fecha_Baja, Medidores.tipo, 'S' AS prosumidor, Medidores.tipo, RIGHT(prosumidor, LEN(prosumidor)-20) as potencia, RTRIM(LEFT(prosumidor, 20)) as clase FROM VW_CCDATOSCOMERCIALES INNER JOIN Suministros INNER JOIN Usuarios ON Suministros.id_suministro = Usuarios.id_suministro ON VW_CCDATOSCOMERCIALES.Id_Usuario = Usuarios.id_usuario INNER JOIN Tarifas ON Usuarios.tarifa = Tarifas.Tarifa LEFT OUTER JOIN Medidores ON Usuarios.id_usuario = Medidores.id_usuario WHERE Usuarios.prosumidor <>''")
    #convierto el cursor en array
    usuarios = tuple(cursor)
    cursor.close()
    for i in range (0, len(usuarios)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(85 + 5 * int(i/len(usuarios)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------

        #0 id_suministro
        #1 Tarifa
        #2 Tension_Suministro
        #3 NIC
        #4 Razon_Social
        #5 Piso
        #6 Dto
        #7 Tipo_Documento
        #8 Nro_Documento
        #9 CIIU
        #10 Fecha_Alta
        #11 Fecha_Baja
        #12 tipo
        #13 prosumidor
        #14 tipo
        #15 potencia
        #16 clase
        if usuarios[i][11]==None or usuarios[i][11]=='':
            str_linea = usuarios[i][0].strip() + ',' + str(usuarios[i][3])
            str_linea = str_linea + ',' + usuarios[i][4].replace(',', '')
            str_linea = str_linea + ',' + usuarios[i][5].strip()
            str_linea = str_linea + ',' + usuarios[i][6].strip()
            str_linea = str_linea + ',' + usuarios[i][7].strip()
            str_linea = str_linea + ',' + usuarios[i][8].strip()
            str_linea = str_linea + ',' + usuarios[i][9].strip()
            str_linea = str_linea + ',' + usuarios[i][10].strftime('%Y-%m-%d').replace("'","")
            if usuarios[i][11]==None or usuarios[i][11]=='':
                str_linea = str_linea + ','
            else:
                str_linea = str_linea + ',' + usuarios[i][11].strftime('%Y-%m-%d').replace("'","")
            if usuarios[i][1]=='T1AP':
                str_linea = str_linea + ',,'
            elif usuarios[i][1]=='T1GAC':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T1GBC':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T1R':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T4NR':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T4R':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T2BT':
                str_linea = str_linea + ',EQBT-MEDT2TF,'
            elif usuarios[i][1]=='T3BT':
                str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T2MT':
                str_linea = str_linea + ',EQMT-MEDT2TF,'
            elif usuarios[i][1]=='T3MT':
                str_linea = str_linea + ',EQMT-MEDT3TF,'
            elif usuarios[i][1]=='T5MT':
                str_linea = str_linea + ',EQMT-MEDT3TF,'
            elif usuarios[i][1]=='T5BT':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            elif usuarios[i][1]=='T6BT':
                if int(usuarios[i][2]) <= 300:
                    str_linea = str_linea + ',EQBT-MEDT1MF,'
                else:
                    str_linea = str_linea + ',EQBT-MEDT3TF,'
            else:
                str_linea = str_linea + ',,'
            if usuarios[i][12]==None:
                str_linea = str_linea + ',Monotarifa'
            else:
                str_linea = str_linea + ',Multitarifa Bidireccional'
            str_linea = str_linea + ',S,' + usuarios[i][15]
            str_linea = str_linea + ',' + usuarios[i][16]
            f.writelines(str_linea + '\n')
    f.close()
    #----------------------------------------------------------------------------
    progress.setValue(90)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    #ET (AT-MT; MT-MT)
    #Dicho archivo aplica para relación de tensiones AT/MT/MT, AT/MT, MT/MT y potencias
    #superiores a 1000 kVA, siempre deberá tener asociado el o los transformadores, con las
    #relaciones de tensiones y potencias mencionadas con anterioridad
    str_archivo = 'c:/gis/energis6/DPE/ETs.txt'
    f = open(str_archivo,'w')
    progress.setWindowTitle('Exportando Estaciones Transformadoras ...')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(Nodos.Geoname) AS geoname, MAX(Nodos.Nombre) AS nombre, Nodos.Descripcion AS SSEE, MAX(Nodos.Tension) AS tension, MAX(Nodos.Val4) AS Datos, MAX(Nodos.UUCC) AS uucc, MAX(Nodos.Modificacion) AS fecha, MAX(Nodos.subzona) AS zona, MAX(Ciudades.Descripcion) AS localidad, MAX(Ciudades.Partido) AS partido FROM Nodos INNER JOIN Ciudades ON Nodos.localidad = Ciudades.Ciudad WHERE (Nodos.Elmt = 1) GROUP BY Nodos.Descripcion HAVING (MAX(Nodos.Tension) >= 1000)')
    #convierto el cursor en array
    fuentes = tuple(cursor)
    cursor.close()
    for i in range (0, len(fuentes)):
        #0 Geoname
        #1 Nombre
        #2 SSEE
        #3 Tension
        #4 Datos
        #5 UUCC
        #6 Modificacion
        #7 Subzona
        #8 Localidad
        #9 Partido
        str_expediente = '1111/2001'
        if fuentes[i][4]!='':
            datos = fuentes[i][4].split('|')
            if datos[1] == '00000/2001':
                str_expediente = '1111/2001'
            elif datos[1] == '00000/2000':
                str_expediente = '1111/2001'
            else:
                str_expediente = datos[1]
        if fuentes[i][2]==None:
            str_linea = 'ET,EETT'
        else:
            str_linea = 'ET,' + fuentes[i][2].replace ('-', '')
        str_linea = str_linea + ',Buenos Aires'
        str_linea = str_linea + ',' + fuentes[i][9]
        str_linea = str_linea + ',' + fuentes[i][8]
        str_linea = str_linea + ',' + fuentes[i][7]
        str_linea = str_linea + ',' #+ Replace(Adodc1.Recordset('Direccion'), ',', '')
        str_linea = str_linea + ',0'
        str_linea = str_linea + ',' + fuentes[i][2]
        str_linea = str_linea + ',' + fuentes[i][6].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',' + str_expediente
        str_linea = str_linea + ',En Servicio'
        str_linea = str_linea + ',1,0'
        f.writelines(str_linea + '\n')
    f.writelines('ET,SSEE,Buenos Aires,,1,,,0,SSEE,2000/01/01,1111/2001,En Servicio,1,0' + '\n')
    f.close()
    #----------------------------------------------------------------------------
    progress.setValue(95)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    #ET, CT (MT-MT; MT-BT)
    #El archivo maestro aplica para relaciones de tensiones MT/MT, MT/BT y potencias
    #comprendidas desde 1kVA hasta 2500 kVA. A su vez se conserva con la finalidad de agrupar los
    #distintos Elementos (Transformadores, Switch, Capacitores, Regulador de Tensión, TI-TV,
    #Descargador, Reactor) que se encuentren un ET o CT en particular
    str_archivo = 'c:/gis/energis6/DPE/CTs.txt'
    f = open(str_archivo,'w')
    progress.setWindowTitle('Exportando Centros de Transformación ...')
    cursor = conn.cursor()
    cursor.execute('SELECT Nodos.Geoname,Nodos.Nombre,Nodos.Modificacion,Ct.Exp,Ct.es,Ct.Tipo_ct,Nodos.Tension,Ct.caeis,Ct.caeies,CT.caees,CT.caeees,CT.casis,CT.casies,CT.cases,CT.casees,MAX(Transformadores.Tipo) AS Tipo,Sum(Transformadores.Potencia) AS Potencia,Ct.Partido ,Ct.localidad, Ct.direccion, Nodos.subzona, Nodos.UUCC FROM (Ct LEFT JOIN Transformadores ON Ct.Id_ct = Transformadores.Id_ct) INNER JOIN Nodos ON Ct.Id_ct = Nodos.Nombre WHERE Nodos.Elmt = 4 GROUP BY Nodos.Geoname,Nodos.Nombre,Nodos.Modificacion,Ct.Exp,Ct.es,Ct.Tipo_ct,Nodos.Tension,Ct.caeis,Ct.caeies,Ct.caees,Ct.caeees,CT.casis,CT.casies,CT.cases,CT.casees,Aux,Ct.Partido,Ct.localidad, Ct.direccion, Nodos.subzona, Nodos.UUCC HAVING (Nodos.Tension > 1000)')
    #convierto el cursor en array
    cts = tuple(cursor)
    cursor.close()
    for i in range (0, len(cts)):
        #----------------------------------------------------------------------------
        # Actualiza el progreso
        progress.setValue(95 + 5 * int(i/len(cts)))
        if progress.wasCanceled():
            return
        # Permitir que la GUI se actualice (similar a DoEvents)
        QApplication.processEvents()
        #----------------------------------------------------------------------------
        #0 Geoname
        #1 Nombre
        #2 Modificacion
        #3 Exp
        #4 ES
        #5 Tipo_ct
        #6 Tension
        #7 caeis
        #8 caeies
        #9 caees
        #10 caeees
        #11 casis
        #12 casies
        #13 cases
        #14 casees
        #15 Tipo
        #16 Potencia
        #17 Partido
        #18 localidad
        #19 direccion
        #20 subzona
        #21 UUCC
        if cts[i][3]==None:
            str_expediente = '1111/2001'
        elif cts[i][3]=='00000/2001':
            str_expediente = '1111/2001'
        elif cts[i][3]=='00000/2000':
            str_expediente = '1111/2001'
        else:
            str_expediente = cts[i][3]
        str_linea = 'CT,' + cts[i][1].replace(',', '').replace('-', '_')
        str_linea = str_linea + ',Buenos Aires'
        str_linea = str_linea + ',' + cts[i][17]
        str_linea = str_linea + ',' + cts[i][18]
        if cts[i][20]==None:
            str_linea = str_linea + ','
        else:
            str_linea = str_linea + ',' + cts[i][20]
        str_linea = str_linea + ',' + cts[i][19].replace(',', '')
        str_linea = str_linea + ',0'
        str_linea = str_linea + ',' + cts[i][1].replace(',', '')
        if cts[i][5]=='Monoposte':
            str_linea = str_linea + ',Aereo'
        elif cts[i][5]=='a Nivel':
            str_linea = str_linea + ',A Nivel'
        elif cts[i][5]=='Biposte':
            str_linea = str_linea + ',Aereo Plataforma'
        elif cts[i][5]=='Plataforma':
            str_linea = str_linea + ',Aereo Plataforma'
        elif cts[i][5]=='Camara':
            str_linea = str_linea + ',A Nivel'
        elif cts[i][5]=='Camara Nivel':
            str_linea = str_linea + ',A Nivel'
        elif cts[i][5]=='Camara Subterranea':
            str_linea = str_linea + ',Subterranea'
        else:
            str_linea = str_linea + ',Aereo'
        if cts[i][4]==0:
            str_linea = str_linea + ',Fuera de Servicio'
        else:
            str_linea = str_linea + ',En Servicio'
        str_linea = str_linea + ',' + cts[i][2].strftime('%Y-%m-%d').replace("'","")
        str_linea = str_linea + ',' + str_expediente
        if cts[i][21]==None:
            str_linea = str_linea + ',SD,'
        else:
            str_linea = str_linea + ',' + cts[i][21].replace(',', '') + ','
        str_tension1 = str(cts[i][6])
        str_linea = str_linea + ',' + str_tension1
        caeis = 0
        caeies = 0
        caees = 0
        caeees = 0
        if cts[i][7]!=None:
            caeies = cts[i][7]
        if cts[i][8]!=None:
            caeies = cts[i][8]
        if cts[i][9]!=None:
            caees = cts[i][9]
        if cts[i][10]!=None:
            caeees = cts[i][10]
        if caeis + caees==0:
            if cts[i][5]=='A Nivel' or cts[i][5]=='Subterranea':
                caeis = 1
            else:
                caees = 1
        str_linea = str_linea + ',' + str(caeis) + ',' + str(caeies) + ',' + str(caees) + ',' + str(caeees)
        cursor = conn.cursor()
        cursor.execute("SELECT Desde, Hasta, Tension FROM Lineas WHERE Tension<>" + str_tension1 + " AND (Desde=" + str(cts[i][0]) + " OR Hasta=" + str(cts[i][0]) + ") ORDER BY Tension DESC")
        #convierto el cursor en array
        lineas = tuple(cursor)
        cursor.close()
        str_tension2 = '400'
        #str_nodo_baja = 0
        #if lineas[0][0]==cts[i][0]:
        #    str_nodo_baja = lineas[0][1]
        #else:
        #    str_nodo_baja = lineas[0][0]
        casis = 0
        casies = 0
        cases = 0
        casees = 0
        if cts[i][11]!=None:
            casis = cts[i][11]
        if cts[i][12]!=None:
            casies = cts[i][12]
        if cts[i][13]!=None:
            cases = cts[i][13]
        if cts[i][14]!=None:
            casees = cts[i][14]
        if casis + cases==0:
            if cts[i][5]=='A Nivel' or cts[i][5]=='Subterranea':
                casis = 1
            else:
                cases = 1
        if cts[i][5]==1:
            str_tension2 = str(lineas[0][2])
        str_linea = str_linea + ',' + str_tension2
        str_linea = str_linea + ',' + str(casis) + ',' + str(casies) + ',' + str(cases) + ',' + str(casees)
        f.writelines(str_linea + '\n')

    str_linea = 'Buenos Aires'
    str_linea = str_linea + ',' + cts[i][17]
    str_linea = str_linea + ',' + cts[i][18]
    if cts[i][20]==None:
        str_linea = str_linea + ','
    else:
        str_linea = str_linea + ',' + cts[i][20]
    str_linea = str_linea + ',' + cts[i][19].replace(',', '')

    f.writelines('CT,CT,' + str_linea + ',0,0,Aereo,En Servicio,2000/01/01,1111/2001,CT,,13200,0,0,1,0,400,0,0,1,0'+ '\n')

    f.close()
    str_archivo = 'c:/gis/energis6/DPE/envolventes.txt'
    f = open(str_archivo,'w')
    progress.setWindowTitle('Exportando Envolventes ...')
    f.close()
    #----------------------------------------------------------------------------
    progress.setValue(100)
    QApplication.processEvents()
    #----------------------------------------------------------------------------
    QMessageBox.warning(None, 'EnerGis 6', "Exportado en C:/GIS/EnerGis6/DPE/")

def exportar_demitec(self, conn, srid, nombre_modelo):
    #try:
    if os.path.isdir('c:/gis/energis6/Google/')==False:
        os.mkdir('c:/gis/energis6/Google/')
    if nombre_modelo == None or nombre_modelo == '':
        nombre_modelo = 'EnerGis6'
    str_archivo = 'c:/gis/energis6/Google/lineas_' + nombre_modelo + '.txt'
    f = open(str_archivo,'w')

    cursor = conn.cursor()
    cursor.execute("SELECT Geoname, LEN(Fase) AS Fases, Longitud, Tension, Alimentador, obj.STAsText() FROM Lineas WHERE Tension > 1000")
    #convierto el cursor en array
    lineas = tuple(cursor)
    cursor.close()
    f.writelines('Id' + chr(9) + 'Fases' + chr(9) + 'Longitud' + chr(9) + 'Tension' + chr(9) + 'Alimentador' + chr(9) + 'Coordenadas' + '\n')
    for linea in lineas:
        str_linea = ''
        str_polilinea = linea[5].replace('LINESTRING (','').replace(')','')
        coordenadas = str_polilinea.split(', ')
        for coordenada in coordenadas:
            x, y = coordenada.split(' ')
            coords = convertir_coordenadas(self, x, y, srid, 4326)
            str_linea = str_linea + str(coords[1]) + ' ' + str(coords[0]) + ', '
        str_linea = 'LINESTRING (' + str_linea[:-2] + ')'
        str_linea = str(linea[0]) + chr(9) + str(linea[1]) + chr(9) + str(linea[2]) + chr(9) + str(linea[3]) + chr(9) + str(linea[4]) + chr(9) + str_linea
        f.writelines(str_linea + '\n')
    f.close()

    str_archivo = 'c:/gis/energis6/Google/seccionadores_' + nombre_modelo + '.txt'
    f = open(str_archivo,'w')
    cursor = conn.cursor()
    cursor.execute("SELECT Geoname, Nombre, CASE WHEN elmt=2 THEN 'NC' ELSE 'NA' END AS Estado, obj.STAsText() FROM Nodos WHERE elmt IN (2,3) AND Tension > 1000")
    #convierto el cursor en array
    seccionadores = tuple(cursor)
    cursor.close()
    f.writelines('Id' + chr(9) + 'Nombre' + chr(9) + 'Tipo' + chr(9) + 'Coordenadas' + '\n')
    for secc in seccionadores:
        str_linea = ''
        str_nodo = secc[3].replace('POINT (','').replace(')','')
        x, y = str_nodo.split(' ')
        coords = convertir_coordenadas(self, x, y, srid, 4326)
        str_linea = str_linea + str(coords[1]) + ' ' + str(coords[0]) + ', '
        str_linea = 'POINT (' + str_linea[:-2] + ')'
        str_linea = str(secc[0]) + chr(9) + str(secc[1]) + chr(9) + str(secc[2]) + chr(9) + str_linea
        f.writelines(str_linea + '\n')
    f.close()

    QMessageBox.warning(None, 'EnerGis 6', "Exportado en C:/GIS/EnerGis6/Google/")

