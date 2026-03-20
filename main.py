#main struc 0.3 (MVP Ideal)
    #Classes:
        #AI
            #Azul
            #Rosa
            #hear
        #speak
    

    #flujo:
        #input: escrito <--------> escucha
        #    filtra/limpia       pasa a texto
        #           |            filtra/limpia
        #           |__________________|
        #                    |
        #               decide comando
        #    ___________________|_______________
        #    |                  |               |
        #ejecuta              habla           aprende
        #anuncia result.        |          anuncia result.
        #       |_______________|____________|
        #                  |
        #             restart loop


    #NOTAS
    #Mistral parece poder darte la base necesaria. Pero tendré que finetunearla.


    #--------------------------------------------------------------------------------------------------------#
    #--------------------------------------------------------------------------------------------------------#
#Herramientas prescindibles
def debug_print(text):
    print("[DEBUG]*|*|*|*|*|*"+text)

import json                             
import sounddevice as sd               
import numpy as np                     
import queue                            
import keyboard                        
import re           
from pywhispercpp.model import Model   
import os                               
import sqlite3   
import threading                       
import time
from llama_cpp import Llama

#===================================================================================================#
#                   misc. functions                                                                 #
#===================================================================================================#

class Violetta:
    def __init__(self):
        debug_print(os.getcwd())
        with open("config.json", "r", encoding="utf-8") as f:
            parameters = json.load(f)
            self.Celeste=Celeste(parameters["celeste"]["db"],parameters["celeste"]["model"],parameters["celeste"]["ai_enabled"])
            self.Rosa=Rosa(parameters["rosa"]["db"],parameters["rosa"]["diccionario_base"],parameters["rosa"]["model"],parameters["rosa"]["ai_enabled"])
            self.Listener=Listener(parameters["listener"]["model"],parameters["listener"]["samplerate"],parameters["listener"]["hear"],parameters["listener"]["wait"])
            self.Speaker=Speaker(parameters["speaker"]["model"],parameters["speaker"]["talk"],parameters["speaker"]["sh"],parameters["speaker"]["repetir"])
            self.cola_inputs=queue.Queue()
            self.charla=parameters["violetta"]["charla"]
            self.quit_com=parameters["violetta"]["quitc"]
            self.hear_com=parameters["violetta"]["hearc"]
            self.deaf_com=parameters["violetta"]["deafc"]
            self.charlar=parameters["violetta"]["charc"]
            self.exc=parameters["violetta"]["excc"]
            self.main_loop()

    def main_loop(self):
        #creando hilos
        self.t_in_read=threading.Thread(target=self.read_in, daemon=True)
        self.t_in_hear=threading.Thread(target=self.hear_in, daemon=True)
        self.t_consumidor=threading.Thread(target=self.consumidor_inputs, daemon=True)
        #lanzando hilos
        self.t_in_read.start()
        #self.t_in_hear.start()
        self.t_consumidor.start()
        #pa que no cierre
        self.t_in_read.join()
        #self.t_in_hear.join()
        self.t_consumidor.join()


    def consumidor_inputs(self):
        while True:
            chan, entrada = self.cola_inputs.get()
            if entrada is not "":
                debug_print(entrada)
                self.decide(entrada)
                self.cola_inputs.task_done()
            time.sleep(0.1)
    
    def read_in(self):
        while True:
            self.cola_inputs.put(('read', self.filter_wish(input("[VIOLETTA]**Qué quisieras que haga ahora?" \
            ""))))
    
    def hear_in(self):
        while True:
            self.cola_inputs.put(('hear', self.filter_wish(self.Listener.listen())))
    
    def filter_wish(self,raw_wish):
        raw_wish = raw_wish or ""
        return re.sub(r'[^a-z0-9 _()"]', '', raw_wish.lower())

    def decide(self,elemento):
        if elemento in self.quit_com:
            exit()
        elif elemento in self.hear_com:
            self.Listener.hear=True
        elif elemento in self.deaf_com:
            self.Listener.hear=False
        elif elemento in self.charlar:
            self.charla=True
        elif elemento in self.exc:
            self.charla=False
        elif self.charla==True:
            self.Rosa.respuesta(elemento)
        else:
            self.Rosa.respuesta(self.Celeste.execute_wish(elemento))

                
        
class Celeste:
    def __init__(self, db, model, enabled):
        self.data_base = db
        self.data = sqlite3.connect(self.data_base)
        self.data_cursor = self.data.cursor()
        self.ai_enabled = enabled
        if self.ai_enabled:
            debug_print(model)
            self.model = Llama(
            model_path=model,
            n_ctx=2048,
            n_threads=8
            )

    def execute_wish(self,wish):
        if self.ai_enabled:
            wish = self.model(wish,max_tokens=50)
        if os.path.exists(self.data_base):
            self.data_cursor.execute("SELECT script FROM commands WHERE alias = ?", (wish,))
            row = self.data_cursor.fetchone()
            if row:
                execution = "aux_scripts." + row[0]
                debug_print(execution)
                exec(execution)
                hice = "el usuario te pidio que hagas " + wish + ", hiciste," + execution
            else:
                hice = self.learn_new_command(wish)
        else: 
            hice = self.learn_new_command(wish)
        return hice


    def learn_new_command(self,command):
        self.data_cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            alias TEXT PRIMARY KEY,
            script TEXT
        )
        ''')
        print (f"[AZUL]**Me pediste: {command}, no obstante no tengo esa acción incorporada. Ayudame a configurarla! \n")
        #now let´s learn that command or arguments (a bunch of if´s and some other scripts and arguments)
        hice = "el usuario te pidio que hagas " + command + ", no hiciste nada. no tenes ese comando, el usuario no quiso configurarlo ahora"

        func_name = input("[AZUL]**Nombre de la función?\n[AZUL]**Si te arrepentiste, podés echarte atrás con back, quit, salir, y otras expresiones similares.\n")
        if func_name.lower() in ["salir", "exit", "quit", "back", "atras", "volver"]:
            return hice
        new = input("[AZUL]**Es una función nueva?\n")#-----------------------agregar los chequeos para que no pregunte bobadas cuando coincide con funcion existente
        if new.lower() in ["yes", "si", "y", "s", "sep", "yeah"]:
            self.write_new_function()  
        argsbase =  input("[AZUL]**Qué argumentos usa?\n[AZUL]**Ejemplo:\n[AZUL]**1,pizza,doom")
        args = [x.strip() for x in argsbase.split(",")]
        for arg in args:
            self.data_cursor.execute("SELECT path FROM path WHERE element = ?", (arg,))
            row = self.data_cursor.fetchone()
            if not row:
                ispath = input ("[AZUL]**Este argumento es una ruta a un archivo/carpeta?")
                if ispath.lower() in ["yes", "si", "y", "s", "sep", "yeah"]:
                    arg_path =  input("[AZUL]**Cuál?\n[AZUL]**Ejemplo:\n[AZUL]**c/users/user/desktop")#------------desde aca
                    mapping_arg = (arg,arg_path)
                    self.data_cursor.execute("INSERT OR REPLACE INTO path VALUES (?, ?)", mapping_arg)
                    self.data.commit()
        listadoargs = ', '.join(f'"{x}"' for x in args)
        script = func_name + "(" + listadoargs + ")"
        mappings = (command, script)
        self.data_cursor.execute("INSERT OR REPLACE INTO commands VALUES (?, ?)", mappings)
        self.data.commit()
        hice = "el usuario te pidio que hagas " + command + ", aprendiste el comando e hiciste " + command        
        return hice 


    def write_new_function():
        need_user = "yes"
        if need_user == "yes":
            print("[AZUL]**No puedo escribir código todavía.\n[AZUL]**Necesito que lo hagas por mí, ok?")
        else:
            return "yes"


class Rosa:
    def __init__(self, db, diccionario_base, model, enabled):
        self.data_base = db
        self.diccionario_base = diccionario_base
        self.data = sqlite3.connect(self.data_base)
        self.data_cursor = self.data.cursor()
        self.ai_enabled=enabled
        if self.ai_enabled:
            debug_print(model)
            self.model = Llama(
            model_path=model,
            n_ctx=2048,
            n_threads=8
            )
    def respuesta (self,inpuct):
        if self.ai_enabled:
            response = self.model(inpuct,max_tokens=50)
        else:
            response = self.calculate_response_no_ai(inpuct) #calcular de forma manual, probablemente con otra función
        print(f"\n[ROSA]** {response}")

    def calculate_response_no_ai (self,inpuct):
        if inpuct.startswith("el usuario te pidio que hagas"):
            inpuct = "Esto es lo que se me pidió:\n"
        else:
            inpuct = self.diccionario_base.get(inpuct,inpuct)
        return inpuct


class Listener:    #------------------------------REHACER COMPLETO BASADO EN AUDIO TO TEXT
    def __init__(self, model, sample, hear, wait):
        self.model = Model(model)
        self.samplerate = sample
        self.queue = queue.Queue()
        self.hear = hear
        self.tecla_tomar = wait

    def listen(self):
        while self.hear == True:
            keyboard.wait("w")
            audio = self.record_audio()
            segs = self.model.transcribe(audio, language="es")
            listen_result = " ".join(seg.text for seg in segs)
            return(listen_result)
        
    def record_audio(self,duration_sec=5):
        rec = sd.rec(int(duration_sec * self.samplerate), samplerate=self.samplerate, channels=1, dtype='float32')
        sd.wait()
        return np.concatenate(rec, axis=0).ravel()


class Speaker:    #------------------------------REHACER COMPLETO BASADO EN TEXT TO SPEECH
    def __init__(self, model,talk,t_callar,t_repetir):
        #self.model = Model(model)
        self.queue = queue.Queue()
        self.talk = talk
        self.tecla_callar = t_callar
        self.tecla_repetir = t_repetir
        self.last_text = ""
    def decir(self,texto):
        1#tts + some configs


if __name__ == "__main__":
    violetta=Violetta()
