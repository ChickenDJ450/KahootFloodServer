from http.server import BaseHTTPRequestHandler,HTTPServer

import urllib.parse as urlparse


from main import kahoot
import threading
import sys
import time


PORT_NUMBER = 8080



def kahoot_run(pin, x, name):
  send = kahoot(pin, name+str(x))
  send.connect()

def GameExists(pin):
  send = kahoot(pin, "Test Name")
  return send.reserve_session()


def sendData(self, data):
  self.wfile.write(str(data).encode())
  

class myHandler(BaseHTTPRequestHandler):
  
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/text')
        self.end_headers()
        
        query_components = urlparse.parse_qs(urlparse.urlparse(self.path).query)

        if (len(query_components) > 0):
            if('game' in query_components) and ('basename' in query_components) and ('count' in query_components):
                pin = query_components['game'][0]
                name = query_components['basename'][0]
                count = int(query_components['count'][0])
                if GameExists(pin):
                    print('Connect to ' + pin)
                    sendData(self,"connecting ...")
                    for x in range(count):
                      time.sleep(0.1)
                      
                      print(('[{}] Client Connect').format(x+1)) #x+1 for print from 1
                      t = threading.Thread(target=kahoot_run, args=(pin,x+1,name,)) #x+1 for name start from 1
                      t.daemon = True
                      t.start()

                      
                else:
                    sendData(self, "Game does not exists with that pin")

        else:
            self.wfile.write(str('Error').encode())

        return

try:
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    print ('Started httpserver on port ' , PORT_NUMBER)
    server.serve_forever()

except KeyboardInterrupt:
    print ('^C received, shutting down the web server')
    server.socket.close()





