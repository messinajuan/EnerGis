"""
/***************************************************************************
 autoSaver
                                 A QGIS plugin
 auto save current project
                             -------------------
        begin                : 2018-05-01
        copyright            : (C) 2018 by Juan Messina
        email                : messinajuan@yahoo.com.ar
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""

from .energis6 import EnerGis6

def classFactory(iface):
    return EnerGis6(iface)
