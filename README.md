# AnalisisVideoAWSRekognitionYOLOv8

## Descripción del Proyecto
El presente proyecto fue creado con la finalidad de detección de rostros de personas en videos (específicamente en películas), así como armas o vehículos, utilizando multiprocesamiento, para así procesar “N” cantidad de videos a la vez y mostrar resultados, sin necesidad de que se termine el programa por completo. Gracias a la extracción de fotogramas en los videos se puede conocer si algún objeto aparece en un fotograma en específico, así como reconocer si una persona en específico está en dicho fotograma. 

## Instrucciones de Instalación
Para utilizar el presente proyecto, es necesario tener instalado Python, así como las siguientes librerías:
 1. os 
 2. shutil
 3. threading
 4. time
 5. boto3
 6. io
 7. cv2
 8. tkinter

## Explicación de cada librería
 1. os: Es utilizada para el manejo de carpetas dentro del proyecto.
 2. shutil: Su función es manipular las carpetas que existan dentro de una carpeta.
 3. threading: Gracias a esta, se puede utilizar el multiprocesamiento.
 4. time: Utilizada para pausar la ejecución en ciertas partes del código en el multiprocesamiento.
 5. boto3: Es para utilizar los distintos servicios de AWS, en especifico el S3 (subir imágenes del entrenamiento en el almacenamiento de la nube), DynamoDB (base de datos que permite manejar a través de una tabla cada una de las personas registradas en el entrenamiento) y Rekognition (detección de personas y rostros).
 6. io: Es implementada en el manejo de archivos, como en los fotogramas de los videos.
 7. cv2: Creación de etiquetas y cuadros de caras o objetos detectados en los fotogramas de los videos.
 8. tkinter: Utilización de interfaz gráfica en Python.
