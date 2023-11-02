# coding: utf-8

import tkinter as tk
from tkinter import filedialog
import os
import pymysql
import pygame
from pygame import mixer

ubicacion_temporal = os.path.expanduser("~")

# Inicializar pygame y mixer
pygame.init()
mixer.init()

cancion_actual = None
reproductor = None
# Variable para mantener un registro del estado de la reproducción
reproduccion_pausada = False
posicion_reproduccion = 0  

# Variables para almacenar los nombres de los archivos temporales
archivo_temporal_actual = "musica_temp/temp_cancion_actual.mp3"
archivo_temporal_siguiente = "musica_temp/temp_cancion_siguiente.mp3"

# Variable para mantener un registro del estado de la reproducción
reproduccion_pausada = False

# Función para guardar una canción en la base de datos y actualizar la lista
def guardar_cancion_en_db_y_actualizar_lista(nombre_cancion, file_path):
    conexion = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="bd1",
        charset="utf8",
        connect_timeout=60
    )

    try:
        with conexion.cursor() as cursor:
            with open(file_path, 'rb') as archivo:
                contenido = archivo.read()
            consulta = "INSERT INTO canciones (nombre_cancion, archivo_cancion) VALUES (%s, %s)"
            cursor.execute(consulta, (nombre_cancion, contenido))
            conexion.commit()
            
            # Agregar el nombre de la canción a la lista
            nombres_canciones.append(nombre_cancion)
            
            # Actualizar la lista en el Listbox
            lista_canciones.delete(0, tk.END)
            for nombre in nombres_canciones:
                lista_canciones.insert(tk.END, nombre)
    finally:
        conexion.close()

# Función para seleccionar y guardar música
def seleccionar_y_guardar_musica():
    file_path = filedialog.askopenfilename(title="Seleccione una canción",
                                           filetypes=[("Audio files", "*.mp3 *.wav *.ogg")])
    if file_path:
        nombre_cancion = os.path.basename(file_path)  
        guardar_cancion_en_db_y_actualizar_lista(nombre_cancion, file_path)
        print(f"Canción '{nombre_cancion}' guardada en la base de datos y actualizada en la lista.")

# Función para cargar nombres de canciones desde la base de datos
def cargar_nombres_canciones():
    conexion = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="bd1",
        charset="utf8",
        connect_timeout=60
    )

    try:
        with conexion.cursor() as cursor:
            consulta = "SELECT nombre_cancion FROM canciones"
            cursor.execute(consulta)
            resultados = cursor.fetchall()
            nombres = [resultado[0] for resultado in resultados]
            return nombres
    finally:
        conexion.close()

# Función para pausar o reanudar la reproducción
def pausar_reanudar():
    global reproduccion_pausada

    if not reproduccion_pausada:
        pygame.mixer.music.pause()
        reproduccion_pausada = True
    else:
        pygame.mixer.music.unpause()
        reproduccion_pausada = False
                

# Función para manejar la selección de una canción desde el Listbox
def seleccionar_cancion(event):
    global cancion_actual, reproductor, archivo_temporal_actual, archivo_temporal_siguiente, reproduccion_pausada

    if cancion_actual is not None and reproductor is not None and reproductor.get_busy():
        reproductor.stop()

    seleccion = lista_canciones.get(lista_canciones.curselection())
    print(f"Canción seleccionada: {seleccion}")

    # Conectar a la base de datos y obtener el archivo de la canción
    conexion = pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="bd1",
        charset="utf8",
        connect_timeout=60
    )

    try:
        with conexion.cursor() as cursor:
            consulta = "SELECT archivo_cancion FROM canciones WHERE nombre_cancion = %s"
            cursor.execute(consulta, (seleccion,))
            resultado = cursor.fetchone()
            if resultado:
                # Guardar la nueva canción en el archivo temporal siguiente
                with open(archivo_temporal_siguiente, "wb") as archivo_temporal:
                    archivo_temporal.write(resultado[0])
                # Reproducir la nueva canción desde el archivo temporal siguiente
                reproductor = mixer.music
                reproductor.load(archivo_temporal_siguiente)
                reproductor.play()
                cancion_actual = seleccion
                archivo_en_reproduccion = archivo_temporal_siguiente  # Actualizar el archivo en reproducción
                reproduccion_pausada = False 
                
                # Intercambiar los nombres de los archivos temporales
                archivo_temporal_actual, archivo_temporal_siguiente = archivo_temporal_siguiente, archivo_temporal_actual
            else:
                print("La canción no se encontró en la base de datos.")
    finally:
        conexion.close()


# Función para detener la reproducción
def detener_reproduccion():
    global cancion_actual, reproductor, archivo_temporal_actual, archivo_temporal_siguiente

    if cancion_actual is not None and reproductor is not None and reproductor.get_busy():
        reproductor.stop()
        cancion_actual = None
        # Eliminar el archivo temporal actual y siguiente si existen
        if os.path.exists(archivo_temporal_actual):
            os.remove(archivo_temporal_actual)
        if os.path.exists(archivo_temporal_siguiente):
            os.remove(archivo_temporal_siguiente)


# Crear una ventana tkinter
ventana = tk.Tk()
ventana.title("Reproductor de música")

# Obtener el tamaño de la pantalla
ancho_pantalla = ventana.winfo_screenwidth()
alto_pantalla = ventana.winfo_screenheight()

# Definir el tamaño de la ventana
ancho_ventana = 400
alto_ventana = 500

# Calcular la posición para centrar la ventana
x_pos = (ancho_pantalla - ancho_ventana) // 2
y_pos = (alto_pantalla - alto_ventana) // 4

# Establecer la geometría de la ventana
ventana.geometry(f"{ancho_ventana}x{alto_ventana}+{x_pos}+{y_pos}")

fondo_img = tk.PhotoImage(file="musica_temp/fondo.png")

# Crea un widget Label para mostrar la imagen de fondo
fondo_label = tk.Label(ventana, image=fondo_img)
fondo_label.place(relwidth=1, relheight=1) 

# Crear un botón para seleccionar y guardar la canción
boton_seleccionar = tk.Button(ventana, text="Seleccionar y Guardar Canción", command=seleccionar_y_guardar_musica, font=("Arial", 16), bg="green", fg="white")
boton_seleccionar.pack(padx=20, pady=10)

# Crear un Listbox para mostrar los nombres de las canciones
fuente = ("Arial", 15)  
nombres_canciones = cargar_nombres_canciones()

global lista_canciones

lista_canciones = tk.Listbox(ventana, height=10, width=100, bg="navy", fg="white") 
lista_canciones.configure(font=fuente)
for nombre in nombres_canciones:
    lista_canciones.insert(tk.END, nombre)
lista_canciones.pack(padx=20, pady=10)

# Asociar la función de selección a la lista
lista_canciones.bind('<<ListboxSelect>>', seleccionar_cancion)

# Crear un botón para pausar o reanudar la reproducción
boton_pausar_reanudar = tk.Button(ventana, text="Pausar/Reanudar", command=pausar_reanudar, font=("Arial", 16), bg="blue", fg="white")
boton_pausar_reanudar.pack(padx=20, pady=10)

# Iniciar el bucle principal de Tkinter
ventana.mainloop()
