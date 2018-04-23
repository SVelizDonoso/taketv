# TakeTV
<img src="https://image.ibb.co/iZqizH/taketv.png" >

TakeTV permite descubrir dispositivos de red DLNA/UPnP y ayuda a reproducir archivos multimedia en los televisores inteligentes desde nuestra terminal en Linux.

# Dependencias
Antes de ejecutar el script asegúrate de tener instalado youtube-dl en tu Linux

```sh
sudo apt-get install youtube-dl
```

# Dispositivos Testeados
```sh
[-] Smart TV AOC
[-] Smart TV Recco
[-] Smart TV Samsung
[-] Smart TV LG
[-] Android TV 
[-] ?
```

# Instalación
```sh
git clone https://github.com/SVelizDonoso/taketv.git
cd taketv
python taketv.py
```
# Opciones

```sh
python taketv.py -h

	████████╗ █████╗ ██╗  ██╗███████╗████████╗██╗   ██╗
	╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝██║   ██║
	   ██║   ███████║█████╔╝ █████╗     ██║   ██║   ██║
	   ██║   ██╔══██║██╔═██╗ ██╔══╝     ██║   ╚██╗ ██╔╝
	   ██║   ██║  ██║██║  ██╗███████╗   ██║    ╚████╔╝ 
	   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝     ╚═══╝  
                                                                       


                                                           
    Developer :@svelizdonoso                                                      
    GitHub: https://github.com/SVelizDonoso

    
taketv.py [--ip <dispositivo>] [--all] [-t[imeout] <segundos>] [--play <url>] [--pause] [--stop]
 --ip <dispositivo> - ip de la TV
 --all - descubrimiento de equipos por upnp 
 --play <url> - url de el la imagen,musica o video. en caso de estar vacia reproduce el recurso anterior.
 --pause - pausar el recurso
 --stop - parar el recurso
 --mute - mute playback
 --unmute - quitar volumen
 --volume <vol> - agregar o quitar volumen
 --seek <tiempon> en HH:MM:SS> - definir donde parte la pista
 --timeout <segundos> - tiempo espera descubrimiento
 --help - ayuda uso del script
```
# Uso de la Herramienta
Detección de Dispositivos 
```sh
python taketv.py --all --timeout 7



	████████╗ █████╗ ██╗  ██╗███████╗████████╗██╗   ██╗
	╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝██║   ██║
	   ██║   ███████║█████╔╝ █████╗     ██║   ██║   ██║
	   ██║   ██╔══██║██╔═██╗ ██╔══╝     ██║   ╚██╗ ██╔╝
	   ██║   ██║  ██║██║  ██╗███████╗   ██║    ╚████╔╝ 
	   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝     ╚═══╝  
                                                                       


                                                           
    Developer :@svelizdonoso                                                      
    GitHub: https://github.com/SVelizDonoso

    
[*] Lista de Dispositivos Detectados: 

[-]  [   Otro   ] Nombre: Technicolor TG789vn v3 (1345RA35L) | IP: 192.168.1.1
[-]  [ TV Media ] Nombre: eHomeMediaCenter | IP: 192.168.1.111
[-]  [ TV Media ] Nombre: TV Set | IP: 192.168.1.130

```
Reproducir imagen
```sh
python taketv.py --ip 192.168.1.130 --play http://servidor/img/1.jpg
```
Reproducir audio
```sh

python taketv.py --ip 192.168.1.130 --play http://servidor/mus/1.mp3
```
Reproducir video
```sh
python taketv.py --ip 192.168.1.130 --pause http://servidor/vid/1.mp4
```
Detener
```sh
python taketv.py --ip 192.168.1.130 --stop 
```
Quitar Sonido 
```sh
python taketv.py --ip 192.168.1.130 --mute 
```
Agregar sonido 
```sh
python taketv.py --ip 192.168.1.130 --unmute
```
 Sonido nivel 5
```sh
python taketv.py --ip 192.168.1.130 ----volume 5
```

# Uso asistente
TakeTV tiene un asistente que permite levantar un servidor HTTP local. además ayuda a descargas imágenes y archivos multimedia de Youtube(mp4/mp3)

```sh
python assistent.py -h

     

	████████╗ █████╗ ██╗  ██╗███████╗████████╗██╗   ██╗
	╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝██║   ██║
	   ██║   ███████║█████╔╝ █████╗     ██║   ██║   ██║
	   ██║   ██╔══██║██╔═██╗ ██╔══╝     ██║   ╚██╗ ██╔╝
	   ██║   ██║  ██║██║  ██╗███████╗   ██║    ╚████╔╝ 
	   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝     ╚═══╝  
                                                                       


      Servidor WEB LOCAL y Asistente de Descargas de Archivos Multimedia.
      Autor: @svelizdonoso

	


usage: Uso:python assistent.py --httpserver --port 8000  [-h] [--url URL]
                                                         [--port PORT]
                                                         [--httpserver]
                                                         [--listserver]
                                                         [--dyoutubemp4]
                                                         [--dyoutubemp3]
                                                         [--dyoutubeall]
                                                         [--dimage]
                                                         [--version]

optional arguments:
  -h, --help     show this help message and exit
  --url URL      URL del recurso
  --port PORT    Puerto a la Escucha Servidor Local
  --httpserver   Levantar Servidor local
  --listserver   Listar archivos Servidor
  --dyoutubemp4  Transforma URL youtube a mp4 y descarga archivo
  --dyoutubemp3  Transforma URL youtube a mp3 y descarga archivo
  --dyoutubeall  Transforma URL youtube a mp3/mp4 y descarga archivos
  --dimage       Descarga archivo imagen
  --version      show program's version number and exit

```
Descargar mp4 de youtube a servidor local
```sh
python assistent.py --url https://www.youtube.com/watch?v=kUHgqiqQb6M --dyoutubemp4
```

Descargar mp3 de youtube a servidor local
```sh
python assistent.py --url https://www.youtube.com/watch?v=kUHgqiqQb6M --dyoutubemp4
```

Descargar mp3 y mp4 de youtube a servidor local
```sh
python assistent.py --url https://www.youtube.com/watch?v=kUHgqiqQb6M --dyoutubeall
```
Descargar imagen a servidor local
```sh
python assistent.py --url https://k32.kn3.net/taringa/6/8/5/2/5/C/LOBIZNO/70E.jpg --dimage
```
listar archivos del servidor local
```sh
python assistent.py --listserver

[*] Archivos en musica:
  [!] Sin Archivos en la Carpeta musica
[*] Archivos en video:
  [!] Sin Archivos en la Carpeta video
[*] Archivos en imagen:
  [!] Sin Archivos en la Carpeta imagen

```
Levantar servidor Web
```sh
python assistent.py --httpserver --port 8000



[*] Servidor Local Levantado en:
[*] http://192.168.1.148:8000/

-------------------------------------------------------------------------------------------
[*] Archivos en musica:
  [!] Sin Archivos en la Carpeta musica
[*] Archivos en video:
  [!] Sin Archivos en la Carpeta video
[*] Archivos en imagen:
  [!] Sin Archivos en la Carpeta imagen

None
-------------------------------------------------------------------------------------------
Ctrl + C para Salir.


```

# Advertencia
Este software se creo SOLAMENTE para fines educativos. No soy responsable de su uso. Úselo con extrema precaución.

# Autor
@svelizdonoso https://github.com/SVelizDonoso/


