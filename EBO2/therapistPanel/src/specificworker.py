#!/usr/bin/python3
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

from PySide6.QtCore import QTimer, QFile, Slot, QEvent
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6 import QtCore, QtUiTools, QtGui, QtWidgets
from rich.console import Console
from genericworker import *
import interfaces as ifaces
import csv
from datetime import datetime
import os

# Rutas de UIs y logos
UI_MENU     = "../../igs/therapistPanel.ui"
LOGO_1      = "../../igs/logos/logo_euro.png"
LOGO_2      = "../../igs/logos/robolab.png"

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


class SpecificWorker(GenericWorker):

    update_ui_signal = QtCore.Signal()

    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

            QtCore.QTimer.singleShot(100, lambda: self.update_ui_signal.emit())

        # Si SpecificWorker es un Widget, lo ocultamos para que solo se vea tu UI cargada.
        if isinstance(self, QWidget):
            self.hide()

        self.counts = {
            "atencion_button" : 0,
            "comprension_button" : 0,
            "frustracion_button" : 0,
            "apoyo_button" : 0,
        }
        self.pacienteactual = ""
        self.registrosesion = []
        self.residencianame = ""
        self.log_dir = "therapy_control"
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # 2. UI e hilos
        self.ui = self.therapistPanel_ui()
        self.update_ui_signal.connect(self.handle_update_ui)

    def eventFilter (self, obj, event):
        """ Captura el cierre de la ventana principal """
        if event.type() == QtCore.QEvent.Close:
            # 1. Preguntar si realmente quiere salir
            respuesta = QMessageBox.question(
                obj, "Cerrar", "¿Estás seguro de que quieres finalizar la sesión?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if respuesta == QMessageBox.Yes:
                # 2. Si dice que sí, pedimos el nombre de la residencia
                self.solicitar_residencia_y_guardar()
                return True  # Bloqueamos el cierre inmediato para manejarlo nosotros
            else:
                event.ignore()
                return True
        return super().eventFilter(obj, event)

    def solicitar_residencia_y_guardar(self):
        # Usamos QtWidgets.QInputDialog directamente
        nombre, ok = QtWidgets.QInputDialog.getText(
            self.ui, "Finalizar sesión",
            "Introduzca el nombre del Centro:",
            text="Centro"
        )

        # Guardamos el nombre (o uno por defecto si cancela)
        self.residencianame = nombre if (ok and nombre) else ""

        # Ejecutamos el guardado final
        self.guardarSesionFinal()

        # Cerramos la aplicación
        self.ui.removeEventFilter(self)
        self.ui.close()
        QApplication.quit()

    def guardarSesionFinal(self):
        """ Guarda un CSV final con todos los pacientes registrados durante la jornada """
        # Verificamos si hay algún clic suelto que no se haya registrado por paciente
        clics_pendientes = sum(self.counts.values())
        if clics_pendientes > 0:
             console.print("[yellow]⚠ Aviso: Había clics sin asignar a ningún paciente al cerrar.[/yellow]")

        fecha_str = datetime.now().strftime("%d%m%Y_%H%M")
        nombre_fichero = f"{self.residencianame.replace(' ', '_')}_{fecha_str}.csv"
        path_final = os.path.join(self.log_dir, nombre_fichero)

        # Headers actualizados con 'Hora'
        headers = ["Paciente", "Hora", "Atencion", "Comprension", "Frustracion", "Apoyo"]

        try:
            with open(path_final, mode='w', newline='', encoding='utf-8') as f:
                # Metadatos
                f.write(f"# Residencia: {self.residencianame}\n")
                f.write(f"# Fecha: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n")

                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                # Escribimos la lista de pacientes registrados mediante el botón
                for fila in self.registrosesion:
                    writer.writerow(fila)

            console.print(f"[bold green]✅ Archivo final de residencia guardado: {path_final}[/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Error al guardar log final: {e}[/bold red]")

################################################# LOGICA DE BOTONES #################################################################################################

    def atencion_clicked(self):
        self.counts["atencion_button"] += 1
        print(f"Atencion: {self.counts['atencion_button']}")

    def comprension_clicked(self):
        self.counts["comprension_button"] += 1
        print(f"Comprension: {self.counts['comprension_button']}")

    def frustracion_clicked(self):
        self.counts["frustracion_button"] += 1
        print(f"Frustracion: {self.counts['frustracion_button']}")

    def apoyo_clicked(self):
        self.counts["apoyo_button"] += 1
        print(f"Apoyo: {self.counts['apoyo_button']}")

    def paciente_clicked(self):
        """ Registra al paciente que acaba de finalizar su sesión """
        # 1. Pedir nombre del paciente que acaba de terminar la sesión
        nombre, ok = QtWidgets.QInputDialog.getText(
            self.ui, "Registrar Sesión", "Nombre del Paciente que finaliza:"
        )

        if ok and nombre:
            # 2. Guardamos sus datos actuales en la lista de la sesión
            self.registrosesion.append({
                "Paciente": nombre,
                "Hora": datetime.now().strftime("%H:%M:%S"),
                "Atencion": self.counts["atencion_button"],
                "Comprension": self.counts["comprension_button"],
                "Frustracion": self.counts["frustracion_button"],
                "Apoyo": self.counts["apoyo_button"]
            })

            # 3. Reiniciar contadores a cero para el siguiente paciente
            for key in self.counts:
                self.counts[key] = 0

            console.print(f"[bold blue]👤 Sesión registrada para: {nombre}[/bold blue]")
            QMessageBox.information(self.ui, "Completado", f"Datos de {nombre} guardados.\nContadores reiniciados.")
        else:
            console.print("[yellow]⚠ Registro de paciente cancelado.[/yellow]")

    def load_ui_generic(self, ui_path, ui_number, *, logo_paths=None, botones=None,
                        ayuda_button=None, after_load=None):
        loader = QtUiTools.QUiLoader()
        file = QFile(ui_path)
        file.open(QFile.ReadOnly)
        ui = loader.load(file)
        file.close()

        # Logos
        if logo_paths:
            for label_name, path in logo_paths.items():
                label = getattr(ui, label_name, None)
                if label:
                    label.setPixmap(QPixmap(path))
                    label.setScaledContents(True)

        # Botones
        if botones:
            for btn_name, func in botones.items():
                btn = getattr(ui, btn_name, None)
                if btn:
                    btn.clicked.connect(func)
                    print(f"[OK] Botón '{btn_name}' conectado correctamente.")
                else:
                    print(f"[ERROR] No encuentro un botón llamado '{btn_name}' en el archivo .ui")
                    print(f"       -> Revisa el 'objectName' en Qt Designer.")

        # Ayuda
        if ayuda_button and hasattr(ui, ayuda_button):
            getattr(ui, ayuda_button).clicked.connect(lambda: self.toggle_ayuda(ui))
            if hasattr(ui, "ayuda"):
                ui.ayuda.hide()

        # Hook opcional post-carga (por si quieres hacer algo extra)
        if callable(after_load):
            after_load(ui)

        # Registrar para eventFilter
        if not hasattr(self, 'ui_numbers'):
            self.ui_numbers = {}
        self.ui_numbers[ui] = ui_number
        ui.installEventFilter(self)
        return ui


    def toggle_ayuda(self, ui):
        if hasattr(ui, "ayuda"):
            ui.ayuda.setVisible(not ui.ayuda.isVisible())


    def __del__(self):
        """Destructor"""

    def therapistPanel_ui(self):
        ui = self.load_ui_generic(
            UI_MENU, ui_number=1,
            logo_paths={"label": LOGO_1, "label_3": LOGO_2},
            botones={
                "atencion_button": self.atencion_clicked,
                "comprension_button": self.comprension_clicked,
                "frustracion_button": self.frustracion_clicked,
                "apoyo_button": self.apoyo_clicked,
                "paciente_button": self.paciente_clicked,
            },
            ayuda_button="ayuda_button",
            after_load=lambda u: (hasattr(u, "ayuda") and u.ayuda.hide())
        )
        return ui



    ####################################################################################################################################

    def cerrar_ui(self, numero):
        ui_nombre = "ui" if numero == 1 else f"ui{numero}"
        ui_obj = getattr(self, ui_nombre, None)
        if ui_obj:
            ui_obj.removeEventFilter(self)  # Desactiva el event filter
            ui_obj.close()  # Cierra la ventana
            ui_obj.installEventFilter(self)  # Reactiva el event filter
        else:
            print(f"Error: {ui_nombre} no existe en la instancia.")


    @QtCore.Slot()
    def compute(self):
        # Si por algún motivo la interfaz se ocultara, esto la mantiene viva
        # pero para no saturar el sistema, solo verificamos si es visible
        if self.ui and not self.ui.isVisible():
            self.ui.show()
        return True
    @Slot()
    def handle_update_ui(self):
        """ Esta función se encarga de hacer visible la ventana """
        if self.ui:
            self.ui.show()
            self.ui.raise_()
            self.ui.activateWindow() # La pone al frente de todas las carpetas
            print("LOG: Interfaz mostrada con éxito.")

    # def centrar_ventana(self, ventana):
    #     pantalla = QApplication.primaryScreen().availableGeometry()
    #     tamano_ventana = ventana.size()
    #     x = (pantalla.width() - tamano_ventana.width()) // 2
    #     y = (pantalla.height() - tamano_ventana.height()) // 2
    #     ventana.move(x, y)

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)
