#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import urllib2
import sys
import socket
import SimpleHTTPServer
import SocketServer
import argparse
import time
import datetime


cwd, filename=  os.path.split(os.path.abspath(__file__))

def upServer(port=3000):
	Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
	httpd = SocketServer.TCPServer(("", int(port)), Handler)
	ip = getIpServer()
	print "[*] Servidor Local Levantado en:"
	print "[*] http://"+ip+":"+str(port)+"/"
	print ""
	print "-------------------------------------------------------------------------------------------"
	print listfile(ip,port)
	print "-------------------------------------------------------------------------------------------"
	print "Ctrl + C para Salir."
	print ""
	httpd.serve_forever()



def getIpServer():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("8.8.8.8", 80))
	LHOST = s.getsockname()[0]
	s.close()
	return LHOST

def downloadyoutube(url,tipo):
	if tipo=="mp3":
		print "[*] Espere un momento......"
		os.system("youtube-dl -x --audio-format mp3 "+url+" -o "+cwd+"/musica/mp3"+str(time.time())+".mp3")
		print "[-] Descarga Completada..."
	elif tipo =="mp4":
		print "[*] Espere un momento......"
		os.system("youtube-dl "+url+" -o "+cwd+"/video/mp4"+str(time.time())+".mp4")
		print "[-] Descarga Completada..."
	elif tipo=="all":
		print "[*] Espere un momento......"
		os.system("youtube-dl -x --audio-format mp3 "+url+" -o "+cwd+"/musica/mp3"+str(time.time())+".mp3")
		os.system("youtube-dl "+url+" -o "+cwd+"/video/mp4"+str(time.time())+".mp4")
		print "[-] Descarga Completada..."
		
	else:
		print "[!] Formato no soportado.."
	print ""

def downloadImage(url):
    try:
	    print "[*] Espere un momento......"
	    os.system("wget "+url+" -P "+cwd+"/imagen/")
	    print "[-] Descarga Completada..."
    except:
	    pass
    print ""

def makedir():
    try:
	   os.stat("musica")
	   os.stat("video")
	   os.stat("imagen")
	   print ""
    except:
	   print "creando directorios..."
           os.mkdir("musica")
	   os.mkdir("video")
           os.mkdir("imagen")
	   print ""

def listfile(ip,port=3000):
	
	directory = ['musica','video','imagen']
	for d in directory:
		print "[*] Archivos en "+ d + ":"
		dirs = os.listdir( d )
		if len(dirs) > 0:
			for archivo in dirs:
		  	 print "  [-] http://" +ip +":"+str(port)+"/"+d+"/"+archivo
		else:
			print "  [!] Sin Archivos en la Carpeta "+d
	print ""

def help():
	parser = argparse.ArgumentParser("Uso: python assistent.py --httpserver --port 8000")
	parser.add_argument('--url', help='URL del recurso ')
	parser.add_argument('--port', help='Puerto a la Escucha Servidor Local')
	parser.add_argument('--httpserver', action="store_true",help='Levantar Servidor local')
	parser.add_argument('--listserver',action="store_true", help='Listar archivos Servidor')
	parser.add_argument('--dyoutubemp4',action="store_true", help='Transforma URL youtube a mp4 y descarga archivo')
	parser.add_argument('--dyoutubemp3',action="store_true", help='Transforma URL youtube a mp3 y descarga archivo')
	parser.add_argument('--dyoutubeall',action="store_true", help='Transforma URL youtube a mp3/mp4 y descarga archivos')
	parser.add_argument('--dimage', action="store_true",help='Descarga archivo imagen')
	parser.add_argument('--version', action='version', version='%(prog)s 1.0')
        return parser.parse_args()	

print """
     
	████████╗ █████╗ ██╗  ██╗███████╗████████╗██╗   ██╗
	╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝██║   ██║
	   ██║   ███████║█████╔╝ █████╗     ██║   ██║   ██║
	   ██║   ██╔══██║██╔═██╗ ██╔══╝     ██║   ╚██╗ ██╔╝
	   ██║   ██║  ██║██║  ██╗███████╗   ██║    ╚████╔╝ 
	   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝     ╚═══╝  
                                                                       
      Servidor WEB LOCAL y Asistente de Descargas de Archivos Multimedia.
      Autor: @svelizdonoso

"""

h = help()
makedir()

if h.httpserver:
	if h.port =="":
		upServer(3000)
	else:
		upServer(h.port)
if h.url and h.dyoutubemp4:
	downloadyoutube(h.url,"mp4")
if h.url and h.dyoutubemp3:
	downloadyoutube(h.url,"mp3")
if h.url and h.dimage:
	downloadImage(h.url)
if h.url and h.dyoutubeall:
	downloadyoutube(h.url,"all")
if h.listserver:
	ip = getIpServer()
	listfile(ip)
	



		
