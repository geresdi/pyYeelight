import socket as s
import json as j
from time import sleep

class YeelightControl:
    
    def __init__(self):
        self._refresh = 0
        self._ip = ""
        self._port = ""
        self._id = 0
        self._model = ""
        self._version = 0
        self._commands = []
        self._brightness = -1
        self._mode = -1
        self._temperature = 0
        self._rgb = 0
        self._hue = 0
        self._saturation = 0
        self._name = ""
        self._powered = False

    
    def discover(self):
        d_message= "M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1982\r\nMAN: \"ssdp:discover\"\r\nST: wifi_bulb\r\n"
        d_IP = "239.255.255.250"
        d_port = 1982
        d_sock = s.socket(s.AF_INET,s.SOCK_DGRAM)
        d_sock.settimeout(1.0)
        d_sock.sendto(d_message.encode(),(d_IP,d_port))
        d_result = d_sock.recv(1024).decode().split('\r\n')
        if d_result[0].strip() ==  "HTTP/1.1 200 OK":
            self._refresh = int(d_result[1].split("=")[1])
            self._ip = d_result[4].split(":")[2][2:]
            self._port = int(d_result[4].split(":")[3])
            self._id = int(d_result[6].split(":")[1],0)
            self._model = d_result[7].split(":")[1].strip()
            self._version = int(d_result[8].split(":")[1])
            self._commands = d_result[9].split(":")[1].strip().split(" ")
            self._powered = (d_result[10].split(":")[1].strip() == "on")
            self._brightness = int(d_result[11].split(":")[1])
            self._mode = int(d_result[12].split(":")[1])
            self._temperature = int(d_result[13].split(":")[1])
            self._rgb = int(d_result[14].split(":")[1])
            self._hue = int(d_result[15].split(":")[1])
            self._saturation = int(d_result[16].split(":")[1])
            self._name = d_result[17].split(":")[1].strip()
            d_sock.close()
            return True
        d_sock.close()
        return False

    def connect(self):
        com_sock = s.socket(s.AF_INET,s.SOCK_STREAM)
        com_sock.settimeout(1.0)
        if com_sock.connect_ex((self._ip,self._port)) == 0:
            self._com_sock = com_sock
            return True
        return False
    
    def disconnect(self):
        if self._com_sock is not None:
            self._com_sock.close()
            return True
        return False
    
    @property
    def refresh(self):
        return self._refresh
    
    @property
    def ip(self):
        return self._ip
    
    @property
    def port(self):
        return self._port
    
    @property
    def id(self):
        return self._id
    
    @property
    def model(self):
        return self._model
    
    @property
    def version(self):
        return self._version
    
    @property
    def commands(self):
        return self._commands
    
    @property
    def powered(self):
        message = {"id":1,"method":"get_prop","params":["power"]}
        return j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0].strip() == "on"

    @powered.setter
    def powered(self,val):
        if val: 
            m = "on"
        else: 
            m = "off"
        message = {"id":1,"method":"set_power","params":[m,"sudden", 0]}
        self._comm(j.JSONEncoder().encode(message)+"\r\n")
        
    def toggle(self):
        message = {"id":1,"method":"toggle","params":[]}
        self._comm(j.JSONEncoder().encode(message)+"\r\n")
        
    @property
    def name(self):
        message = {"id":1,"method":"get_prop","params":["name"]}
        return j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0].strip()
    
    @name.setter
    def name(self,val):
        message = {"id":1,"method":"set_name","params":[val]}
        self._send(j.JSONEncoder().encode(message)+"\r\n")
        
    @property
    def brightness(self):
        message = {"id":1,"method":"get_prop","params":["bright"]}
        return int(j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0])
    
    @brightness.setter
    def brightness(self,val):
        val = int(val)
        if val < 1 or val > 100:
            return False
        message = {"id":1,"method":"set_bright","params":[val,"sudden",0]}
        self._comm(j.JSONEncoder().encode(message)+"\r\n")
        
    @property
    def temperature(self):
        message = {"id":1,"method":"get_prop","params":["ct"]}
        return int(j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0])
    
    @temperature.setter
    def temperature(self,val):
        val = int(val)
        if val < 1700 or val > 6500:
            return False
        message = {"id":1,"method":"set_ct_abx","params":[val,"sudden",0]}
        self._comm(j.JSONEncoder().encode(message)+"\r\n")
        
    @property
    def rgb(self):
        message = {"id":1,"method":"get_prop","params":["rgb"]}
        val=int(j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0])
        b = val % 256
        g = (val % 65536) // 256
        r = (val - b - g) // 65536
        return {'raw': val, 'r':r, 'g':g, 'b':b}  
    
    @rgb.setter
    def rgb(self,colors):
        r = int(colors[0])
        g = int(colors[1])
        b = int(colors[2])
        if r < 0 or r > 255 or b < 0 or b > 255 or g < 0 or g > 255:
            return False
        val = 65536 * r + 256 * g + b 
        message = {"id":1,"method":"set_rgb","params":[val,"sudden",0]}
        self._comm(j.JSONEncoder().encode(message)+"\r\n")

    @property
    def hue(self):
        message = {"id":1,"method":"get_prop","params":["hue"]}
        val=int(j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0])
        return val
    
    #TODO: set hue via set_hsv
    
    @property
    def saturation(self):   
        message = {"id":1,"method":"get_prop","params":["sat"]}
        val=int(j.JSONDecoder().decode(self._comm(j.JSONEncoder().encode(message)+"\r\n"))["result"][0])
        return val     
    
    #TODO: set saturation via set_hsv
    
    
    #low level communication
        
    def _comm(self, message):
        if self._send(message) == True:
            return self._receive()
        return False
    
    def _send(self, message):
        if self._com_sock.sendall(message.encode()) == None:
            return True
        return False
    
    def _receive(self):
        sleep(0.2)
        #ret = self._com_sock.recv(4096).decode()
        #print(ret)
        #return ret.split('\r\n')[-2]
        return self._com_sock.recv(1024).decode().split('\r\n')[-2]

    