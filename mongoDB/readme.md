usuario: 				    dbUser
Contraseña: 				dbUserPassword

usuario: 				    dbRaspberry
Contraseña: 				dbRaspberryPassword

Instalar la librería en Python
NOTA: revisar versión de Python 	python -m pip install "pymongo[srv]==3.12"
sea mayor a 3.12 --------------                

URL para conectarse al cluster		mongodb+srv://dbUser:<db_password>@cluster0.aghdbrn.mongodb.net/?appName=Cluster0
con nuestra contraseña queda asi:	mongodb+srv://dbUser:dbUserPassword@cluster0.aghdbrn.mongodb.net/?appName=Cluster0


En el cluster tendremos:
			Database: 	    Arqui1_G2
			Colecciones:	Sensores
					        --------
					        --------
			


el .env tiene: 	    MONGODB_URI=mongodb+srv://dbUser:dbUserPassword@cluster0.aghdbrn.mongodb.net/?appName=Cluster0
					MONGODB_DB=Arqui1_G2				
					MONGODB_COLLECTION=Sensores -> NO VA EN EL .env por que tenemos muchas colecciones



CORRER EL PROGRAMA:
cd mongoDB
pip install python-dotenv
python -m pip install "pymongo[srv]==3.13"  // DEPENDE CUAL SEA TU VERSION DE PYTHON