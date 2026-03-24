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
from PyQt6 import QtCore
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QDate, QDateTime, QTime
from datetime import timedelta
from PyQt6 import uic

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__),'frm_elegir_fechas.ui'))

class frmElegirFechas(DialogType, DialogBase):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(self.size())
        dia_del_mes_pasado = self.restar_un_mes(QDate.currentDate())
        primer_dia = QDate(dia_del_mes_pasado.year(), dia_del_mes_pasado.month(), 1)
        hora = QTime(0, 0)
        desde = QDateTime(primer_dia, hora)
        ultimo_dia = QDate(QDate.currentDate().year(), QDate.currentDate().month(), 1)
        ultimo_dia = ultimo_dia.toPyDate() - timedelta(days=1)
        hora = QTime(23, 59)
        hasta = QDateTime(ultimo_dia, hora)
        self.datDesde.setDateTime(desde)
        self.datHasta.setDateTime(hasta)
        self.chkDesde.setChecked(True)
        self.chkHasta.setChecked(True)
        self.cmdAceptar.clicked.connect(self.aceptar)
        self.cmdSalir.clicked.connect(self.salir)

    def restar_un_mes(self, date):
        year = date.year()
        month = date.month()
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        day = min(date.day(), QDate(year, month, 1).daysInMonth())
        return QDate(year, month, day)

    def aceptar(self):
        self.fecha_desde = None
        if self.chkDesde.isChecked() == True:
            self.fecha_desde = self.datDesde.dateTime().toPyDateTime()
        self.fecha_hasta = None
        if self.chkHasta.isChecked() == True:
            self.fecha_hasta = self.datHasta.dateTime().toPyDateTime()
        self.close()

    def salir(self):
        self.fecha_desde = None
        self.fecha_hasta = None
        self.close()
