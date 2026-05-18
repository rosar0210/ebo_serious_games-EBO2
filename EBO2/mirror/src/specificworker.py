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
from fcntl import F_ADD_SEALS

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from rich.console import Console
from genericworker import *
import interfaces as ifaces
import numpy as np
import cv2
import mediapipe as mp
import pandas as pd
import random
import time
from time import sleep
import datetime

import sys

sys.path.append('/opt/robocomp/lib')
console = Console(highlight=False)


class SpecificWorker(GenericWorker):


    def __init__(self, proxy_map, configData, startup_check=False):
        super(SpecificWorker, self).__init__(proxy_map, configData)
        self.Period = configData["Period"]["Compute"]
        if startup_check:
            self.startup_check()
        else:
            self.timer.timeout.connect(self.compute)
            self.timer.start(self.Period)

        self.NUM_LEDS = 54

        self.imagen = None
        #Inicialización módulo de malla facial
        self.modelo = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        self.options = mp.tasks.vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=self.modelo),
            running_mode=mp.tasks.vision.RunningMode.IMAGE,
            output_face_blendshapes=True
        )
        self.landmarker = mp.tasks.vision.FaceLandmarker.create_from_options(self.options)

        self.imag_final = None

        self.ratio_bocaa_ref = None
        self.ratio_bocaa = None
        self.ratio_boca_ref = None
        self.ratio_boca = None
        self.ratio_ojos_ref = None
        self.ratio_ojos = None
        self.ratio_cejas_ref = None
        self.ratio_cejas = None
        self.calibrado = False
        self.blendshapes_base = {}

        self.mood_aleatorio = []

        self.running = False
        self.nombre = "Usuario"
        self.modo_juego = "usuario_imita"
        self.rondas = 3
        self.intentos = 2
        self.fallos = 0
        self.rondas_complet = 0
        self.responses_times = []
        self.start_time= None
        self.df = pd.DataFrame(columns=[
            "Nombre", "Intentos", "Rondas", "Modo Juego", "Fecha", "Hora",
            "Rondas completadas", "Fallos", "Tiempo transcurrido (min)", "Tiempo transcurrido (seg)",
            "Tiempo medio respuesta (seg):"
        ])



    def __del__(self):
        """Destructor"""
        cv2.destroyAllWindows()



    @QtCore.Slot()
    def compute(self):
        self.JuegoMirror_StartGame()
        return True

    def startup_check(self):
        print(f"Testing RoboCompCameraSimple.TImage from ifaces.RoboCompCameraSimple")
        test = ifaces.RoboCompCameraSimple.TImage()
        print(f"Testing RoboCompLEDArray.Pixel from ifaces.RoboCompLEDArray")
        test = ifaces.RoboCompLEDArray.Pixel()
        QTimer.singleShot(200, QApplication.instance().quit)




    # =============== Methods for Component Implements ==================
    # ===================================================================

    #
    # IMPLEMENTATION of StartGame method from JuegoMirror interface
    #
    def JuegoMirror_StartGame(self):
        console.print("Iniciando Juego Mirror...")
        self.running = True
        self.start_time = time.time()
        # Puedes obtener fecha y hora actual aquí
        ahora = datetime.datetime.now()
        self.fecha = ahora.strftime("%Y-%m-%d")
        self.hora = ahora.strftime("%H:%M:%S")

        # Lanzar la introducción en un hilo separado o llamar directamente
        self.introduccion()
        pass

    def captura_imagen(self):
        "Captura la imagen y devuelve los puntos necesarios"
        #Captura y extracción de dimensiones de la imagen
        self.imag = self.camerasimple_proxy.getImage()
        self.ancho = self.imag.width
        self.alto = self.imag.height
        self.alto = self.imag.height

        #Conversión a binario y RGB para usar OpenCV
        self.imagen = np.frombuffer(self.imag.image, dtype=np.uint8).reshape((self.alto, self.ancho, 3))
        self.imagen = cv2.cvtColor(self.imagen, cv2.COLOR_BGR2RGB)

        #Mostrar imagen
        cv2.imshow("Camara RoboComp - Juego Mirror", self.imagen)
        cv2.waitKey(20)
        # ------------------------------------------
        self.mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=self.imagen)

        #Procesado de la imagen
        self.imag_final = self.landmarker.detect(self.mp_image)

        if self.imag_final.face_blendshapes:
            return {b.category_name: b.score for b in self.imag_final.face_blendshapes[0]}
        return None

    def calibracion (self):
        "Captura la cara con emoción neutra para tener valores de referenciaq"
        puntos = self.captura_imagen()
        if puntos:
            self.ratio_bocaa_ref = puntos.get('jawOpen', 0.0)
            self.ratio_boca_ref = (puntos.get('mouthSmileLeft', 0.0) + puntos.get('mouthSmileRight',0.0)) / 2
            self.ratio_ojos_ref = (puntos.get('eyeWideLeft', 0.0) + puntos.get('eyeWideRight', 0.0)) / 2
            self.ratio_cejas_ref = (puntos.get('browDownLeft', 0.0) + puntos.get('browDownRight', 0.0)) / 2

            self.calibrado = True
            print("Calibración completada con éxito.")
            return True
        return False

    def sorprendido(self, imag_actual):
        if imag_actual is None: return False

        # Extraemos los valores del diccionario recibido
        self.ratio_bocaa = imag_actual.get('jawOpen', 0.0)
        self.ratio_ojos = (imag_actual.get('eyeWideLeft', 0.0) + imag_actual.get('eyeWideRight', 0.0)) / 2

        boca_abierta = self.ratio_bocaa > (self.ratio_bocaa_ref*1.3) or self.ratio_bocaa > 0.15
        ojos_abiertos = self.ratio_ojos > (self.ratio_ojos_ref*1.2) or self.ratio_ojos > 0.10

        # Si la boca está más abierta que en el reposo y los ojos más abiertos
        if boca_abierta and ojos_abiertos:
            return True
        return False

    def contento(self, imag_actual):
        if imag_actual is None: return False

        self.ratio_boca = (imag_actual.get('mouthSmileLeft', 0.0) + imag_actual.get('mouthSmileRight', 0.0)) / 2

        if self.ratio_boca > (self.ratio_boca_ref+0.1) or self.ratio_boca > 0.25:
            return True
        return False

    def enfadado(self, imag_actual):
        if imag_actual is None: return False

        self.ratio_cejas = (imag_actual.get('browDownLeft', 0.0) + imag_actual.get('browDownRight', 0.0)) / 2

        if self.ratio_cejas > (self.ratio_cejas_ref + 0.08) or self.ratio_cejas > 0.20:
            return True
        return False


################################ FLUJO DEL JUEGO ############################################
    def introduccion  (self):

        self.emotionalmotor_proxy.expressJoy()
        self.speech_proxy.say(f"Hola {self.nombre}, vamos a jugar a la mímica de emociones.", False)
        print(f"Hola {self.nombre}, vamos a jugar a la mímica de emociones.")
        self.terminaHablar()

        self.speech_proxy.say("Antes de nada, vamos a calibrar la cámara. Pon cara neutra y relajada y mira a la cámara.", False)
        print("Antes de nada, vamos a calibrar la cámara. Pon cara neutra y relajada y mira a la cámara.")
        self.terminaHablar()

        calibrado = False
        while not calibrado and self.running:
            calibrado = self.calibracion()
            if not calibrado:
                print("Recalibrando")
                self.speech_proxy.say("Fallo en la calibración. Recalibrando", False)
                self.terminaHablar()

        if self.modo_juego == "usuario_imita":
            self.speech_proxy.say("En este juego yo pondré una cara y tú tendrás que imitarla. "
                "Prepárate para poner tu mejor cara.", False)
            print("En este juego yo pondré una cara y tú tendrás que imitarla. Prepárate para poner tu mejor cara.")
            self.terminaHablar()
            self.usuario_imita()
        else:
            self.speech_proxy.say("En este juego tú pondrás una cara y yo intentaré imitarte. "
                "Vamos a ver lo bien que te leo.", False)
            print("En este juego tú pondrás una cara y yo intentaré imitarte. Vamos a ver lo bien que te leo.")
            self.terminaHablar()
            self.robot_imita()

    def usuario_imita(self):
        self.mood_aleatorio=[]
        i = 0

        while i < int(self.rondas) and self.running:
            self.speech_proxy.say(f"Ronda número {i+1}", False)
            print(f"Ronda número {i+1}.")
            self.rondas_complet = i +1
            self.terminaHablar()

            mood = self.random_mood()
            print(self.mood_aleatorio)
            self.mostrar_emocion(mood)
            sleep(1)

            self.start_answer_time = None
            self.get_respuesta(mood)
            print(f"La respuesta ha sido: {self.respuesta}")
            if not self.running:
                break
            i+= 1

            if i == int(self.rondas):
                self.finJuego()

    def finJuego(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time

        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)

        self.speech_proxy.say("Juego terminado", False)
        print("Juego terminado")
        self.terminaHablar()
        self.media = sum(self.responses_times)/len(self.responses_times)
        self.agregar_resultados(self.nombre, self.intentos, self.rondas, self.mod_juego, self.fecha, self.hora, self.rondas_complet, self.fallos, minutes, seconds, self.media)
        self.guardar_resultados()
        return

    def get_respuesta(self, mood):
        self.imita = False
        self.intent = 0

        if self.start_answer_time is None:
            self.start_answer_time = time.time()

        print(f"Imitación de {mood}")

        while self.running and not self.imita:
            self.respuesta = self.detectar_emocion(mood)
            sleep(3)
            if self.respuesta == True and self.running:
                self.imita = True
                self.responses_times.append(time.time()- self.start_answer_time)
                self.speech_proxy.say(f"Lo has hecho genial!", False)
                print(f"Emocion {mood} detectada")
                self.terminaHablar()

                cv2.waitKey(50)
            else:
                self.intent += 1
                self.restantes = int(self.intentos) - int(self.intent)

                self.speech_proxy.say(f"Te quedan {self.restantes} intentos", False)
                print(f"Te quedan {self.restantes} intentos.")
                self.terminaHablar()
                self.fallos += 1

                if self.restantes <= 0:
                    self.game_over()
                    return

                self.speech_proxy.say(f"No te he visto bien. Te quedan {self.restantes} intentos", False)
                self.terminaHablar()
                self.repetir_mood()

                sleep(3)
                cv2.waitKey(50)
                continue

    def detectar_emocion(self, emocion):
        imag = self.captura_imagen()

        respuesta = False

        if emocion == "alegría":
            respuesta = self.contento(imag)
        elif emocion == "ira":
            respuesta = self.enfadado(imag)
        elif emocion == "sorpresa":
            respuesta = self.sorprendido(imag)

        return respuesta



    def repetir_mood(self):
        print("Mostrando emoción nuevamente...")
        self.speech_proxy.say("Atención, voy a mostrarte de nuevo la emoción", False)
        self.speech_proxy.say("Atención, voy a mostrarte de nuevo la emoción", False)
        self.terminaHablar()
        print(self.mood_aleatorio)
        self.mostrar_emocion(self.mood_aleatorio[-1])

    def game_over(self):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time

        if len(self.responses_times) > 0:
            self.media = (sum(self.responses_times)/len(self.responses_times))
        else:
            self.media = 0.0
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        rondas = int(self.rondas_complet) - 1
        print("Game Over")
        self.speech_proxy.say("El juego ha terminado", False)
        print(f"Juego terminado. Tiempo transcurrido: {minutes} minutos y {seconds} segundos.")
        self.terminaHablar()
        self.running = False
        self.agregar_resultados(self.nombre, self.intentos, self.rondas, self.modo_juego, self.fecha, self.hora, self.rondas_complet, self.fallos, minutes, seconds, self.media)
        self.guardar_resultados()

    def terminaHablar(self):
        sleep(2.5)
        while self.speech_proxy.isBusy():
            pass
        ########## FUNCIÓN QUE GENERA LA SECUENCIA DE EMOCIONES  ##########

    def random_mood(self):
        mood = random.choice(["alegría", "ira", "sorpresa"])
        # Comprobar si el último color es el mismo que el nuevo
        while self.mood_aleatorio and self.mood_aleatorio[-1] == mood:
            mood = random.choice(["alegría", "ira", "sorpresa"])
        self.mood_aleatorio.append(mood)
        return mood

    def mostrar_emocion (self, emocion):
        self.emotionalmotor_proxy.expressJoy()
        self.set_all_LEDS_colors(red=0, green=0, blue=0, white=0)
        sleep(1)
        if isinstance(emocion, list):
            emocion = emocion[0]
        print (f"EBO expresando {emocion}")

        if emocion == "alegría":
            self.ebomoods_proxy.expressJoy()
        elif emocion == "ira":
            self.ebomoods_proxy.expressAnger()
        elif emocion == "sorpresa":
            self.ebomoods_proxy.expressSurprise()

        sleep(2.5)

    def set_all_LEDS_colors(self, red=0, green=0, blue=0, white=0):
        pixel_array = {i: ifaces.RoboCompLEDArray.Pixel(red=red, green=green, blue=blue, white=white) for i in
                       range(self.NUM_LEDS)}
        self.ledarray_proxy.setLEDArray(pixel_array)

##################################### GUARDAR RESULTADOS ###############################################################
    def agregar_resultados(self, nombre, intentos, rondas, modo_juego, fecha, hora, rondas_completadas, fallos,
                           tiempo_transcurrido_min, tiempo_transcurrido_seg, tiempo_medio_respuesta):

        # Crea un diccionario con los datos nuevos
        nuevo_resultado = {
            "Nombre": nombre,
            "Intentos": intentos,
            "Rondas": rondas,
            "Modo Juego": modo_juego,
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
        self.modo_juego = ""
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

        self.start_question_time = None
        self.end_question_time = 0
        self.response_time = 0
        self.responses_times = []
        self.media = 0

        self.df = pd.DataFrame(columns=[
            "Nombre", "Intentos", "Rondas", "Modo Juego", "Fecha", "Hora",
            "Rondas completadas", "Fallos", "Tiempo transcurrido (min)", "Tiempo transcurrido (seg)",
            "Tiempo medio respuesta (seg):"
        ])



    # ===================================================================
    # ===================================================================


    ######################
    # From the RoboCompCameraSimple you can call this methods:
    # RoboCompCameraSimple.TImage self.camerasimple_proxy.getImage()

    ######################
    # From the RoboCompCameraSimple you can use this types:
    # ifaces.RoboCompCameraSimple.TImage

    ######################
    # From the RoboCompEboMoods you can call this methods:
    # RoboCompEboMoods.void self.ebomoods_proxy.expressAnger()
    # RoboCompEboMoods.void self.ebomoods_proxy.expressDisgust()
    # RoboCompEboMoods.void self.ebomoods_proxy.expressFear()
    # RoboCompEboMoods.void self.ebomoods_proxy.expressJoy()
    # RoboCompEboMoods.void self.ebomoods_proxy.expressSadness()
    # RoboCompEboMoods.void self.ebomoods_proxy.expressSurprise()

    ######################
    # From the RoboCompEmotionalMotor you can call this methods:
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressAnger()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressDisgust()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressFear()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressJoy()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressSadness()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.expressSurprise()
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.isanybodythere(bool isAny)
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.listening(bool setListening)
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.pupposition(float x, float y)
    # RoboCompEmotionalMotor.void self.emotionalmotor_proxy.talking(bool setTalk)

    ######################
    # From the RoboCompGestorSG you can call this methods:
    # RoboCompGestorSG.void self.gestorsg_proxy.LanzarApp()

    ######################
    # From the RoboCompLEDArray you can call this methods:
    # RoboCompLEDArray.PixelArray self.ledarray_proxy.getLEDArray()
    # RoboCompLEDArray.bool self.ledarray_proxy.setLEDArray(PixelArray pixelArray)

    ######################
    # From the RoboCompLEDArray you can use this types:
    # ifaces.RoboCompLEDArray.Pixel

    ######################
    # From the RoboCompSpeech you can call this methods:
    # RoboCompSpeech.bool self.speech_proxy.isBusy()
    # RoboCompSpeech.bool self.speech_proxy.say(str text, bool overwrite)


