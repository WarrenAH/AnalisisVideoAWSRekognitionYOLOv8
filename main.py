import os
import shutil
import threading
import time
import boto3
import io
import cv2
import tkinter as tk

from tkinter import filedialog, scrolledtext
from threading import Thread
from PIL import Image, ImageTk
from ultralytics import YOLO
from moviepy.editor import VideoFileClip

def Entrenamiento():
    s3 = boto3.resource('s3')

    # carpeta de entrenamiento
    carpeta_entrenamiento = './Entrenamiento/'

    # lista para almacenar las imágenes y sus nombres
    imagenes = []

    # iterar sobre los archivos en la carpeta de entrenamiento
    for filename in os.listdir(carpeta_entrenamiento):
        # combinar la ruta de la carpeta de entrenamiento con el nombre del archivo
        filepath = os.path.join(carpeta_entrenamiento, filename)
        # obtener el nombre del archivo sin la extensión
        nombre = os.path.splitext(filename)[0]
        # reemplazar los guiones bajos (_) con espacios en el nombre del archivo
        nombre = nombre.replace('_', ' ')
        # añadir la tupla (ruta del archivo, nombre) a la lista de imagenes
        imagenes.append((filepath, nombre))

    # iterar a traves de la lista para cargar objetos en S3
    for imagen in imagenes:
        archivo = open(imagen[0],'rb')
        objecto = s3.Object('actores','index/'+ imagen[0])
        ret = objecto.put(Body=archivo,
                        Metadata={'FullName':imagen[1]})

def DetectarPersona(imagen, nombreImagen, archivoTxt):
    image = cv2.imread(imagen)
    actoresEncontrados = []

    rekognition = boto3.client('rekognition', region_name='us-east-1')
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')

    # cargar la imagen desde un archivo
    imagenObtenida = Image.open(imagen)

    stream = io.BytesIO()
    imagenObtenida.save(stream, format="JPEG")
    imagenBinaria = stream.getvalue()

    # detectar caras en la imagen
    respuesta = rekognition.detect_faces(Image={'Bytes': imagenBinaria})

    # verificar si se encontraron caras en la imagen
    if len(respuesta['FaceDetails']) == 0:
        return

    # iterar sobre cada cara detectada
    for detalleCara in respuesta['FaceDetails']:
        # obtener las coordenadas de la cara en la imagen
        box = detalleCara['BoundingBox']
        width, height = imagenObtenida.size
        left = width * box['Left']
        top = height * box['Top']
        face_width = width * box['Width']
        face_height = height * box['Height']

        # convertir la cara recortada a bytes
        imagenCara = imagenObtenida.crop((left, top, left + face_width, top + face_height))

        stream = io.BytesIO()
        imagenCara.save(stream, format="JPEG")
        caraBinaria = stream.getvalue()

        try:
            segundaRespuesta = rekognition.search_faces_by_image(
                CollectionId='actores',
                Image={'Bytes': caraBinaria}
            )
        except Exception as e:
            print(f"No se encontro alguna cara reconocible en la imagen.")
            continue

        found = False
        for match in segundaRespuesta['FaceMatches']:
            print(match['Face']['FaceId'], match['Face']['Confidence'])

            cara = dynamodb.get_item(
                TableName='face_recognition',
                Key={'RekognitionId': {'S': match['Face']['FaceId']}}
            )

            if 'Item' in cara:
                cv2.rectangle(image, (int(left), int(top)), (int(left + face_width), int(top + face_height)),
                              (52, 219, 124), 2)

                # escribir el nombre de la persona encima de la cara
                print("Persona encontrada: ", cara['Item']['FullName']['S'])
                actoresEncontrados.append(cara['Item']['FullName']['S'])
                found = True

                # obtener las dimensiones del texto
                (text_width, text_height), _ = cv2.getTextSize(cara['Item']['FullName']['S'], cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)

                # dibujar el fondo del texto (rectángulo)
                cv2.rectangle(image, (int(left), int(top - text_height - 10)), (int(left + text_width), int(top)),
                              (52, 219, 124),
                              cv2.FILLED)

                # dibujar el texto
                cv2.putText(image, cara['Item']['FullName']['S'], (int(left), int(top - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

                # dibujar el cuadrado alrededor del texto
                cv2.rectangle(image, (int(left), int(top - text_height - 10)), (int(left + text_width), int(top)),
                              (52, 219, 124), 2)

        if not found:
            cv2.rectangle(image, (int(left), int(top)), (int(left + face_width), int(top + face_height)),
                          (219, 52, 82), 2)

            # obtener las dimensiones del texto
            (text_width, text_height), _ = cv2.getTextSize("Desconocido(a)", cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                                                           2)

            # dibujar el fondo del texto (rectangulo)
            cv2.rectangle(image, (int(left), int(top - text_height - 10)), (int(left + text_width), int(top)),
                          (219, 52, 82),
                          cv2.FILLED)

            # dibujar el texto
            cv2.putText(image, "Desconocido(a)", (int(left), int(top - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9,
                        (255, 255, 255), 2)

            # dibujar el cuadrado alrededor del texto
            cv2.rectangle(image, (int(left), int(top - text_height - 10)), (int(left + text_width), int(top)),
                          (219, 52, 82), 2)
            print("La persona no es reconocible.")


    if len(actoresEncontrados) > 0:
        with open(archivoTxt, 'a', encoding='utf-8') as file:
            file.write("En el fotograma " + nombreImagen + " se encontro(aron) el(los) actor(es): " + ", ".join(actoresEncontrados) + '\n')

    cv2.imwrite(imagen, image)
def EncontrarObjetos(imagen, nombreImagen, archivoTxt):
    image = cv2.imread(imagen)

    modeloVehiculos = YOLO('./Modelo/yolov8x.pt')

    # definir el diccionario de clases
    clasesVehiculos = {
        1: 'Bicicleta',
        2: 'Carro',
        3: 'Motocicleta',
        4: 'Avion',
        5: 'Bus',
        6: 'Tren',
        7: 'Camion',
        8: 'Bote',
    }

    modeloArmas = YOLO('./Modelo/Armas.pt')

    # definir el diccionario de clases
    clasesArmas = {
        0: 'Arma',
        1: 'Cuchillo',
    }

    resultadosVehiculos = modeloVehiculos(source=image, classes=[1, 2, 3, 4, 5, 6, 7, 8])

    # reemplazar nombres de clases con etiquetas modificadas en los resultados
    for resultado in resultadosVehiculos:
        for cls_id, custom_label in clasesVehiculos.items():
            if cls_id in resultado.names:
                resultado.names[cls_id] = custom_label


    resultadosArmas = modeloArmas(source=image, show_conf=False, conf=0.8)

    for resultado in resultadosArmas:
        for cls_id, custom_label in clasesArmas.items():
            if cls_id in resultado.names:
                resultado.names[cls_id] = custom_label

    # extraer boxes, classes, names, y confidences
    boxesVehiculos = resultadosVehiculos[0].boxes.xyxy.tolist()
    classesVehiculos = resultadosVehiculos[0].boxes.cls.tolist()
    namesVehiculos = resultadosVehiculos[0].names


    # extraer boxes, classes, names, y confidences
    boxesArmas = resultadosArmas[0].boxes.xyxy.tolist()
    classesArmas = resultadosArmas[0].boxes.cls.tolist()
    namesArmas = resultadosArmas[0].names

    listaObjetos = [["bicicleta(s)", 0], ["carro(s)", 0], ["motocicleta(s)", 0], ["avion(es)", 0], ["bus(es)", 0],
                    ["tren(es)", 0], ["camion(es)", 0], ["bote(s)", 0], ["arma(s)", 0], ["cuchillo(s)", 0]]

    for box, cls, conf in zip(boxesVehiculos, classesVehiculos, namesVehiculos):
        x1, y1, x2, y2 = box
        name = namesVehiculos[int(cls)]

        if name == "Bicicleta":
            listaObjetos[0][1] += 1
        elif name == "Carro":
            listaObjetos[1][1] += 1
        elif name == "Motocicleta":
            listaObjetos[2][1] += 1
        elif name == "Avion":
            listaObjetos[3][1] += 1
        elif name == "Bus":
            listaObjetos[4][1] += 1
        elif name == "Tren":
            listaObjetos[5][1] += 1
        elif name == "Camion":
            listaObjetos[6][1] += 1
        else:
            listaObjetos[7][1] += 1

        # obtener las dimensiones del texto
        (text_width, text_height), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)

        # dibujar el fondo del texto (rectangulo)
        cv2.rectangle(image, (int(x1), int(y1 - text_height - 10)), (int(x1 + text_width), int(y1)), (219, 152, 52),
                      cv2.FILLED)

        # dibujar el texto
        cv2.putText(image, name, (int(x1), int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # dibujar el cuadrado alrededor del texto
        cv2.rectangle(image, (int(x1), int(y1 - text_height - 10)), (int(x1 + text_width), int(y1)), (219, 152, 52), 2)

        # dibujar el cuadro alrededor del objeto
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (219, 152, 52), 2)

    for box, cls, conf in zip(boxesArmas, classesArmas, namesArmas):
        x1, y1, x2, y2 = box
        name = namesArmas[int(cls)]

        if name == "Arma":
            listaObjetos[8][1] += 1
        else:
            listaObjetos[9][1] += 1

        # obtener las dimensiones del texto
        (text_width, text_height), _ = cv2.getTextSize(name, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)

        # dibujar el fondo del texto (rectángulo)
        cv2.rectangle(image, (int(x1), int(y1 - text_height - 10)), (int(x1 + text_width), int(y1)), (43, 57, 192),
                      cv2.FILLED)

        # Dibujar el texto
        cv2.putText(image, name, (int(x1), int(y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        # dibujar el cuadrado alrededor del texto
        cv2.rectangle(image, (int(x1), int(y1 - text_height - 10)), (int(x1 + text_width), int(y1)), (43, 57, 192), 2)

        # dibujar el cuadro alrededor del objeto
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (43, 57, 192), 2)

    contador = 0
    textos = []

    # Recorremos la lista de objetos
    for objeto in listaObjetos:
        if objeto[1] > 0:
            contador += objeto[1]
            textos.append(f"{objeto[1]} {objeto[0]}")

    textoFinal = ', '.join(textos)

    if contador > 0:
        with open(archivoTxt, 'a', encoding='utf-8') as file:
            file.write(f"En el fotograma {nombreImagen} se encontró la siguiente cantidad de objetos {contador} en: {textoFinal}\n")
        cv2.imwrite(imagen, image)


def ExtraerFotogramas(rutaVideo, directorioSalida, intervalo=5):
    # obtiene el nombre del archivo de video sin la extensión
    nombreVideo = os.path.splitext(os.path.basename(rutaVideo))[0]

    # crea la subcarpeta dentro de 'extraidos' con el nombre del archivo de video
    directorioSalida = os.path.join(directorioSalida, nombreVideo)
    if not os.path.exists(directorioSalida):
        os.makedirs(directorioSalida)

    video = VideoFileClip(rutaVideo)

    duracion = video.duration

    # extrae los fotogramas cada 'intervalo', en segundos
    for t in range(0, int(duracion), intervalo):
        # convierte el tiempo a formato hh:mm:ss
        tiempoString = '{:02d}-{:02d}-{:02d}'.format(t // 3600, (t % 3600) // 60, t % 60)

        # Genera el nombre del archivo de salida
        nombreFotograma = os.path.join(directorioSalida, f"{tiempoString}.jpg")

        # extrae el fotograma en el tiempo especificado y lo guarda como imagen
        video.save_frame(nombreFotograma, t=t)

    # Cierra el video
    video.close()

def EliminarCarpetas():
    directorioFotograma = os.path.join("./", "Fotograma")
    if os.path.exists(directorioFotograma):
        shutil.rmtree(directorioFotograma)

def EncontrarCarasObjetos(carpeta, carpetaFotograma, nombreCarpetaFotograma):
    time.sleep(3)

    archivoTxt = os.path.join(carpeta, nombreCarpetaFotograma+".txt")

    if not os.path.exists(archivoTxt):
        with open(archivoTxt, "w") as archivo:
            pass

    # lista para almacenar los nombres de los archivos procesados
    archivosProcesados = []

    # obtener la cantidad total de archivos en la carpeta
    totalArchivos = len(os.listdir(carpetaFotograma))

    # bucle mientras haya archivos sin procesar
    while totalArchivos > len(archivosProcesados):
        # obtener la lista de archivos en la carpeta
        archivos = os.listdir(carpetaFotograma)

        #iterar sobre cada archivo en la carpeta
        for archivo in archivos:
            # si el archivo es una imagen y no ha sido procesado anteriormente
            if (archivo.endswith(".jpg") or archivo.endswith(".png")) and archivo not in archivosProcesados:
                directorioImagen = os.path.join(carpetaFotograma, archivo)

                imagen = cv2.imread(directorioImagen)

                imagenGris = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)

                clasificadorCara = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )

                cara = clasificadorCara.detectMultiScale(
                    imagenGris, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
                )

                nombreArchivo = os.path.splitext(archivo)[0]

                if len(cara) > 0:
                    print(directorioImagen)
                    print(nombreArchivo)
                    DetectarPersona(directorioImagen, nombreArchivo, archivoTxt)

                EncontrarObjetos(directorioImagen, nombreArchivo, archivoTxt)

                #agregar el nombre del archivo a la lista de procesados
                archivosProcesados.append(archivo)

        time.sleep(1)

        totalArchivos = len(os.listdir(carpetaFotograma))

def Programa(listaVideos):
    EliminarCarpetas()

    directorioSalida = os.path.join("./", "Fotograma")

    if not os.path.exists(directorioSalida):
        os.makedirs(directorioSalida)

    hilos = []

    # utilizar Thread para aplicar multiprocesamiento a cada ubicacion de los videos
    for video in listaVideos:
        hilo = Thread(target=ExtraerFotogramas, args=(video, directorioSalida))
        hilo.start()
        hilos.append(hilo)

    for video in listaVideos:
        nombreVideo = os.path.splitext(os.path.basename(video))[0]

        directorioFotograma = os.path.join("./Fotograma", nombreVideo)

        hilo = Thread(target=EncontrarCarasObjetos, args=(directorioSalida, directorioFotograma, nombreVideo))
        hilo.start()
        hilos.append(hilo)

    # esperar a que todos los hilos terminen
    for hilo in hilos:
        hilo.join()

def InterfazGraficaVideosBusqueda():
    def BusquedaVideo():
        rutasSeleccionadas = filedialog.askopenfilenames(initialdir="./Video", title="Seleccionar archivos de video",
                                                          filetypes=(("Archivos de video", "*.mp4"), ("Todos los archivos", "*.*")))
        for rutaArchivo in rutasSeleccionadas:
            numVideo = sum(1 for ruta in [labelRuta1.cget("text"), labelRuta2.cget("text"), labelRuta3.cget("text")] if ruta)

            if rutaArchivo:
                # verificar si el archivo seleccionado ya está entre los videos seleccionados
                rutasVideos = [labelRuta1.cget("text"), labelRuta2.cget("text"), labelRuta3.cget("text")]
                rutasArchivos = [ruta.split(': ')[1] for ruta in rutasVideos if ruta]
                if rutaArchivo in rutasArchivos:
                    rutasDuplicadas = [ruta for ruta in rutasArchivos if ruta == rutaArchivo]
                    rutasDuplicadasStr = "\n".join(rutasDuplicadas)
                    tk.messagebox.showerror("Error", f"Este video ya ha sido seleccionado anteriormente:\n{rutasDuplicadasStr}")
                    continue

                # verificar si el archivo seleccionado tiene formato .mp4
                if not rutaArchivo.endswith(".mp4"):
                    tk.messagebox.showerror("Error", f"El archivo '{rutaArchivo}' no es un archivo .mp4.")
                    continue

                if numVideo == 0:
                    labelRuta1.config(text=f"Video 1: {rutaArchivo}")
                elif numVideo == 1:
                    labelRuta2.config(text=f"Video 2: {rutaArchivo}")
                elif numVideo == 2:
                    labelRuta3.config(text=f"Video 3: {rutaArchivo}")

                VerificarSeleccionVideo()

    def VerificarSeleccionVideo():
        rutasVideos = [labelRuta1.cget("text"), labelRuta2.cget("text"), labelRuta3.cget("text")]
        rutasArchivos = [ruta.split(': ')[1] for ruta in rutasVideos if
                          ruta]
        if all(rutasArchivos):
            if len(set(rutasArchivos)) == len(rutasArchivos):
                botonContinuar.pack(pady=10)
            else:
                tk.messagebox.showerror("Error", "Los tres videos deben ser diferentes.")
        else:
            botonContinuar.pack_forget()

    def OcultarVentana():
        ventana.withdraw()

    def EjecucionPrograma():
        DesactivarBotones()
        rutasVideos = [labelRuta1.cget("text"), labelRuta2.cget("text"), labelRuta3.cget("text")]
        rutasArchivos = [ruta.split(': ')[1] for ruta in rutasVideos if
                         ruta]
        hilo = threading.Thread(target=Programa, args=[rutasArchivos], daemon=True).start()
        time.sleep(10)
        InterfazGraficaResultadosImagenes()
        InterfazGraficaResultadosTexto()
        OcultarVentana()
        ActivarBotones()

    def RealizarEntrenamiento():
        DesactivarBotones()
        try:
            Entrenamiento()
        except Exception as e:
            tk.messagebox.showerror("Error", f"Ocurrió un error durante el entrenamiento: {str(e)}")
            return
        tk.messagebox.showinfo("Exitoso", "El entrenamiento se hizo correctamente.")
        ActivarBotones()

    def DesactivarBotones():
        botonBuscar.config(state=tk.DISABLED)
        botonContinuar.config(state=tk.DISABLED)
        botonEntrenar.config(state=tk.DISABLED)

    def ActivarBotones():
        botonBuscar.config(state=tk.ACTIVE)
        botonContinuar.config(state=tk.ACTIVE)
        botonEntrenar.config(state=tk.ACTIVE)

    if not os.path.exists("./Video"):
        os.makedirs("./Video")

    if not os.path.exists("./Modelo"):
        os.makedirs("./Modelo")

    if not os.path.exists("./Entrenamiento"):
        os.makedirs("./Entrenamiento")

    if not os.path.exists("./Fotograma"):
        os.makedirs("./Fotograma")

    ventana = tk.Tk()
    ventana.title("Buscar videos analisis")
    ventana.geometry("500x300")

    frameBotones = tk.Frame(ventana)
    frameBotones.pack(pady=10)

    botonBuscar = tk.Button(frameBotones, text="Buscar videos", command=BusquedaVideo)
    botonBuscar.pack(side=tk.LEFT, padx=10)

    botonEntrenar = tk.Button(frameBotones, text="Entrenar", command=RealizarEntrenamiento)
    botonEntrenar.pack(side=tk.LEFT, padx=10)

    labelRuta1 = tk.Label(ventana, text="", wraplength=400)
    labelRuta1.pack(pady=5)
    labelRuta2 = tk.Label(ventana, text="", wraplength=400)
    labelRuta2.pack(pady=5)
    labelRuta3 = tk.Label(ventana, text="", wraplength=400)
    labelRuta3.pack(pady=5)

    botonContinuar = tk.Button(ventana, text="Continuar",
                               command=lambda: [EjecucionPrograma()])

    ventana.mainloop()

def InterfazGraficaResultadosTexto():
    def MostrarContenido(archivo, txtWidget):
        posicionScroll = txtWidget.yview()[0]
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        txtWidget.configure(state='normal')
        txtWidget.delete('1.0', tk.END)
        txtWidget.insert(tk.END, contenido)
        txtWidget.configure(state='disabled')
        txtWidget.yview_moveto(posicionScroll)

    # ruta de la carpeta que contiene los archivos .txt
    ruta = './Fotograma'

    # obtener la lista de archivos .txt en la ruta
    archivosTxt = [archivo for archivo in os.listdir(ruta) if archivo.endswith('.txt')]

    # crear ventana principal
    root = tk.Toplevel()
    root.title('Analisis eventos')

    # crear un cuadro de texto con scroll para cada archivo .txt
    textoWidgets = []
    for archivo in archivosTxt:
        lblNombre = tk.Label(root, text=f'Eventos del video: {archivo}:')
        lblNombre.pack()
        txtContenido = scrolledtext.ScrolledText(root, width=80, height=10)
        txtContenido.pack()
        MostrarContenido(os.path.join(ruta, archivo), txtContenido)
        textoWidgets.append(txtContenido)

        # Función para actualizar el contenido periódicamente
        def ActualizarContenido(archivo, txtWidget):
            MostrarContenido(archivo, txtWidget)
            txtWidget.after(5000, ActualizarContenido, archivo, txtWidget)

        ActualizarContenido(os.path.join(ruta, archivo), txtContenido)

def InterfazGraficaResultadosImagenes():
    def MostrarImagen(archivo, imgLabel, nombreLabel):
        imagen = Image.open(archivo)
        imagen = imagen.resize((400, 400), Image.LANCZOS)
        foto = ImageTk.PhotoImage(imagen)
        imgLabel.configure(image=foto)
        imgLabel.image = foto
        nombreLabel.configure(text=os.path.basename(archivo))

    ruta = './Fotograma'
    carpetas = [carpeta for carpeta in os.listdir(ruta) if os.path.isdir(os.path.join(ruta, carpeta))]

    root = tk.Toplevel()
    root.title('Analisis imagenes')

    indices = {carpeta: 0 for carpeta in carpetas}

    def MostrarSiguienteImagen(carpeta):
        archivosImagenes = [archivo for archivo in os.listdir(os.path.join(ruta, carpeta)) if archivo.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        indices[carpeta] = (indices[carpeta] + 1) % len(archivosImagenes)
        MostrarImagen(os.path.join(ruta, carpeta, archivosImagenes[indices[carpeta]]), imgLabels[carpeta], nombreLabels[carpeta])

    def MostrarAnteriorImagen(carpeta):
        archivos_imagenes = [archivo for archivo in os.listdir(os.path.join(ruta, carpeta)) if archivo.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        indices[carpeta] = (indices[carpeta] - 1) % len(archivos_imagenes)
        MostrarImagen(os.path.join(ruta, carpeta, archivos_imagenes[indices[carpeta]]), imgLabels[carpeta], nombreLabels[carpeta])

    columna = 1

    imgLabels = {}
    nombreLabels = {}
    for carpeta in carpetas:
        lblNombre = tk.Label(root, text=f'Imagenes del video: {carpeta}:')
        lblNombre.grid(row=1, column=columna)

        imgLabel = tk.Label(root, width=400, height=400)
        imgLabel.grid(row=2, column=columna)

        nombreLabel = tk.Label(root, text="")
        nombreLabel.grid(row=3, column=columna)

        imgLabels[carpeta] = imgLabel
        nombreLabels[carpeta] = nombreLabel

        archivosImagenes = [archivo for archivo in os.listdir(os.path.join(ruta, carpeta)) if archivo.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
        if archivosImagenes:
            MostrarImagen(os.path.join(ruta, carpeta, archivosImagenes[0]), imgLabel, nombreLabel)

        botonSiguiente = tk.Button(root, text="Siguiente", command=lambda c=carpeta: MostrarSiguienteImagen(c))
        botonSiguiente.grid(row=4, column=columna)

        botonAnterior = tk.Button(root, text="Anterior", command=lambda c=carpeta: MostrarAnteriorImagen(c))
        botonAnterior.grid(row=5, column=columna)

        columna += 1

def main():
    InterfazGraficaVideosBusqueda()
if __name__ == "__main__":
    main()

