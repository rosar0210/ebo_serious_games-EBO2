#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
#    Copyright (C) 2026 by YOUR NAME HERE
#
#    This file is part of RoboComp
#
#    RoboComp is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    RoboComp is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with RoboComp.  If not, see <http://www.gnu.org/licenses/>.
#

# \mainpage RoboComp::therapistPanel
#
# \section intro_sec Introduction
#
# Some information about the component...
#
# \section interface_sec Interface
#
# Descroption of the interface provided...
#
# \section install_sec Installation
#
# \subsection install1_ssec Software depencences
# Software dependences....
#
# \subsection install2_ssec Compile and install
# How to compile/install the component...
#
# \section guide_sec User guide
#
# \subsection config_ssec Configuration file
#
# <p>
# The configuration file...
# </p>
#
# \subsection execution_ssec Execution
#
# Just: "${PATH_TO_BINARY}/therapistPanel --Ice.Config=${PATH_TO_CONFIG_FILE}"
#
# \subsection running_ssec Once running
#
#
#
# ... (cabecera y comentarios iniciales se mantienen igual)

import argparse
import signal
import sys
import os
from pathlib import Path

from rich.console import Console
from rich.text import Text
console = Console()


# ROBOCOMP = '/home/rosa/robocomp'
# configloader_path = os.path.join(ROBOCOMP, "core", "classes", "ConfigLoader")
# if not os.path.exists(configloader_path):
#     configloader_path = os.path.join(ROBOCOMP, "classes", "ConfigLoader")
# sys.path.append(str(configloader_path))

# Esta es la ruta exacta que encontró el comando find
sys.path.append("/home/rosa/robocomp/core/classes/ConfigLoader")

# Ahora importamos la clase
from ConfigLoader import ConfigLoader
# --------------------------------------------

try:
    from ConfigLoader import ConfigLoader
except ImportError:
    console.print(Text("ERROR CRÍTICO: No encuentro ConfigLoader.py", "red"))
    console.print(Text(f"He buscado en: {classes_path}", "yellow"))
    console.print(Text(f"Comprueba que tienes instalado RoboComp en /opt/robocomp", "yellow"))
    exit(-1)
# --- FIN DEL CAMBIO ---

# --------------------------------------------

try:
    from ConfigLoader import ConfigLoader
except ModuleNotFoundError:
    console.print(Text(f"ERROR CRÍTICO: No encuentro ConfigLoader.py", "red"))
    console.print(Text(f"Buscado en: {configloader_path}", "red"))
    exit(-1)

# --- AÑADIR ESTO ---
import os
import sys

# Calculamos la ruta a la carpeta 'src' (un nivel arriba y luego entrar en src)
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.abspath(os.path.join(current_dir, "..", "src"))
sys.path.append(src_path)
# -------------------

from specificworker import SpecificWorker  # <--- Esta es la línea que ya tenías

import interfaces
from PySide6 import QtWidgets, QtCore # Añadido QtCore para el handler de señales



#SIGNALS handler
def sigint_handler(*args):
    QtCore.QCoreApplication.quit()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    parser = argparse.ArgumentParser()
    parser.add_argument('configfile', nargs='?', type=str, default='etc/config')
    parser.add_argument('--startup-check', action='store_true')

    args = parser.parse_args()
    configData = ConfigLoader.load_config(args.configfile)
    interface_manager = interfaces.InterfaceManager(configData)

    if interface_manager.status == 0:
        worker = SpecificWorker(interface_manager.get_proxies_map(), configData, args.startup_check)
        if hasattr(worker, "setParams"): worker.setParams(configData)
    else:
        print("Error getting required connections, check config file")
        sys.exit(-1)

    interface_manager.set_default_hanlder(worker, configData)
    signal.signal(signal.SIGINT, sigint_handler)
    app.exec()
    interface_manager.destroy()
