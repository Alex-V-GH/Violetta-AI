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
                  
class Violetta:
    def __init__(self):
        print(os.getcwd())
        with open("config.json", "r", encoding="utf-8") as f:
            parameters = json.load(f)
            self.Azul=azul(parameters["azul"]["db"],parameters["azul"]["model"])
            self.Rosa=rosa(parameters["rosa"]["db"],parameters["rosa"]["model"])
            self.Listener=listener(parameters["listener"]["model"],parameters["listener"]["samplerate"],parameters["listener"]["hear"],parameters["listener"]["wait"])
            self.Speaker=speaker(parameters["speaker"]["model"],parameters["speaker"]["talk"],parameters["speaker"]["sh"],parameters["speaker"]["repetir"])
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
        self.t_consumidor=threading.Thread(target=self.consumidor_inpucts, daemon=True)
        #lanzando hilos
        self.t_in_read.start()
        self.t_in_hear.start()
        self.t_consumidor.start()
        #pa que no cierre
        self.t_in_read.join()
        self.t_in_hear.join()
        self.t_consumidor.join()


    def consumidor_inpucts(self):
        while True:
            chan, entrada = self.cola_inputs.get()
            self.decide(entrada)
            self.cola_inputs.task_done()
            time.sleep(0.1)
    
    def read_in(self):
        while True:
            self.cola_inputs.put(('read', self.filter_wish(input("Escriba lo que desea que haga:" \
            ""))))
            time.sleep(20)
    
    def hear_in(self):
        while True:
            self.cola_inputs.put(('hear', self.filter_wish(self.Listener.listen())))
            time.sleep(20)
    
    def filter_wish(self,raw_wish):
        raw_wish = raw_wish or ""
        return re.sub(r'[^a-z0-9 _()""]', '', raw_wish.lower())

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
            self.Azul.execute_wish(elemento)
                
        
class azul:
    def __init__(self, db, model):
        self.data_base = db
        self.data = sqlite3.connect(self.data_base)
        self.data_cursor = self.data.cursor()
        print(model)
        self.model = Model(model)#, from_file=True)

    def execute_wish(self,wish):
        if os.path.exists(self.data_base):
            self.data_cursor.execute("SELECT script FROM commands WHERE alias = ?", (wish,))
            row = self.data_cursor.fetchone()
            if row:
                execution = "aux_scripts." + row[0]
                print(execution)
                exec(execution)
            else:
                self.learn_new_command(wish)
        else: 
            self.learn_new_command(wish)


    def learn_new_command(self,command):
        self.data_cursor.execute('''
        CREATE TABLE IF NOT EXISTS commands (
            alias TEXT PRIMARY KEY,
            script TEXT
        )
        ''')
        print (f"Your action is {command}. Let´s set it up!\n")
        #now let´s learn that command or arguments (a bunch of if´s and some other scripts and arguments)

        func_name = input("Function name?\nYou can always say exit or cancel to go back\n")
        if func_name.lower() in ["salir", "exit", "quit", "back", "atras", "volver"]:
            return
        new = input("Is it a brand new command?\n")
        if new.lower() in ["yes", "si", "y", "s", "sep", "yeah"]:
            self.write_new_function()  
        argsbase =  input("Function args?\n")
        args = [x.strip() for x in argsbase.split(",")]
        for arg in args:
            self.data_cursor.execute("SELECT path FROM path WHERE element = ?", (arg,))
            row = self.data_cursor.fetchone()
            if not row:
                ispath = input ("This name has a path? Y/N")
                if ispath.lower() in ["yes", "si", "y", "s", "sep", "yeah"]:
                    arg_path =  input("what is the path / value of this argument?\nTo write a path, please use only the /, and never comillas")#------------desde aca
                    mapping_arg = (arg,arg_path)
                    self.data_cursor.execute("INSERT OR REPLACE INTO path VALUES (?, ?)", mapping_arg)
                    self.data.commit()
        listadoargs = ', '.join(f'"{x}"' for x in args)
        script = func_name + "(" + listadoargs + ")"
        mappings = (command, script)
        self.data_cursor.execute("INSERT OR REPLACE INTO commands VALUES (?, ?)", mappings)
        self.data.commit()
        self.execute_wish(command) 


    def write_new_function():
        need_user = "yes"
        if need_user == "yes":
            print("i don´t have that ability yet")
        else:
            return "yes"


class rosa:
    def __init__(self, db, model):
        self.data_base = db
        self.data = sqlite3.connect(self.data_base)
        self.data_cursor = self.data.cursor()
        print(model)
        self.model = Model(model)#, from_file=True)
    def respuesta (self,inpuct):
        print(f"***debug*** rosa.respuesta({inpuct})")


class listener:
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


class speaker:
    def __init__(self, model,talk,t_callar,t_repetir):
        self.model = Model(model)
        self.queue = queue.Queue()
        self.talk = talk
        self.tecla_callar = t_callar
        self.tecla_repetir = t_repetir
        self.last_text = ""
    def decir(self,texto):
        1#tts + some configs


if __name__ == "__main__":
    violetta=Violetta()