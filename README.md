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
Una vez instaladas, es necesario tener una cuenta en AWS para acceder a los servicios de: Lambda, S3, Rekognition, y DynamoDB, luego, seguir los siguientes pasos:
 1. Se deberá acceder a AWS y buscar IAM (Identity and Access Management), dentro, se debe acceder a la sección que dice Administración del acceso. Una vez en esta sección se mostrará el Panel de IAM, y se deberá tocar el botón que dice Administrar las claves de acceso. Luego, se debe ir donde dice Claves de acceso, tocar el botón que dice Crear clave de acceso, se nos pedirá confirmación, se acepta, una vez creado, se debe apuntar la Clave de acceso y la Clave de acceso secreta, ya que se necesitaran más adelante.
 2. En el CMD de Windows se debe tener acceso a la carpeta donde se encuentra el repositorio clonado, se debe ejecutar el siguiente comando: 
```
aws configure
```
 3. Se pedirá primeramente la Clave de acceso, la Clave de acceso secreta y cuando se pida la región se deberá colocar lo siguiente: 
```
us-east-1
```
 4. Una vez hecho esto, se debe ejecutar el siguiente comando: 
```
aws rekognition create-collection --collection-id actores --region us-east-1", se desplegará un mensaje de que fue creado. Luego, se debe ejecutar este otro comando: "aws dynamodb create-table --table-name face_recognition --attribute-definitions AttributeName=RekognitionId,AttributeType=S --key-schema AttributeName=RekognitionId,KeyType=HASH --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 --region us-east-1
```
5. Se desplegará un mensaje de que fue creado. El ultimo comando sería el siguiente:
```
aws s3 mb s3://actores --region us-east-1
```
 6. En IAM, se debe acceder a la sección de Roles, darle en el botón que dice Crear rol, seleccionar Servicio de AWS, en Servicio o caso de uso se debe escoger Lambda, se debe continuar y donde dice Nombre del rol se debe escribir el siguiente: 
```
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogGroup",
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": "arn:aws:logs:*:*:*"
		},
		{
			"Effect": "Allow",
			"Action": [
				"s3:GetObject"
			],
			"Resource": [
				"arn:aws:s3:::actores/*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"dynamodb:PutItem"
			],
			"Resource": [
				"arn:aws:dynamodb:us-east-1:637423633559:table/face_recognition"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"rekognition:IndexFaces"
			],
			"Resource": "*"
		}
	]
}
```


