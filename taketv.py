#!/usr/bin/env python
# -*- coding:utf-8 -*-


__version__ = "0.01"

import re
import sys
import time
import signal
import socket
import select
import logging
import traceback
import mimetypes
from contextlib import contextmanager


import os
py3 = sys.version_info[0] == 3
if py3:
    from urllib.request import urlopen
    from http.server import HTTPServer
    from http.server import BaseHTTPRequestHandler
else:
    from urllib2 import urlopen
    from BaseHTTPServer import BaseHTTPRequestHandler
    from BaseHTTPServer import HTTPServer

import shutil
import threading

SSDP_GROUP = ("239.255.255.250", 1900)
URN_AVTransport = "urn:schemas-upnp-org:service:AVTransport:1"
URN_AVTransport_Fmt = "urn:schemas-upnp-org:service:AVTransport:{}"

URN_RenderingControl = "urn:schemas-upnp-org:service:RenderingControl:1"
URN_RenderingControl_Fmt = "urn:schemas-upnp-org:service:RenderingControl:{}"

SSDP_ALL = "ssdp:all"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def _get_tag_value(x, i = 0):
   
   x = x.strip()
   value = ''
   tag = ''

   if x[i:].startswith('<?'):
      i += 2
      while i < len(x) and x[i] != '<':
         i += 1

   if x[i:].startswith('</'):
      i += 2
      in_attr = False
      while i < len(x) and x[i] != '>':
         if x[i] == ' ':
            in_attr = True
         if not in_attr:
            tag += x[i]
         i += 1
      return (tag.strip(), '', x[i+1:])

   if not x[i:].startswith('<'):
      return ('', x[i:], '')

   i += 1

   in_attr = False
   while i < len(x) and x[i] != '>':
      if x[i] == ' ':
         in_attr = True
      if not in_attr:
         tag += x[i]
      i += 1

   i += 1 
   
   empty_elmt = '<' + tag + ' />'
   closed_elmt = '<' + tag + '>None</'+tag+'>'
   if x.startswith(empty_elmt):
      x = x.replace(empty_elmt, closed_elmt)

   while i < len(x):
      value += x[i]
      if x[i] == '>' and value.endswith('</' + tag + '>'):        
         close_tag_len = len(tag) + 2 
         value = value[:-close_tag_len]
         break
      i += 1
   return (tag.strip(), value[:-1], x[i+1:])

def _xml2dict(s, ignoreUntilXML = False):

   if ignoreUntilXML:
      s = ''.join(re.findall(".*?(<.*)", s, re.M))

   d = {}
   while s:
      tag, value, s = _get_tag_value(s)
      value = value.strip()
      isXml, dummy, dummy2 = _get_tag_value(value)
      if tag not in d:
         d[tag] = []
      if not isXml:
         if not value:
            continue
         d[tag].append(value.strip())
      else:
         if tag not in d:
            d[tag] = []
         d[tag].append(_xml2dict(value))
   return d



def _xpath(d, path):

   for p in path.split('/'):
      tag_attr = p.split('@')
      tag = tag_attr[0]
      if tag not in d:
         return None

      attr = tag_attr[1] if len(tag_attr) > 1 else ''
      if attr:
         a, aval = attr.split('=')
         for s in d[tag]:
            if s[a] == [aval]:
               d = s
               break
      else:
         d = d[tag][0]
   return d



def _get_port(location):
   port = re.findall('http://.*?:(\d+).*', location)
   return int(port[0]) if port else 80


def _get_control_url(xml, urn):
   return _xpath(xml, 'root/device/serviceList/service@serviceType={}/controlURL'.format(urn))

@contextmanager
def _send_udp(to, packet):
   sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
   sock.sendto(packet.encode(), to)
   yield sock
   sock.close()

def _unescape_xml(xml):
   return xml.replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')

def _send_tcp(to, payload):
   try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(5)
      sock.connect(to)
      sock.sendall(payload.encode('utf-8'))
      #print "---------------------------------------------------------"
      #print "[-] Payload:"
      #print str(payload)
      #print "---------------------------------------------------------"
      data = sock.recv(2048)
      if py3:
         data = data.decode('utf-8')
      data = _xml2dict(_unescape_xml(data), True)

      errorDescription = _xpath(data, 's:Envelope/s:Body/s:Fault/detail/UPnPError/errorDescription')
      if errorDescription is not None:
         logging.error(errorDescription)
   except Exception as e:
      data = ''
   finally:
      sock.close()
   return data


def _get_location_url(raw):
    t = re.findall('\n(?i)location:\s*(.*)\r\s*', raw, re.M)
    if len(t) > 0:
        return t[0]
    return ''

def _get_friendly_name(xml):
   name = _xpath(xml, 'root/device/friendlyName')
   return name if name is not None else 'Desconocido'

def _get_serve_ip(target_ip, target_port=80):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target_ip, target_port))
    my_ip = s.getsockname()[0]
    s.close()
    return my_ip

class DlnapDevice:

   def __init__(self, raw, ip):
      self.__logger = logging.getLogger(self.__class__.__name__)
      self.__logger.info('=> Nuevo Div (ip = {}) initialization..'.format(ip))

      self.ip = ip
      self.ssdp_version = 1

      self.port = None
      self.name = 'Desconocido'
      self.control_url = None
      self.rendering_control_url = None
      self.has_av_transport = False

      try:
         self.__raw = raw.decode()
         self.location = _get_location_url(self.__raw)
         self.__logger.info('location: {}'.format(self.location))

         self.port = _get_port(self.location)
         self.__logger.info('port: {}'.format(self.port))

         raw_desc_xml = urlopen(self.location).read().decode()

         self.__desc_xml = _xml2dict(raw_desc_xml)
         self.__logger.debug('description xml: {}'.format(self.__desc_xml))

         self.name = _get_friendly_name(self.__desc_xml)
         self.__logger.info('friendlyName: {}'.format(self.name))

         self.control_url = _get_control_url(self.__desc_xml, URN_AVTransport)
         self.__logger.info('control_url: {}'.format(self.control_url))

         self.rendering_control_url = _get_control_url(self.__desc_xml, URN_RenderingControl)
         self.__logger.info('rendering_control_url: {}'.format(self.rendering_control_url))

         self.has_av_transport = self.control_url is not None
         self.__logger.info('=> inicializacion completa'.format(ip))
      except Exception as e:
         self.__logger.warning('Dispositivo (ip = {}) init exception:\n{}'.format(ip, traceback.format_exc()))

   def __repr__(self):
      return 'Nombre: {} | IP: {}'.format(self.name, self.ip)

   def __eq__(self, d):
      return self.name == d.name and self.ip == d.ip

   def _payload_from_template(self, action, data, urn):

      fields = ''
      for tag, value in data.items():
        fields += '<{tag}>{value}</{tag}>'.format(tag=tag, value=value)

      payload = """<?xml version="1.0" encoding="utf-8"?>
         <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
            <s:Body>
               <u:{action} xmlns:u="{urn}">
                  {fields}
               </u:{action}>
            </s:Body>
         </s:Envelope>""".format(action=action, urn=urn, fields=fields)
      return payload

   def _create_packet(self, action, data):

      if action in ["SetVolume", "SetMute", "GetVolume"]:
          url = self.rendering_control_url
          urn = URN_RenderingControl_Fmt.format(self.ssdp_version)
      else:
          url = self.control_url
          urn = URN_AVTransport_Fmt.format(self.ssdp_version)
      payload = self._payload_from_template(action=action, data=data, urn=urn)

      packet = "\r\n".join([
         'POST {} HTTP/1.1'.format(url),
         'User-Agent: {}/{}'.format(__file__, __version__),
         'Accept: */*',
         'Content-Type: text/xml; charset="utf-8"',
         'HOST: {}:{}'.format(self.ip, self.port),
         'Content-Length: {}'.format(len(payload)),
         'SOAPACTION: "{}#{}"'.format(urn, action),
         'Connection: close',
         '',
         payload,
         ])

      self.__logger.debug(packet)
      return packet

   def set_current_media(self, url, instance_id = 0):
      packet = self._create_packet('SetAVTransportURI', {'InstanceID':instance_id, 'CurrentURI':url, 'CurrentURIMetaData':'' })
      _send_tcp((self.ip, self.port), packet)

   def play(self, instance_id = 0):
      packet = self._create_packet('Play', {'InstanceID': instance_id, 'Speed': 1})
      _send_tcp((self.ip, self.port), packet)

   def pause(self, instance_id = 0):
      packet = self._create_packet('Pause', {'InstanceID': instance_id, 'Speed':1})
      _send_tcp((self.ip, self.port), packet)

   def stop(self, instance_id = 0):
      packet = self._create_packet('Stop', {'InstanceID': instance_id, 'Speed': 1})
      _send_tcp((self.ip, self.port), packet)


   def seek(self, position, instance_id = 0):
      packet = self._create_packet('Seek', {'InstanceID':instance_id, 'Unit':'REL_TIME', 'Target': position })
      _send_tcp((self.ip, self.port), packet)


   def volume(self, volume=10, instance_id = 0):
      packet = self._create_packet('SetVolume', {'InstanceID': instance_id, 'DesiredVolume': volume, 'Channel': 'Master'})

      _send_tcp((self.ip, self.port), packet)
      
      
   def get_volume(self, instance_id = 0):
      packet = self._create_packet('GetVolume', {'InstanceID':instance_id, 'Channel': 'Master'})
      _send_tcp((self.ip, self.port), packet)


   def mute(self, instance_id = 0):
      packet = self._create_packet('SetMute', {'InstanceID': instance_id, 'DesiredMute': '1', 'Channel': 'Master'})
      _send_tcp((self.ip, self.port), packet)

   def unmute(self, instance_id = 0):
      packet = self._create_packet('SetMute', {'InstanceID': instance_id, 'DesiredMute': '0', 'Channel': 'Master'})
      _send_tcp((self.ip, self.port), packet)

   def info(self, instance_id=0):
      packet = self._create_packet('GetTransportInfo', {'InstanceID': instance_id})
      return _send_tcp((self.ip, self.port), packet)

   def media_info(self, instance_id=0):
      packet = self._create_packet('GetMediaInfo', {'InstanceID': instance_id})
      return _send_tcp((self.ip, self.port), packet)


   def position_info(self, instance_id=0):
      packet = self._create_packet('GetPositionInfo', {'InstanceID': instance_id})
      return _send_tcp((self.ip, self.port), packet)


   def set_next(self, url):
      pass

   def next(self):
      pass


def discover(name = '', ip = '', timeout = 1, st = SSDP_ALL, mx = 3, ssdp_version = 1):
   st = st.format(ssdp_version)
   payload = "\r\n".join([
              'M-SEARCH * HTTP/1.1',
              'User-Agent: {}/{}'.format(__file__, __version__),
              'HOST: {}:{}'.format(*SSDP_GROUP),
              'Accept: */*',
              'MAN: "ssdp:discover"',
              'ST: {}'.format(st),
              'MX: {}'.format(mx),
              '',
              ''])
   devices = []
   with _send_udp(SSDP_GROUP, payload) as sock:
      start = time.time()
      while True:
         if time.time() - start > timeout:
            break
         r, w, x = select.select([sock], [], [sock], 1)
         if sock in r:
             data, addr = sock.recvfrom(1024)
             if ip and addr[0] != ip:
                continue

             d = DlnapDevice(data, addr[0])
             d.ssdp_version = ssdp_version
             if d not in devices:
                if not name or name is None or name.lower() in d.name.lower():
                   if not ip:
                      devices.append(d)
                   elif d.has_av_transport:
                      devices.append(d)
                      break

         elif sock in x:
             raise Exception('Getting response failed')
         else:
             pass
   return devices

def banner():
    print """


	████████╗ █████╗ ██╗  ██╗███████╗████████╗██╗   ██╗
	╚══██╔══╝██╔══██╗██║ ██╔╝██╔════╝╚══██╔══╝██║   ██║
	   ██║   ███████║█████╔╝ █████╗     ██║   ██║   ██║
	   ██║   ██╔══██║██╔═██╗ ██╔══╝     ██║   ╚██╗ ██╔╝
	   ██║   ██║  ██║██║  ██╗███████╗   ██║    ╚████╔╝ 
	   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝     ╚═══╝  
                                                                       


                                                           
    Developer :@svelizdonoso                                                      
    GitHub: https://github.com/SVelizDonoso

    """

def signal_handler(signal, frame):
   print(' Ctrl + C, para salir')
   sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
   import getopt
   banner()
   def usage():
      
      print('{} [--ip <dispositivo>] [--all] [-t[imeout] <segundos>] [--play <url>] [--pause] [--stop]'.format(__file__))
      print(' --ip <dispositivo> - ip de la TV')
      print(' --all - descubrimiento de equipos por upnp ')
      print(' --play <url> - url de el la imagen,musica o video. en caso de estar vacia reproduce el recurso anterior.')
      print(' --pause - pausar el recurso')
      print(' --stop - parar el recurso')
      print(' --mute - mute playback')
      print(' --unmute - quitar volumen')
      print(' --volume <vol> - agregar o quitar volumen')
      print(' --seek <tiempon> en HH:MM:SS> - definir donde parte la pista')
      print(' --timeout <segundos> - tiempo espera descubrimiento')
      print(' --help - ayuda uso del script')
      print ""

   def version():
      print(__version__)

   try:
      opts, args = getopt.getopt(sys.argv[1:], "hvd:t:i:", [   # information arguments
                                                               'help',
                                                               'version',
                                                               'log=',

                                                               # device arguments
                                                               'device=',
                                                               'ip=',

                                                               # action arguments
                                                               'play=',
                                                               'pause',
                                                               'stop',
                                                               'volume=',
                                                               'mute',
                                                               'unmute',
                                                               'seek=',


                                                               # discover arguments
                                                               'list',
                                                               'all',
                                                               'timeout=',
                                                               'ssdp-version=',

                                                               # transport info
                                                               'info',
                                                               'media-info',
								])
   except getopt.GetoptError:
      usage()
      sys.exit(1)

   device = ''
   url = ''
   vol = 10
   position = '00:00:00'
   timeout = 1
   action = ''
   logLevel = logging.WARN
   compatibleOnly = False
   ip = ''
   proxy = False
   proxy_port = 8000
   ssdp_version = 1


   for opt, arg in opts:
      if opt in ('-h', '--help'):
         usage()
         sys.exit(0)
      elif opt in ('-v', '--version'):
         version()
         sys.exit(0)
      elif opt in ('--log'):
         if arg.lower() == 'debug':
             logLevel = logging.DEBUG
         elif arg.lower() == 'info':
             logLevel = logging.INFO
         elif arg.lower() == 'warn':
             logLevel = logging.WARN
      elif opt in ('--all'):
         compatibleOnly = False
      elif opt in ('-d', '--device'):
         device = arg
      elif opt in ('-t', '--timeout'):
         timeout = float(arg)
      elif opt in ('--ssdp-version'):
         ssdp_version = int(arg)
      elif opt in ('-i', '--ip'):
         ip = arg
         compatibleOnly = False
         timeout = 10
      elif opt in ('--list'):
         action = 'list'
      elif opt in ('--play'):
         action = 'play'
         url = arg
      elif opt in ('--pause'):
         action = 'pause'
      elif opt in ('--stop'):
         action = 'stop'
      elif opt in ('--volume'):
         action = 'volume'
         vol = arg
      elif opt in ('--seek'):
         action = 'seek'
         position = arg
      elif opt in ('--mute'):
         action = 'mute'
      elif opt in ('--unmute'):
         action = 'unmute'
      elif opt in ('--info'):
         action = 'info'
      elif opt in ('--media-info'):
         action = 'media-info'
      

   logging.basicConfig(level=logLevel)

   st = URN_AVTransport_Fmt if compatibleOnly else SSDP_ALL
   allDevices = discover(name=device, ip=ip, timeout=timeout, st=st, ssdp_version=ssdp_version)
   if not allDevices:
      print(bcolors.FAIL +'[!]  No se logro detectar dispositivos, por favor intentalo nuevamente...'+bcolors.ENDC )
      sys.exit(1)

   if action in ('', 'list'):
      print('[*] Lista de Dispositivos Detectados: ')
      print ""
      for d in allDevices:
         print bcolors.OKGREEN + ('[-]  {} {}'.format('[ TV Media ]' if d.has_av_transport else '[   Otro   ]', d))+bcolors.ENDC 
      print ""
      sys.exit(0)

   d = allDevices[0]
   print(d)


   if action == 'play':
      try:
         d.stop()
         d.set_current_media(url=url)
         d.play()
      except Exception as e:
         print(bcolors.FAIL+'[!] No se puedo realizar la tarea, por favor intantalo nuevamente....'+bcolors.ENDC )
         logging.warn('[!] Play exception:\n{}'.format(traceback.format_exc()))
         sys.exit(1)
   elif action == 'pause':
      d.pause()
   elif action == 'stop':
      d.stop()
   elif action == 'volume':
      d.volume(vol)
   elif action == 'seek':
      d.seek(position)
   elif action == 'mute':
      d.mute()
   elif action == 'unmute':
      d.unmute()
   elif action == 'info':
      print(d.info())
   elif action == 'media-info':
      print(d.media_info())

 
