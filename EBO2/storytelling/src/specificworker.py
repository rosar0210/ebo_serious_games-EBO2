#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2025 by YOUR NAME HERE
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

from PySide6 import QtUiTools
from rich.console import Console
from genericworker import *
import os
import json
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import Qt, QTimer, QFile, Signal, Slot
import threading
import time
import sys
import requests
from dotenv import load_dotenv

# Rutas comunes
UI_SEL = "../../igs/seleccion_menu.ui"
UI_CONV = "../../igs/conversacional_menu2.ui"
UI_ST = "../../igs/storytelling_menu.ui"
UI_RESP = "../../igs/respuesta_gpt.ui"
LOGO_1 = "../../igs/logos/logo_euro.png"
LOGO_2 = "../../igs/logos/robolab.png"

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)

script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(script_dir, "../../.."))
ruta_env = "/home/rosa/ebo_serious_games/EBO2/ebo_gpt/.env"

if os.path.exists(ruta_env):
    load_dotenv(ruta_env)
else:
    print(f"⚠️ Advertencia: No se encontró el archivo .env en {ruta_env}")

# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel


class SpecificWorker(GenericWorker):
    update_ui_signal = Signal()

    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 2000
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

        #Creamos directorio (si no existe) para almacenar los archivos de las conversaciones en memoria
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        self.memoria_path = os.path.join(self.base_path, "memoria")

        if not os.path.exists(self.memoria_path):
            os.makedirs(self.memoria_path)
            print(f"Carpeta creada exitosamente en: {self.memoria_path}")

        self.flag_test = True
        print("COMPONENTE STORYTELLING INICIADO")

        self.ui = self.game_selector_ui()
        self.ui2 = self.conversational_ui()
        self.ui3 = self.storytelling_ui()
        self.ui4 = self.respuesta_ui()

        self.reiniciar_variables()

        # Variables para lógica autónoma
        self.autonomo = False
        self._autonomo_thread = None
        self._asr_lock = threading.Lock()

        self.update_ui_signal.connect(self.handle_update_ui)

    def __del__(self):
        """Destructor"""

    def setParams(self, params):
        # try:
        #   self.innermodel = InnerModel(params["InnerModelPath"])
        # except:
        #   traceback.print_exc()
        #   print("Error reading config params")
        return True

    @QtCore.Slot()
    def compute(self):

        return True

    def reiniciar_variables(self):
        self.nombre_jugador = ""
        self.aficiones = ""
        self.edad = ""
        self.familiares = ""

        self.personalidad = ""

        self.historial_charla = []

    ### CARGADOR DE UIs
    def load_ui(self, ui_path, ui_number, logo_paths=None, botones=None,
                ayuda_button=None, back_button=None, combo_setter=None):

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

        # Ayuda
        if ayuda_button and hasattr(ui, ayuda_button):
            getattr(ui, ayuda_button).clicked.connect(lambda: self.toggle_ayuda(ui))
            if hasattr(ui, "ayuda"):
                ui.ayuda.hide()

        # Back
        if back_button and hasattr(ui, back_button):
            getattr(ui, back_button).clicked.connect(lambda: self.back_clicked_ui(ui_number))

        # Setups específicos (combos, etc.)
        if callable(combo_setter):
            combo_setter(ui)

        # Registrar en eventFilter
        if not hasattr(self, 'ui_numbers'):
            self.ui_numbers = {}
        self.ui_numbers[ui] = ui_number
        ui.installEventFilter(self)
        return ui

    def toggle_ayuda(self, ui):
        if hasattr(ui, "ayuda"):
            ui.ayuda.setVisible(not ui.ayuda.isVisible())

    def back_clicked_ui(self, ui_number):
        # MODIFICACIÓN CLAVE APLICADA AQUÍ
        # Si estamos saliendo de la UI 4, primero detener el modo autónomo de forma segura.
        if ui_number == 4:
            if self.autonomo:
                self.detener_autonomo()
            # Notificar al GPT proxy el cierre del chat antes de lanzar la app principal
            self.gpt_proxy.continueChat("03827857295769204")  # Asumiendo que es el código de parada.

        self.cerrar_ui(ui_number)
        self.gestorsg_proxy.LanzarApp()

    ################ FUNCIONES RELACIONADAS CON LA INTERFAZ GRÁFICA ################

    def centrar_ventana(self, ventana):
        # Obtener la geometría de la pantalla
        pantalla = QApplication.primaryScreen().availableGeometry()

        # Obtener el tamaño de la ventana
        tamano_ventana = ventana.size()

        # Calcular las coordenadas para centrar la ventana
        x = (pantalla.width() - tamano_ventana.width()) // 2
        y = (pantalla.height() - tamano_ventana.height()) // 2

        # Mover la ventana a la posición calculada
        ventana.move(x, y)

    #### UI 1 #### ################ ############################################### ################
    def game_selector_ui(self):
        return self.load_ui(
            UI_SEL, ui_number=1,
            logo_paths={"label": LOGO_1, "label_2": LOGO_2},
            botones={
                "conversation_game": self.conversation_clicked,
                "storytelling_game": self.story_clicked
            },
            ayuda_button="ayuda_button",
            back_button="back_button"
        )

    def conversation_clicked(self):
        print("Conversación Seleccionada")
        self.cerrar_ui(1)
        self.lanzar_ui2()

    def story_clicked(self):
        print("Story Telling Seleccionado")
        self.cerrar_ui(1)
        self.lanzar_ui3()

    #### UI 2 ####
    def conversational_ui(self):
        def set_personalidades(ui):
            ui.comboBox.clear()
            ui.comboBox.addItems([
                "Seleccionar Personalidad...", "EBO_simpatico", "EBO_cacereño",
                "EBO_colegios", "modo_memoria", "modo_cultural",
                "modo_ludico", "modo_cotidiano"
            ])

        ui = self.load_ui(
            UI_CONV, ui_number=2,
            logo_paths={"label": LOGO_1, "label_2": LOGO_2},

            botones={
                "startGame": self.startGame_clicked_conv,
                "startGame_user": self.startGame_clicked_conv
            },
            ayuda_button="ayuda_button",
            back_button="back_button",
            combo_setter=set_personalidades
        )

        #Cargar los usuarios existentes en el ComboBox
        self.actualizar_combo_usuarios(ui)
        ui.comboBox_user.currentIndexChanged.connect(lambda: self.usuario_seleccionado(ui))

        return ui

    def actualizar_combo_usuarios(self, ui):
        ui.comboBox_user.blockSignals(True)  #Evita que se dispare el evento al limpiar
        ui.comboBox_user.clear()
        ui.comboBox_user.addItem("Nuevo Usuario...")  # La primera opción siempre será para crear uno nuevo

        if os.path.exists(self.memoria_path):
            for archivo in os.listdir(self.memoria_path):
                if archivo.endswith(".json"):
                    #Limpiamos el nombre del archivo para mostrarlo
                    nombre = archivo.replace(".json", "").replace("_", " ").title()
                    ui.comboBox_user.addItem(nombre)
        ui.comboBox_user.blockSignals(False)

    def usuario_seleccionado(self, ui):
        seleccion = ui.comboBox_user.currentText()

        if seleccion == "Nuevo Usuario..." or not seleccion:
            # Si es nuevo, limpiamos todos los campos para que el terapeuta los rellene
            ui.nombreE.clear()
            ui.aficionE.clear()
            ui.edadE.clear()
            ui.famiE.clear()
            ui.nombreE.setReadOnly(False)  #Permitimos escribir el nombre
            ui.nombreE.setStyleSheet("")
        else:
            # Si es un usuario existente, cargamos sus datos
            datos = self.cargar_memoria_usuario(seleccion)
            if datos:
                ui.nombreE.setPlainText(datos.get("nombre", seleccion))
                ui.nombreE.setReadOnly(True)  # Bloqueamos el nombre para que no lo editen por error
                ui.aficionE.setPlainText(datos.get("aficiones", ""))
                ui.edadE.setPlainText(datos.get("edad", ""))
                ui.famiE.setPlainText(datos.get("familiares", ""))
                ui.nombreE.setStyleSheet("background-color: #d4edda;")  #Fondo verde de éxito

    def verificar_usuario_existente(self, ui):
        nombre = ui.nombreE.toPlainText().strip()
        if len(nombre) < 3: return  #Evitar buscar con una sola letra

        datos = self.cargar_memoria_usuario(nombre)
        if datos:
            ui.aficionE.setPlainText(datos.get("aficiones", ""))
            ui.edadE.setPlainText(datos.get("edad", ""))
            ui.famiE.setPlainText(datos.get("familiares", ""))
            #Feedback visual de que lo recordamos
            ui.nombreE.setStyleSheet("background-color: #D4EDDA;")
        else:
            ui.nombreE.setStyleSheet("")

    def guardar_memoria_usuario(self, nombre):
        if not nombre: return

        #Primero, recuperamos la síntesis anterior (si la hubiera) para no borrarla al guardar
        datos_antiguos = self.cargar_memoria_usuario(nombre)
        sintesis = datos_antiguos.get("sintesis_conversacion", "No hay registros previos.") if datos_antiguos else "No hay registros previos."

        datos = {
            "nombre": self.nombre_jugador,
            "aficiones": self.aficiones,
            "edad": self.edad,
            "familiares": self.familiares,
            "ultima_sesion": time.strftime("%d-%m-%Y %H:%M:%S"),
            "personalidad_habitual": self.personalidad,
            "sintesis_conversacion": sintesis #Se guarda la síntesis
        }

        nombre_limpio = nombre.lower().strip().replace(" ", "_")
        ruta_archivo = os.path.join(self.memoria_path, f"{nombre_limpio}.json")

        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                json.dump(datos, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la memoria: {e}")

    def cargar_memoria_usuario(self, nombre):
        nombre_limpio = nombre.lower().strip().replace(" ", "_")
        ruta_archivo = os.path.join(self.memoria_path, f"{nombre_limpio}.json")

        if os.path.exists(ruta_archivo):
            try:
                with open(ruta_archivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error al leer memoria: {e}")
        return None

    def actualizar_sintesis_memoria(self, nombre, resumen_nuevo):
        """Añade los puntos importantes de hoy al JSON del usuario"""
        if not nombre: return

        datos = self.cargar_memoria_usuario(nombre)
        if datos:
            # Limpiar el mensaje por defecto si existe
            sintesis_actual = datos.get("sintesis_conversacion", "")
            if sintesis_actual == "No hay registros previos.":
                sintesis_actual = ""

            # Formato: Añadimos la fecha corta y el resumen para tener un histórico
            fecha_hoy = time.strftime("%d/%m")
            nueva_sintesis = f"{sintesis_actual} | [Sesión {fecha_hoy}]: {resumen_nuevo}".strip(" |")

            # Para no saturar al GPT, si la memoria se hace muy larga (más de 4 sesiones),
            # podríamos cortar lo más antiguo, pero por ahora lo concatenamos.
            datos["sintesis_conversacion"] = nueva_sintesis

            # Sobrescribimos el archivo JSON
            nombre_limpio = nombre.lower().strip().replace(" ", "_")
            ruta_archivo = os.path.join(self.memoria_path, f"{nombre_limpio}.json")

            try:
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    json.dump(datos, f, ensure_ascii=False, indent=4)
                print(f"✅ Síntesis de la sesión guardada para {nombre}")
            except Exception as e:
                print(f"❌ Error al actualizar la síntesis: {e}")

    def generar_resumen_background(self, nombre, historial):
        if not historial:
            return

        print(f"Generando síntesis automática de {len(historial)} intervenciones...")
        texto_usuario = " - ".join(historial)

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            print("❌ ERROR: No se ha encontrado la OPENAI_API_KEY en el entorno.")
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Le pedimos a GPT que resuma estrictamente la charla
        data = {
            "model": "gpt-5-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente clínico. Resume la intervención en UNA SOLA FRASE directa y objetiva."
                },
                {
                    "role": "user",
                    "content": f"Sesión del paciente: {texto_usuario}"
                }
            ],
            "max_completion_tokens": 1500,
            "response_format": {"type": "text"}
        }

        try:
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
            if response.status_code == 200:
                resumen_final = response.json()["choices"][0]["message"]["content"].strip()
                self.actualizar_sintesis_memoria(nombre, resumen_final)
                print(f"SÍNTESIS CREADA: {resumen_final}")
            else:
                print(f"Error de API al resumir: {response.text}")
        except Exception as e:
            print(f"Error de conexión al generar resumen automático: {e}")

    def startGame_clicked_conv(self):
        #Preparamos los datos base y la memoria episódica (se guarda en self.user_info)
        self.setDatos()
        memoria_base = self.user_info  # Guardamos la memoria para que no se borre

        self.personalidad = self.ui2.comboBox.currentText()
        if not self.personalidad or self.personalidad == "Seleccionar Personalidad...":
            print("Por favor selecciona una personalidad.")
            return

        if self.personalidad == "EBO_cacereño":
            respuesta = QMessageBox.question(
                self.ui2,
                "Confirmar Personalidad",
                "¿Seguro que quieres comenzar el modo ebo_cacereño?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if respuesta == QMessageBox.No:
                return

        #Juntamos la Personalidad con la Memoria
        if self.personalidad == "EBO_colegios":
            # En colegios no usamos memoria episódica individual
            self.user_info = f"Estas con la clase de {self.nombre_jugador}. Presentate y saluda a todos y todas, y diles que estas aqui para responder todas sus preguntas."

        elif self.personalidad.startswith("modo_"):
            # Unimos la memoria recuperada con las instrucciones del modo de juego
            self.user_info = (f"{memoria_base}\n\n"
                              f"IMPORTANTE: Hoy vas a actuar en {self.personalidad}. "
                              f"El tema principal de conversación de hoy será: {self.aficiones}. "
                              f"Inicia la conversación saludando y usando la información que recuerdas de la sesión anterior.")
        else:
            # Para EBO_simpatico o cacereño, la memoria base ya es perfecta
            self.user_info = memoria_base

        # 3. CHIVATO PARA LA TERMINAL (Para comprobar que funciona)
        print("\n" + "=" * 50)
        print("MEMORIA ENVIADA AL CEREBRO DE EBO:")
        print(self.user_info)
        print("=" * 50 + "\n")

        self.ui2.nombreE.clear()
        self.ui2.aficionE.clear()
        self.ui2.edadE.clear()
        self.ui2.famiE.clear()

        print("Iniciando juego con los datos seleccionados")
        self.cerrar_ui(2)

        # SET GAME INFO (Enviamos al Proxy)
        self.gpt_proxy.setGameInfo(self.personalidad, self.user_info)
        self.lanzar_ui4()
        self.ui4.text_info.setText("EBO comenzará a hablar en breve")

        # START CHAT
        self.gpt_proxy.startChat()
        self.ui4.text_info.setText("Introduzca respuesta")

    def setDatos(self):
        self.nombre_jugador = self.ui2.nombreE.toPlainText().strip()
        self.aficiones = self.ui2.aficionE.toPlainText()
        self.edad = self.ui2.edadE.toPlainText()
        self.familiares = self.ui2.famiE.toPlainText()

        self.guardar_memoria_usuario(self.nombre_jugador)

        seleccion_combo = self.ui2.comboBox_user.currentText()
        es_nuevo = (seleccion_combo == "Nuevo Usuario...")

        if es_nuevo:
            prefijo = "Es la primera vez que hablas con este usuario. Preséntate amablemente y conócele."
        else:
            datos_antiguos = self.cargar_memoria_usuario(self.nombre_jugador)

            # Extraemos la síntesis de forma segura y aplicamos el SÚPER PROMPT
            if datos_antiguos and "sintesis_conversacion" in datos_antiguos and datos_antiguos["sintesis_conversacion"] != "No hay registros previos.":
                sintesis = datos_antiguos["sintesis_conversacion"]
                prefijo = (f"Ya conoces a este usuario de sesiones anteriores. Salúdale con mucha alegría. "
                           f"Acabas de recordar esta información sobre él/ella: {sintesis}. "
                           f"REGLA OBLIGATORIA: Integra esta información de forma muy natural y fluida en la charla para preguntarle qué tal le va, no se la tienes que recordar continuamente. "
                           f"NUNCA leas las fechas, NUNCA digas la palabra 'sesión', ni 'anoté esto', ni leas corchetes. "
                           f"Finge que esos recuerdos te acaban de venir a la mente espontáneamente como le pasaría a un buen amigo, pero no todo el rato.")
            else:
                prefijo = "Ya conoces a este usuario, pero no tienes recuerdos específicos de la última sesión. Salúdale como a un viejo amigo, pero no le digas que no recuerdas nada."

        self.user_info = (f"{prefijo} Sus datos actuales son: Nombre: {self.nombre_jugador}. "
                          f"Edad: {self.edad}. Aficiones: {self.aficiones}. Familiares: {self.familiares}.")

    #### UI 3 #### ################ ############################################### ################
    def storytelling_ui(self):
        def set_juegos(ui):
            self.configure_combobox(ui, "../juegos_story")

        return self.load_ui(
            UI_ST, ui_number=3,
            logo_paths={"label": LOGO_1, "label_2": LOGO_2},
            botones={"startGame": self.startGame_clicked},
            ayuda_button="ayuda_button",
            back_button="back_button",
            combo_setter=set_juegos
        )

    def configure_combobox(self, ui, folder_path):
        # Acceder al QComboBox por su nombre de objeto
        combobox = ui.findChild(QtWidgets.QComboBox, "comboBox")
        if combobox:
            combobox.addItem("Seleccionar juego...")
            # Obtener la lista de archivos en la carpeta
            try:
                archivos = [
                    archivo for archivo in os.listdir(folder_path)
                    if os.path.isfile(os.path.join(folder_path, archivo))
                ]

                # Agregar los nombres de los archivos al QComboBox sin la extensión .json
                for archivo in archivos:
                    nombre_sin_extension, ext = os.path.splitext(archivo)
                    # Agregar solo el nombre sin la extensión
                    combobox.addItem(nombre_sin_extension)
            except FileNotFoundError:
                print(f"La carpeta {folder_path} no existe.")
            except Exception as e:
                print(f"Error al listar archivos: {e}")
        else:
            print("No se encontró el QComboBox")

    def archivo_json_a_string(self, ruta_archivo):
        with open(ruta_archivo, 'r') as archivo:
            json_data = json.load(archivo)  # Carga el contenido del archivo JSON

        # Actualizar valores en el JSON
        json_data["nombre del jugador"] = self.nombre_jugador
        json_data["aficiones"] = self.aficiones
        json_data["edad"] = self.edad
        json_data["familiares"] = self.familiares

        return json.dumps(json_data)

    def startGame_clicked(self):
        juego = self.ui3.comboBox.currentText()

        if not juego or juego == "Seleccionar juego...":
            print("Por favor selecciona un juego.")
            return

        self.nombre_jugador = self.ui3.nombreE.toPlainText()
        self.aficiones = self.ui3.aficionE.toPlainText()
        self.edad = self.ui3.edadE.toPlainText()
        self.familiares = self.ui3.famiE.toPlainText()

        folder_path = "../juegos_story"
        archivo_json = f"{juego}.json"
        self.archivo_path = os.path.join(folder_path, archivo_json)

        self.user_info = self.archivo_json_a_string(self.archivo_path)

        print("------------ JSON ENVIADO ---------------------------------")
        print(self.user_info)
        print("------------ JSON ENVIADO ---------------------------------")

        self.ui3.nombreE.clear()
        self.ui3.aficionE.clear()
        self.ui3.edadE.clear()
        self.ui3.famiE.clear()

        print("Iniciando juego con los datos seleccionados")
        self.cerrar_ui(3)
        # SET GAME INFO
        self.gpt_proxy.setGameInfo("StoryTelling", self.user_info)
        self.lanzar_ui4()
        self.ui4.text_info.setText("EBO comenzará a hablar en breve")
        # START CHAT
        self.gpt_proxy.startChat()
        self.ui4.text_info.setText("Introduzca respuesta")

    def setDatos_clicked(self):
        self.nombre_jugador = self.ui3.nombreE.toPlainText()
        self.aficiones = self.ui3.aficionE.toPlainText()
        self.edad = self.ui3.edadE.toPlainText()
        self.familiares = self.ui3.famiE.toPlainText()

        self.ui3.startGame.setEnabled(True)

    #### UI 4 #### ################ ############################################### ################
    def respuesta_ui(self):
        ui = self.load_ui(
            UI_RESP, ui_number=4,
            logo_paths={"label": LOGO_1, "label_2": LOGO_2},
            botones={"enviar": self.enviar_clicked, "salir": self.salir_clicked,
                     "checkAutonomo": self.toggle_autonomo_clicked},
            ayuda_button="ayuda_button",
            back_button="back_button"
        )
        ui.respuesta.installEventFilter(self)

        checkbox = getattr(ui, "checkAutonomo", None)
        if checkbox:
            # Aseguramos que empieza apagado y sin modo autónomo
            checkbox.setChecked(False)
            self.autonomo = False

        return ui

    def enviar_clicked(self):
        if self.autonomo: return
        mensaje = self.ui4.respuesta.toPlainText()
        if not mensaje: return

        # Guardamos el mensaje en el historial
        self.historial_charla.append(mensaje)

        self.ui4.respuesta.clear()  # Limpiar el QTextEdit
        self.ui4.respuesta.clearFocus()  # Forzar que pierda el foco
        self.ui4.respuesta.setFocus()  # Volver a darle foco después

        self.ui4.text_info.setText("Mensaje ENVIADO, EBO está pensando...")
        QApplication.processEvents()

        self.gpt_proxy.continueChat(mensaje)
        self.ui4.text_info.setText("Introduzca respuesta")

    def salir_clicked(self):
        try:
            self.speech_proxy.say(
                f"He disfrutado mucho hoy, {self.nombre_jugador}. ¿Te gustaría que volvamos a jugar pronto?")
        except:
            pass

        respuesta = QMessageBox.question(
            self.ui4, "Confirmar salida", "¿Estás seguro de que quieres salir?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if respuesta == QMessageBox.Yes:

            if self.nombre_jugador and hasattr(self, 'historial_charla') and len(self.historial_charla) > 0:
                # Lo lanzamos en un Hilo (Thread) para que la pantalla del ordenador no se quede congelada esperando a GPT
                threading.Thread(
                    target=self.generar_resumen_background,
                    args=(self.nombre_jugador, self.historial_charla),
                    daemon=True
                ).start()

            if self.autonomo:
                self.detener_autonomo()

            self.reiniciar_variables()
            self.ui4.text_info.setText("Saliendo del programa...")
            QApplication.processEvents()
            self.cerrar_ui(4)
            self.gestorsg_proxy.LanzarApp()

            self.gpt_proxy.continueChat("03827857295769204")
        else:
            pass

    def iniciar_autonomo(self):
        """ Inicia el proceso del modo autónomo. """
        if self.autonomo:
            print("iniciar_autonomo: Ya está activo o iniciándose. No hacer nada.")
            return
            
        self.autonomo = True 
        print("iniciar_autonomo: Flag 'autonomo' puesto a True.")

        waiter_thread = threading.Thread(
            target=self.esperar_y_lanzar_autonomo,
            daemon=True
        )
        waiter_thread.start()
        print("iniciar_autonomo: Hilo observador lanzado. La GUI sigue respondiendo.")
        
    def esperar_y_lanzar_autonomo(self):
        print("Hilo observador: Esperando a que EBO termine de hablar...")
        
        try:
            while self.speech_proxy.isBusy():
                if not self.autonomo:
                    print("Hilo observador: Arranque cancelado por el usuario (mientras esperaba).")
                    return # Salir del hilo observador
                
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Hilo observador: Error comprobando isBusy(): {e}. Abortando.")
            self.autonomo = False 
            return

        if not self.autonomo:
            print("Hilo observador: Arranque cancelado justo al terminar de hablar.")
            return
            
        print("Hilo observador: Habla terminada. Lanzando hilo autónomo principal...")
        self._autonomo_thread = threading.Thread(
            target=self.ebo_autonomo_test,
            daemon=True 
        )
        self._autonomo_thread.start()
        print("Modo Autónomo INICIADO.")

    def detener_autonomo(self):
        """Pone a False la variable de control, llama a stopListening y espera a que el hilo termine (join)."""
        if self.autonomo:
            self.autonomo = False
            print("Señal de DETENCIÓN enviada al modo autónomo.")

            # PASO 1: Notificar al componente ASR que debe detener su escucha bloqueante
            try:
                # LLAMADA CLAVE: Usamos el método que implementaste en el proxy EboASR
                self.eboasr_proxy.stopListening()
                print("Llamada a eboasr_proxy.stopListening() enviada.")
            except Exception as e:
                print(f"Error al llamar a stopListening: {e}")

            # PASO 2: Esperar a que el hilo termine (Join)
            if self._autonomo_thread and self._autonomo_thread.is_alive():
                print("Esperando a que el hilo autónomo finalice...")
                # Usar un timeout (e.g., 3.0 segundos) para no bloquear indefinidamente.
                self._autonomo_thread.join(timeout=3.0)

                if self._autonomo_thread and self._autonomo_thread.is_alive():
                    # Esto indica que el hilo no terminó a tiempo, pero el proceso principal continúa.
                    print("Advertencia: El hilo autónomo no se detuvo a tiempo.")
                else:
                    print("Hilo autónomo DETENIDO correctamente.")

            self._autonomo_thread = None  # Limpiar la referencia

    def ebo_autonomo_test(self):
        while self.autonomo:
            with self._asr_lock:
                text = self.eboasr_proxy.listenandtranscript()
                print("EBO HA ESCUCHADO: ", text)

            if not self.autonomo:
                break

            if not text:
                time.sleep(0.1)
                continue

            self.historial_charla.append(text)

            self._asr_lock.acquire()

            try:
                self.gpt_proxy.continueChat(text)

                ok = self.wait_for_speech_cycle_forgiving(
                    wait_for_start_timeout=5,
                    wait_for_end_timeout=120.0,
                    poll_interval=0.05,
                    post_silence_grace=0.5,
                    fallback_wait_after_no_start=0.8
                )
                if not ok:
                    time.sleep(1.0)
            finally:
                self._asr_lock.release()

            time.sleep(0.1)

        print("Hilo del modo autónomo DETENIDO.")

    def wait_for_speech_cycle_forgiving(self,
                                        wait_for_start_timeout: float = 1.5,
                                        wait_for_end_timeout: float = 30.0,
                                        poll_interval: float = 0.05,
                                        post_silence_grace: float = 0.25,
                                        fallback_wait_after_no_start: float = 0.8) -> bool:

        start_deadline = time.time() + wait_for_start_timeout
        saw_start = False

        # 1) Esperar inicio hasta timeout
        while time.time() < start_deadline:
            try:
                if self.speech_proxy.isBusy():
                    saw_start = True
                    break
            except Exception:
                # toleramos fallos temporales de proxy
                pass
            time.sleep(poll_interval)

        if not saw_start:
            # No empezó a hablar: fallback corto y salir (modo forgiving)
            time.sleep(fallback_wait_after_no_start)
            return True

        # 2) Si empezó a hablar, esperar a que termine
        end_deadline = time.time() + wait_for_end_timeout
        while time.time() < end_deadline:
            try:
                if not self.speech_proxy.isBusy():
                    # pequeña confirmación post-silence
                    time.sleep(post_silence_grace)
                    if not self.speech_proxy.isBusy():
                        return True
                    # si volvió a activarse, seguir esperando
            except Exception:
                pass
            time.sleep(poll_interval)

        # timeout esperando a que termine de hablar
        return False

    @Slot()
    def toggle_autonomo_clicked(self, checked):
        enviar_btn = getattr(self.ui4, "enviar", None)

        if checked:
            # Modo Autónomo Activado (ON)
            self.iniciar_autonomo()

            if enviar_btn:
                enviar_btn.setEnabled(False)

            self.ui4.text_info.setText("Modo Autónomo ACTIVADO. EBO está a la escucha...")

        else:
            # Modo Autónomo Desactivado (OFF)
            self.detener_autonomo()
            if enviar_btn:
                enviar_btn.setEnabled(True)
            self.ui4.text_info.setText("Introduzca respuesta")

    ################ ############################################### ################

    def eventFilter(self, obj, event):
        """ Captura eventos de la UI """

        # Manejar eventos de cierre de ventana
        ui_number = self.ui_numbers.get(obj, None)

        if ui_number is not None and event.type() == QtCore.QEvent.Close:
            target_ui = self.ui if ui_number == 1 else getattr(self, f'ui{ui_number}', None)

            if obj == target_ui:
                respuesta = QMessageBox.question(
                    target_ui, "Cerrar", "¿Estás seguro de que quieres salir del juego?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if respuesta == QMessageBox.Yes:
                    print(f"Ventana {ui_number} cerrada por el usuario.")
                    # Si la ventana 4 se cierra con la X, detener el hilo y notificar a GPT.
                    if ui_number == 4:
                        if self.autonomo:
                            self.detener_autonomo()
                        self.gpt_proxy.continueChat("03827857295769204")

                    self.reiniciar_variables()
                    self.gestorsg_proxy.LanzarApp()
                    return False  # Permitir el cierre
                else:
                    print(f"Cierre de la ventana {ui_number} cancelado.")
                    event.ignore()  # Bloquear el cierre
                    return True  # Detener la propagación del evento

        # Manejar eventos de teclas en ui4.respuesta
        if hasattr(self, 'ui4') and obj == self.ui4.respuesta and event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.enviar_clicked()  # Llamar a la función enviar
                return True  # Indicar que el evento ha sido manejado

        return super().eventFilter(obj, event)  # Propagar otros eventos normalmente

    def cerrar_ui(self, numero):
        ui_nombre = "ui" if numero == 1 else f"ui{numero}"
        ui_obj = getattr(self, ui_nombre, None)

        if ui_obj:
            ui_obj.removeEventFilter(self)  # Desactiva el event filter
            ui_obj.close()  # Cierra la ventana
            ui_obj.installEventFilter(self)  # Reactiva el event filter
        else:
            print(f"Error: {ui_nombre} no existe en la instancia.")

    ####################################################################################################################################

    def lanzar_ui2(self):
        self.centrar_ventana(self.ui2)
        self.ui2.show()
        QApplication.processEvents()

    def lanzar_ui3(self):
        self.centrar_ventana(self.ui3)
        self.ui3.show()
        QApplication.processEvents()

    def lanzar_ui4(self):
        self.centrar_ventana(self.ui4)
        self.ui4.show()
        QApplication.processEvents()

    def startup_check(self):
        QTimer.singleShot(200, QApplication.instance().quit)

    # =============== Methods for Component Implements ==================
    # ===================================================================

    #
    # IMPLEMENTATION of StartGame method from StoryTelling interface
    #
    def StoryTelling_StartGame(self):
        self.update_ui_signal.emit()

        # print("Juego terminado o ventana cerrada")

    @Slot()
    def handle_update_ui(self):
        # Este código se ejecutará en el hilo principal
        if not self.ui:
            print("Error: la interfaz de usuario no se ha cargado correctamente.")
            return

        self.centrar_ventana(self.ui)
        self.ui.raise_()
        self.ui.show()
        QApplication.processEvents()

    # ===================================================================
    # ===================================================================

    ######################
    # From the RoboCompEboASR you can call this methods:
    # self.eboasr_proxy.listenandtranscript(...)
    # self.eboasr_proxy.stopListening(...)

    ######################
    # From the RoboCompGPT you can call this methods:
    # self.gpt_proxy.continueChat(...)
    # self.gpt_proxy.setGameInfo(...)
    # self.gpt_proxy.startChat(...)

    ######################
    # From the RoboCompGestorSG you can call this methods:
    # self.gestorsg_proxy.LanzarApp(...)

    ######################
    # From the RoboCompSpeech you can call this methods:
    # self.speech_proxy.isBusy(...)
    # self.speech_proxy.say(...)
