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
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from PyQt6 import uic
    
DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_mediciones.ui'))

class frmMediciones(DialogType, DialogBase):

    def __init__(self, conn, id_medicion, limite):
        super().__init__()
        self.setupUi(self)
        #self.setFixedSize(self.size())
        self.conn = conn
        self.id_medicion = id_medicion
        self.limite = limite
        self.cmdSalir.clicked.connect(self.salir)
        # Crear el gráfico de Matplotlib
        canvas = self.create_plot()
        # Agregar el gráfico al layout
        self.layout.addWidget(canvas)

    def create_plot(self):
        #Crear el gráfico de Matplotlib.
        # Crear una figura para Matplotlib
        figure = Figure()
        canvas = FigureCanvas(figure)
        ax = figure.add_subplot(111)
        cursor = self.conn.cursor()
        cursor.execute("SELECT FechaHora,TensionU,TensionV,TensionW FROM Mediciones_Registros WHERE Id_Medicion='" + self.id_medicion + "' ORDER BY FechaHora")
        #convierto el cursor en array
        medicion = tuple(cursor)
        cursor.close()
        x=[]
        v1=[]
        v2=[]
        v3=[]
        for i in range(len(medicion)):
            x.append(medicion[i][0])
            v1.append(medicion[i][1])
            v2.append(medicion[i][2])
            v3.append(medicion[i][3])
        # Generar datos
        min = [220 * (1 + self.limite/100)]*len(medicion)
        max = [220 * (1 - self.limite/100)]*len(medicion)
        # Dibujar las tres series
        ax.plot(x, v1, label="Vr", color="red", linewidth=0.75)
        ax.plot(x, v2, label="Vs", color="green", linewidth=0.75)
        ax.plot(x, v3, label="Vt", color="blue", linewidth=0.75)
        ax.plot(x, min, label="min", linestyle="dotted", color="magenta", linewidth=0.75)
        ax.plot(x, max, label="max", linestyle="dotted", color="magenta", linewidth=0.75)
        # Configurar los ejes
        ax.set_ylim(165, 275)  # Eje Y limitado
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))  # Formato día-mes
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))  # Una etiqueta por día
        ax.tick_params(axis='x', rotation=90)  # Rotar etiquetas del eje X
        # Títulos y etiquetas
        ax.set_title("Medición " + self.id_medicion, fontsize=11)
        #ax.set_xlabel("Fecha", fontsize=10)
        #ax.set_ylabel("V", fontsize=10)
        # Agregar leyenda
        ax.legend(fontsize=10)
        # Agregar rejilla
        ax.grid(alpha=0.3)
        # Ajustar diseño para evitar superposición
        figure.tight_layout()
        return canvas

    def salir(self):
        self.close()
