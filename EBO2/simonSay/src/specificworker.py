#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    Copyright (C) 2024 by YOUR NAME HERE
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


from rich.console import Console
from genericworker import *
import interfaces as ifaces
from time import sleep
import random
from PySide6 import QtUiTools
from PySide6.QtCore import Qt, QTimer, QFile, Signal, Slot, QEvent
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QPixmap
import time
import pandas as pd
from datetime import datetime
import os, warnings
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module=r"pygame\.pkgdata"
)
import pygame

# Rutas de UIs y logos
UI_BTN      = "../../igs/simon_botones.ui"
UI_MENU     = "../../igs/simon_menu.ui"
UI_CHECK    = "../../igs/botonUI.ui"
UI_START    = "../../igs/comenzarUI.ui"
LOGO_1      = "../../igs/logos/logo_euro.png"
LOGO_2      = "../../igs/logos/robolab.png"

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


# If RoboComp was compiled with Python bindings you can use InnerModel in Python
# import librobocomp_qmat
# import librobocomp_osgviewer
# import librobocomp_innermodel


class SpecificWorker(GenericWorker):
    update_ui_signal = QtCore.Signal()
    def __init__(self, proxy_map, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map)
        self.Period = 2000
        self.NUM_LEDS = 54
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

        pygame.init()

        ########## INTRODUCCIÓN DE SONIDOS  ##########
        self.sounds = {
            "rojo": pygame.mixer.Sound('src/rojo.wav'),
            "verde": pygame.mixer.Sound('src/verde.wav'),
            "azul": pygame.mixer.Sound('src/azul.wav'),
            "amarillo": pygame.mixer.Sound('src/amarillo.wav'),
            "win": pygame.mixer.Sound('src/win.wav'),
            "click": pygame.mixer.Sound('src/click.wav'),
            "game_over": pygame.mixer.Sound('src/game_over.wav'),
        }

        self.ayuda = False

        self.ui = self.load_ui()
        self.ui2 = self.therapist_ui()
        self.ui3 = self.load_check()
        self.ui4 = self.comenzar_checked()

        self.reiniciar_variables()

        ########## BATERÍA DE RESPUESTAS ##########
        self.bateria_responder = [
            "Responde ahora!",
            "Te toca responder!",
            "Es tu turno, adelante!",
            "Vamos, responde ya!",
            "Es tu momento, responde ahora!",
            "¡Adelante, es tu turno!",
            "¡Responde con confianza!",
            "¡Vamos, tú puedes responder ahora!"
        ]

        self.bateria_aciertos = [
            "¡Has acertado!",
            "¡Lo estás haciendo genial!",
            "¡Acertaste, increíble!",
            "¡Eso es correcto, muy bien hecho!",
            "¡Perfecto, acertaste!",
            "¡Muy bien, respuesta correcta!",
            "¡Qué acierto tan brillante!",
            "¡Excelente, lo conseguiste!"
        ]

        self.bateria_fallos = [
            "Fallo, pero no te preocupes!",
            "No pasa nada, todos fallamos!",
            "Sigue intentándolo, ¡lo harás mejor!",
            "Es un error, pero no te rindas!",
            "¡Ánimo, la próxima será mejor!",
            "¡No te preocupes, sigue adelante!",
            "¡Un tropiezo no define tu esfuerzo!",
            "¡No pasa nada, la práctica hace al maestro!"
        ]

        self.bateria_rondas = [
            "Es hora de la ronda número {ronda}!",
            "¡Ronda número {ronda}, vamos allá!",
            "¡Toca la ronda número {ronda}!",
            "Preparados para la ronda número {ronda}!",
            "Comienza la ronda número {ronda}, ¡suerte!",
            "¡Atentos, comienza la ronda {ronda}!",
            "¡Vamos con la emocionante ronda número {ronda}!",
            "¡Que comience la ronda número {ronda}, mucha suerte!"
        ]

        self.bateria_fin_juego = [
            "El juego ha terminado, ¡lo has hecho genial!",
            "¡Fin del juego, muy bien jugado!",
            "Esto ha sido todo, ¡excelente trabajo!",
            "¡Gran final, lo hiciste estupendamente!",
            "Juego terminado, ¡felicitaciones por tu esfuerzo!",
            "¡Increíble, has completado el juego!",
            "¡Fantástico, qué gran partida!",
            "¡Finalizado, te has lucido!"
        ]
        
        self.update_ui_signal.connect(self.handle_update_ui)

    def load_ui_generic(self, ui_path, ui_number, *, logo_paths=None, botones=None,
                        ayuda_button=None, back_button=None, after_load=None):
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

    def back_clicked_ui(self, ui_number):
        self.cerrar_ui(ui_number)
        self.gestorsg_proxy.LanzarApp()

    ########## FUNCIÓN PARA AGREGAR LOS DATOS RECOGIDOS AL DATAFRAME ##########
    def agregar_resultados(self, nombre, intentos, rondas, dificultad, fecha, hora, rondas_completadas, fallos, tiempo_transcurrido_min, tiempo_transcurrido_seg, tiempo_medio_respuesta):
        # Crea un diccionario con los datos nuevos
        nuevo_resultado = {
            "Nombre": nombre,
            "Intentos": intentos,
            "Rondas": rondas,
            "Dificultad": dificultad,
            "Fecha": fecha,
            "Hora": hora,
            "Rondas completadas": rondas_completadas,
            "Fallos": fallos,
            "Tiempo transcurrido (min)": tiempo_transcurrido_min,
            "Tiempo transcurrido (seg)": tiempo_transcurrido_seg,  # Corregido aquí
            "Tiempo medio respuesta (seg):": tiempo_medio_respuesta  # Corregido aquí
        }

        # Convierte el diccionario en un DataFrame de una fila
        nuevo_df = pd.DataFrame([nuevo_resultado])

        # Agrega la nueva fila al DataFrame existente
        self.df = pd.concat([self.df, nuevo_df], ignore_index=True)
    


    def __del__(self):
        """Destructor"""

    def setParams(self, params):
        # try:
        #	self.innermodel = InnerModel(params["InnerModelPath"])
        # except:
        #	traceback.print_exc()
        #	print("Error reading config params")
        return True

    ########## FUNCIÓN PARA ALEATORIZAR RESPUESTAS ##########

    def elegir_respuesta(self, bateria, **kwargs):
        if "ronda" in kwargs:
            # Si el kwargs contiene 'ronda', formatea las respuestas de las rondas
            bateria = [respuesta.format(ronda=kwargs["ronda"]) if "ronda" in respuesta else respuesta for respuesta in
                       bateria]
        return random.choice(bateria)

    ########## FUNCIONES PARA EL PROCESO DEL JUEGO  ##########
    def procesoJuego(self):
        if self.dificultad == "facil":
            self.v1 = 2
            self.v2 = 1
        elif self.dificultad == "medio":
            self.v1 = 1
            self.v2 = 0.5
        elif self.dificultad == "dificil":
            self.v1 = 0.5
            self.v2 = 0.25
        else:
            self.v1 = 1
            self.v2 = 0.5

        self.color_aleatorio = []
        i = 0
        sleep(0.5)

        while i < int(self.rondas) and self.running:
            self.speech_proxy.say(self.elegir_respuesta(self.bateria_rondas, ronda= i+1), False)
            print(f"Ronda número {i + 1}")
            self.rondas_complet = i+1
            self.terminaHablar()
            self.random_color()
            print(self.color_aleatorio)
            for color in self.color_aleatorio:
                self.encender_LEDS(color)
                sleep(self.v1)
                self.encender_LEDS("negro")
                sleep(self.v2)

            self.start_question_time = None
            self.get_respuesta()
            print("Tu respuesta ha sido:", self.respuesta)
            if not self.running:
                break
            i += 1

        if i == int(self.rondas):
            self.finJuego()

    def finJuego(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time  # Tiempo en segundos
        # Convertir el tiempo a minutos y segundos
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        self.speech_proxy.say(self.elegir_respuesta(self.bateria_fin_juego), False)
        print(f"Juego terminado. Tiempo transcurrido: {minutes} minutos y {seconds} segundos.")
        self.terminaHablar()
        pygame.mixer.stop()
        self.sounds["win"].play()
        self.set_all_LEDS_colors(0, 255, 0, 0)
        self.emotionalmotor_proxy.expressSurprise()
        sleep(0.5)
        self.encender_LEDS("negro")
        sleep(0.5)
        self.boton = False
        self.media = sum(self.responses_times) / len(self.responses_times)
        self.agregar_resultados(self.nombre, self.intentos, self.rondas, self.dificultad, self.fecha, self.hora, self.rondas_complet, self.fallos, minutes, seconds, self.media)
        self.guardar_resultados()
        self.gestorsg_proxy.LanzarApp()
        return

    ########## FUNCIÓN QUE GENERA LA SECUENCIA DE COLORES  ##########
    def random_color(self):
        color = random.choice(["rojo", "azul", "verde", "amarillo"])
        # Comprobar si el último color es el mismo que el nuevo
        while self.color_aleatorio and self.color_aleatorio[-1] == color:
            color = random.choice(["rojo", "azul", "verde", "amarillo"])
        self.color_aleatorio.append(color)

    ########## FUNCIÓN PARA ENCENDER LAS LUCES LEDS ##########
    def encender_LEDS(self,color):
        if color == "rojo" and self.gameOver:
            self.sounds["game_over"].play()
        elif color in self.sounds:
            pygame.mixer.stop()
            self.sounds[color].play()
        if color== "negro":
            self.set_all_LEDS_colors(0, 0, 0, 0)
        elif color == "rojo":
            self.set_all_LEDS_colors(255, 0, 0, 0)
        elif color== "verde":
            self.set_all_LEDS_colors(0, 255, 0, 0)
        elif color == "azul":
            self.set_all_LEDS_colors(0, 0, 255, 0)
        elif color == "amarillo":
            self.set_all_LEDS_colors(255, 255, 0, 0)
        else:
            print("Error, apagando LEDS")
            self.set_all_LEDS_colors(0, 0, 0, 0)

    def set_all_LEDS_colors(self, red=0, green=0, blue=0, white=0):
        pixel_array = {i: ifaces.RoboCompLEDArray.Pixel(red=red, green=green, blue=blue, white=white) for i in
                       range(self.NUM_LEDS)}
        self.ledarray_proxy.setLEDArray(pixel_array)

    ########## INTRODUCCIÓN AL JUEGO  ##########
    def introduccion (self):

        QApplication.processEvents()

        # Introducción al juego
        self.emotionalmotor_proxy.expressJoy()
        self.speech_proxy.say(f"Hola {self.nombre}, vamos a jugar a Simón Dice.", False)
        print (f"Hola {self.nombre}, vamos a jugar a Simón Dice.")
        self.speech_proxy.say("Simón Dice es un juego de memoria en el que debes repetir la secuencia de colores que se ilumina. ", False)
        print("Simón Dice es un juego de memoria en el que debes repetir la secuencia de colores que se ilumina. ")
        self.speech_proxy.say ("¿Quieres que te explique el juego?", False)
        print("¿Quieres que te explique el juego?")
        self.terminaHablar()

        self.check = ""
        self.centrar_ventana(self.ui3)
        self.ui3.show()
        QApplication.processEvents()
        self.ui3.exec_()

        # Explicación del Juego
        if self.check == "si":
            self.speech_proxy.say("A medida que avances, la secuencia se volverá más larga, poniendo a prueba tu memoria y concentración. "
                                  "Cómo jugar: Se mostrará un color en mis luces, por ejemplo rojo. ", False)
            print ("A medida que avances, la secuencia se volverá más larga, poniendo a prueba tu memoria y concentración. "
                                  "Cómo jugar: Se mostrará un color en mis luces, por ejemplo rojo. ")
            self.terminaHablar()
            self.set_all_LEDS_colors(255, 0, 0, 0)
            sleep(1)
            self.set_all_LEDS_colors(0,0,0,0)
            self.speech_proxy.say("Deberás introducir ese mismo color. "
                                  "Al acertar, añadiré otro color a la secuencia, por ejemplo rojo + azul). ", False)
            print("Deberás introducir ese mismo color. "
                                  "Al acertar, añadiré otro color a la secuencia, por ejemplo rojo + azul). ")
            self.terminaHablar()
            self.set_all_LEDS_colors(255, 0, 0, 0)
            sleep(1)
            self.set_all_LEDS_colors(0, 0, 0, 0)
            sleep(1)
            self.set_all_LEDS_colors(0, 0, 255, 0)
            sleep(1)
            self.set_all_LEDS_colors(0, 0, 0, 0)
            self.speech_proxy.say("Ahora debes repetir ambos en el orden correcto. "
                                  "Con cada turno, la secuencia crece y debes recordar cada color en el orden correcto.", False)
            print("Ahora debes repetir ambos en el orden correcto. "
                                  "Con cada turno, la secuencia crece y debes recordar cada color en el orden correcto.")

        # Prueba de juego
        self.speech_proxy.say("¿Quieres hacer una prueba?", False)
        print("¿Quieres hacer una prueba?")
        self.terminaHablar()

        self.check = ""
        self.centrar_ventana(self.ui3)
        self.ui3.show()
        self.ui3.exec_()

        if self.check == "si":
            self.prueba()
        if self.check == "no":
            if int(self.intentos) == 1:
                self.speech_proxy.say("Vamos a ver cuánto tiempo eres capaz de seguir la secuencia sin equivocarte", False)
                print("Vamos a ver cuánto tiempo eres capaz de seguir la secuencia sin equivocarte")
            elif int(self.intentos) > 1:
                self.speech_proxy.say(f"""Tienes un número limitado de intentos. Si te equivocas en algún color {self.intentos}
                                        veces antes de completar la secuencia, el juego terminará.""", False)
                print(f"""Tienes un número limitado de intentos. Si te equivocas en algún color {self.intentos}
                                        veces antes de completar la secuencia, el juego terminará.""")
            self.speech_proxy.say("¡Comencemos con el juego!", False)
            print("¡Comencemos con el juego!")

        self.terminaHablar()

        self.centrar_ventana(self.ui4)
        self.ui4.show()
        self.ui4.exec_()
        self.start_time =time.time()
        self.fecha = datetime.now().strftime("%d-%m-%Y")
        self.hora = datetime.now().strftime("%H:%M:%S")

    ########## FUNCIÓN PARA OBTENER LA RESPUESTA  ##########
    def get_respuesta(self):
        self.respuesta = []
        self.intent = 0

        if self.start_question_time is None:
            self.start_question_time = time.time()

        print("Introduce la secuencia de colores uno a uno")

        # Bucle de la ronda: hasta que el usuario iguale la longitud de la secuencia o termine el juego
        while self.running and len(self.respuesta) < len(self.color_aleatorio):
            # Mostrar UI y procesar eventos
            self._mostrar_ui_botones()

            # ¿El prefijo actual coincide con la secuencia objetivo?
            if not self._chequear_prefix_ok():
                self.intent += 1
                self.restantes = int(self.intentos) - int(self.intent)

                # Feedback de intentos
                self.speech_proxy.say(self._mensaje_intentos(self.restantes), False)
                self.cerrar_ui(1)
                self.terminaHablar()
                self.fallos += 1

                # Sin intentos: GAME OVER
                if self.restantes <= 0:
                    self._game_over()
                    return

                # Repetir secuencia y reiniciar respuesta parcial
                self.respuesta = []
                self._repetir_secuencia()
                # vuelve al while (no incrementamos nada)
                continue

        # Si hemos salido del while por éxito y el juego sigue vivo, cierre de ronda
        if self.running:
            self.cerrar_ui(1)
            self.speech_proxy.say(self.elegir_respuesta(self.bateria_aciertos), False)
            self.terminaHablar()
            print("Tu respuesta ha sido:", self.respuesta)

    def _mostrar_ui_botones(self):
        """Muestra la UI de botones centrada y procesa eventos."""
        self.centrar_ventana(self.ui)
        self.ui.show()
        QApplication.processEvents()
        self.emotionalmotor_proxy.expressJoy()

    def _chequear_prefix_ok(self):
        """Comprueba si la respuesta actual coincide con el prefijo de la secuencia."""
        for idx, col in enumerate(self.respuesta):
            if col != self.color_aleatorio[idx]:
                return False
        return True

    def _mensaje_intentos(self, restantes: int) -> str:
        if restantes > 1:
            return f"Respuesta incorrecta. {self.elegir_respuesta(self.bateria_fallos)} .Te quedan {restantes} intentos."
        if restantes == 1:
            return f"Respuesta incorrecta. {self.elegir_respuesta(self.bateria_fallos)}.Este es tu último intento."
        return "Respuesta incorrecta, no te quedan más intentos."

    def _repetir_secuencia(self):
        """Vocaliza aviso y repite la secuencia luminosa completa."""
        print("Mostrando la secuencia nuevamente...")
        self.speech_proxy.say("Atención, repito la secuencia.", False)
        self.terminaHablar()
        print(self.color_aleatorio)
        for color in self.color_aleatorio:
            self.encender_LEDS(color)
            sleep(self.v1)
            self.encender_LEDS("negro")
            sleep(self.v2)

    def _game_over(self):
        """Cierra partida guardando resultados y lanzando el menú."""
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time  # seg
        self.media = (sum(self.responses_times) / len(self.responses_times)) if self.responses_times else 0.0
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        rondas = int(self.rondas_complet) - 1
        print("Game Over")
        self.speech_proxy.say(self.elegir_respuesta(self.bateria_fin_juego), False)
        print(f"Juego terminado. Tiempo transcurrido: {minutes} minutos y {seconds} segundos.")
        self.terminaHablar()
        self.fantasia_color()
        self.running = False
        self.boton = False
        self.agregar_resultados(self.nombre, self.intentos, self.rondas, self.dificultad,
                                self.fecha, self.hora, rondas, self.fallos, minutes, seconds, self.media)
        self.guardar_resultados()
        self.gestorsg_proxy.LanzarApp()

    def fantasia_color(self, veces: int = 3):
        self.emotionalmotor_proxy.expressJoy()
        self.gameOver = True
        for _ in range(veces):
            self.encender_LEDS("rojo");
            sleep(0.5)
            self.encender_LEDS("negro");
            sleep(0.5)
        self.gameOver = False

    def prueba (self):
        self.speech_proxy.say("¡Genial! Comencemos con la prueba. Vamos a hacer 2 rondas",False)

        print("¡Genial! Comencemos con la prueba. Vamos a hacer 2 rondas")

        self.terminaHablar()

        self.color_aleatorio = []
        self.running = True
        i = 0
        while i <= 1 and self.running:
            self.speech_proxy.say(f"Ronda número {i + 1}", False)
            print(f"Ronda número {i + 1}")
            self.terminaHablar()
            self.random_color()
            print(self.color_aleatorio)

            for color in self.color_aleatorio:
                self.encender_LEDS(color)
                sleep(1)
                self.encender_LEDS("negro")
                sleep(0.5)

            self.get_respuesta()
            print("Tu respuesta ha sido:", self.respuesta)
            i += 1

        if i == 2:
            self.running = False
            self.speech_proxy.say ("¡Lo has hecho muy bien!",False)
            print("¡Lo has hecho muy bien!")

    def terminaHablar(self):
        sleep(2.5)
        while self.speech_proxy.isBusy():
            pass

                        ########## INTERFACES GRÁFICAS ##########
    ####################################################################################################################################

    def load_ui(self):
        ui = self.load_ui_generic(
            UI_BTN, ui_number=1,
            botones={
                "rojo": (lambda: self.color_clicked("rojo")),
                "azul": (lambda: self.color_clicked("azul")),
                "verde": (lambda: self.color_clicked("verde")),
                "amarillo": (lambda: self.color_clicked("amarillo"))
            }
        )
        return ui

    def color_clicked(self, color: str):
        self.respuesta.append(color)
        if color in self.sounds:
            self.sounds[color].play()
        self.register_time_until_pressed()
        print(f"Respuesta: {color.capitalize()}")
    
    def register_time_until_pressed(self):
        if self.end_question_time is None:
            self.end_question_time = time.time()
        
        self.response_time = self.end_question_time - self.start_question_time
        if self.response_time < 0.00001:
            print("Error, valor no almacenado")
        else:
            self.responses_times.append(self.response_time)

        self.start_question_time = None
        self.end_question_time = None

        if self.start_question_time is None:
            self.start_question_time = time.time()
        
        print("------------------------------")
        print(f"Tiempo de respuesta: {self.response_time}")
        print("------------------------------")

    ####################################################################################################################################

    def therapist_ui(self):
        # UI 2: menú (terapeuta)
        ui = self.load_ui_generic(
            UI_MENU, ui_number=2,
            logo_paths={"label": LOGO_1, "label_3": LOGO_2},
            botones={
                "facil": self.facil_clicked,
                "medio": self.medio_clicked,
                "dificil": self.dificil_clicked,
                "confirmar_button": self.therapist,
            },
            ayuda_button="ayuda_button",
            back_button="back_button",
            after_load=lambda u: (hasattr(u, "ayuda") and u.ayuda.hide())
        )
        return ui

    def facil_clicked(self):
        self.dificultad = "facil"
        self.sounds["click"].play()
        self.ui2.dificultad_elegida.setText("Dificultad elegida: Fácil")
        print("Dificultad elegida: Fácil")
    def medio_clicked(self):
        self.dificultad = "medio"
        self.sounds["click"].play()
        self.ui2.dificultad_elegida.setText("Dificultad elegida: Medio")
        print("Dificultad seleccionada: Medio")

    def dificil_clicked(self):
        self.dificultad = "dificil"
        self.sounds["click"].play()
        self.ui2.dificultad_elegida.setText("Dificultad elegida: Difícil")
        print("Dificultad seleccionada: Difícil")

    def therapist(self):
        # Obtiene los valores ingresados en los campos
        self.nombre = self.ui2.usuario.toPlainText()
        self.intentos = self.ui2.intentos.toPlainText()
        self.rondas = self.ui2.rondas.toPlainText()
        # Validaciones simples
        if not self.nombre:
            print("Por favor ingresa un nombre de usuario.")
            return
        if not self.intentos.isdigit() or int(self.intentos) <= 0:
            print("Por favor ingresa un número válido de intentos.")
            return
        if not self.rondas.isdigit() or int(self.rondas) <= 0:
            print("Por favor ingresa un número válido de rondas.")
            return
        if not self.dificultad:
            print("Por favor selecciona una dificultad.")
            return

        # Muestra los valores en consola
        self.set_all_LEDS_colors(0, 0, 0, 0)
        print(f"Usuario: {self.nombre}")
        print(f"Intentos: {self.intentos}")
        print(f"Rondas: {self.rondas}")
        print(f"Dificultad: {self.dificultad}")
        print("Valores confirmados. Juego listo para comenzar.")
        self.boton = True
        self.fallos = 0 # Reinicia contador al empezar juego
        self.sounds["click"].play()
        self.cerrar_ui(2)
        self.ui2.usuario.clear()
        self.ui2.intentos.clear()
        self.ui2.rondas.clear()
        self.introduccion()
        self.procesoJuego()

    ####################################################################################################################################

    def load_check(self):
        # UI 3: diálogo sí/no
        ui = self.load_ui_generic(
            UI_CHECK, ui_number=3,
            botones={
                "si": self.si_clicked,
                "no": self.no_clicked,
            }
        )
        return ui

    def si_clicked(self):
        self.check = "si"
        print("Respuesta: Sí")
        self.ui3.accept()  # Cierra el diálogo cuando el botón es presionado
        self.sounds["click"].play()

    def no_clicked(self):
        self.check = "no"
        print("Respuesta: No")
        self.ui3.accept()  # Cierra el diálogo cuando el botón es presionado
        self.sounds["click"].play()
        
    ####################################################################################################################################

    def comenzar_checked(self):
        # UI 4: diálogo comenzar
        ui = self.load_ui_generic(
            UI_START, ui_number=4,
            botones={"comenzar": self.comenzar}
        )
        return ui

    def comenzar (self):
        self.running = True
        print("¡El juego ha comenzado!")
        self.ui4.accept()  # Cierra el diálogo cuando el botón es presionado
        self.sounds["click"].play()

    ####################################################################################################################################
    
    def eventFilter(self, obj, event):
        """ Captura eventos de la UI """
        # Obtener el número de UI asociado al objeto
        ui_number = self.ui_numbers.get(obj, None)
        if ui_number is not None and event.type() == QtCore.QEvent.Close:
            target_ui = self.ui if ui_number == 1 else getattr(self, f'ui{ui_number}', None)
            if obj == target_ui:
                respuesta = QMessageBox.question(
                    target_ui, "Cerrar", f"¿Estás seguro de que quieres salir del juego?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if respuesta == QMessageBox.Yes:
                    print(f"Ventana {ui_number} cerrada por el usuario.")
                    self.reiniciar_variables()
                    self.set_all_LEDS_colors(0, 0, 0, 0)
                    self.gestorsg_proxy.LanzarApp()
                    return False  # Permitir el cierre
                else:
                    print(f"Cierre de la ventana {ui_number} cancelado.")
                    event.ignore()  # Bloquear el cierre
                    return True  # **DETENER la propagación del evento para que no se cierre**
        return False  # Propaga otros eventos normalmente
    
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

    def guardar_resultados(self):
        archivo = "resultados_juego.json"
        # Inicializar un DataFrame vacío para los datos existentes
        datos_existentes = pd.DataFrame()
        # Intentar leer el archivo existente si existe
        if os.path.exists(archivo):
            try:
                datos_existentes = pd.read_json(archivo, orient='records', lines=True)
            except ValueError:
                print("El archivo JSON existente tiene un formato inválido o está vacío. Sobrescribiendo el archivo.")

        # Verificar que el DataFrame actual no esté vacío
        if self.df.empty:
            print("El DataFrame de nuevos resultados está vacío. No se guardará nada.")
            return

        # Concatenar los datos existentes con los nuevos (si existen)
        if not datos_existentes.empty:
            self.df = pd.concat([datos_existentes, self.df], ignore_index=True)

        # Eliminar duplicados basados en todas las columnas
        self.df = self.df.drop_duplicates()
        # Guardar el DataFrame combinado en formato JSON
        self.df.to_json(archivo, orient='records', lines=True)
        print(f"Resultados guardados correctamente en {archivo}")
        # Leer y mostrar el archivo actualizado para verificar
        df_resultados = pd.read_json(archivo, orient='records', lines=True)
        print(df_resultados)
        # Reiniciar la variable self.df para la próxima partida
        self.reiniciar_variables()
        print("Variable self.df reiniciada para la próxima partida.")

    def reiniciar_variables(self):
        self.nombre = ""
        self.dificultad = ""
        self.intentos = 0
        self.running = False
        self.respuesta = []
        self.rondas = ""
        
        self.boton = False
        self.reiniciar = False
        self.gameOver = False
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None

        self.rondas_complet = 0
        self.fecha = 0
        self.hora = 0
        self.fallos = 0

        self.v1 = 2
        self.v2 = 1

        self.start_question_time = None
        self.end_question_time = 0
        self.response_time = 0
        self.responses_times = []
        self.media = 0

        self.df = pd.DataFrame(columns=[
            "Nombre", "Intentos", "Rondas", "Dificultad", "Fecha", "Hora",
            "Rondas completadas", "Fallos", "Tiempo transcurrido (min)", "Tiempo transcurrido (seg)", "Tiempo medio respuesta (seg):"
        ])


    @QtCore.Slot()
    def compute(self):

        return True

    def startup_check(self):
        print(f"Testing RoboCompCameraSimple.TImage from ifaces.RoboCompCameraSimple")
        test = ifaces.RoboCompCameraSimple.TImage()
        print(f"Testing RoboCompLEDArray.Pixel from ifaces.RoboCompLEDArray")
        test = ifaces.RoboCompLEDArray.Pixel()
        QTimer.singleShot(200, QApplication.instance().quit)

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

    # =============== Methods for Component Implements ==================
    # ===================================================================

    #
    # IMPLEMENTATION of StartGame method from JuegoSimonSay interface
    #
    def JuegoSimonSay_StartGame(self):
        self.set_all_LEDS_colors(255,0,0,0)
        self.update_ui_signal.emit()
        # pass

    @QtCore.Slot()
    def handle_update_ui(self):
        # Este código se ejecutará en el hilo principal
        if not self.ui2:
            print("Error: la interfaz de usuario no se ha cargado correctamente.")
            return

        self.centrar_ventana(self.ui2)
        self.ui2.raise_()
        self.ui2.show()
        QApplication.processEvents()

    # ===================================================================
    # ===================================================================


    ######################
    # From the RoboCompCameraSimple you can call this methods:
    # self.camerasimple_proxy.getImage(...)

    ######################
    # From the RoboCompCameraSimple you can use this types:
    # RoboCompCameraSimple.TImage

    ######################
    # From the RoboCompEmotionalMotor you can call this methods:
    # self.emotionalmotor_proxy.expressAnger(...)
    # self.emotionalmotor_proxy.expressDisgust(...)
    # self.emotionalmotor_proxy.expressFear(...)
    # self.emotionalmotor_proxy.expressJoy(...)
    # self.emotionalmotor_proxy.expressSadness(...)
    # self.emotionalmotor_proxy.expressSurprise(...)
    # self.emotionalmotor_proxy.isanybodythere(...)
    # self.emotionalmotor_proxy.listening(...)
    # self.emotionalmotor_proxy.pupposition(...)
    # self.emotionalmotor_proxy.talking(...)

    ######################
    # From the RoboCompGestorSG you can call this methods:
    # self.gestorsg_proxy.LanzarApp(...)

    ######################
    # From the RoboCompLEDArray you can call this methods:
    # self.ledarray_proxy.getLEDArray(...)
    # self.ledarray_proxy.setLEDArray(...)

    ######################
    # From the RoboCompLEDArray you can use this types:
    # RoboCompLEDArray.Pixel

    ######################
    # From the RoboCompSpeech you can call this methods:
    # self.speech_proxy.isBusy(...)
    # self.speech_proxy.say(...)


