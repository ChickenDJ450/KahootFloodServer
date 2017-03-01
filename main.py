import requests
import json
import time
import threading
import sys
import base64
import array
import urllib.parse


requests.packages.urllib3.disable_warnings()


def error(err_no, err_desc, end, printErr=True):
  import datetime
  if printErr:
    print("Error:  "+str(err_no)+'  - ',err_desc)
  error_dec = "Time: "+str(datetime.datetime.now())+" Error no: " + str(err_no) + "  " + err_desc + "\n"
  with open('log.txt', 'a') as afile:
    afile.write(error_dec)
  if end:
    print('end')
    sys.exit()

def get_tc():
  return int(time.time() * 1000)

def get_o():
  return int(-14)

def get_l():
  return int(0)


class kahoot:
  def __init__(self, pin, name):
    self.pin = pin
    self.name = name
    self.s = requests.Session()
    self.requests = {}
    self.headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:43.0) Gecko/20100101 Firefox/43.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'DNT': '1',
        'Referer':'https://kahoot.it/'
        }

    self.queue = []
    self.questionNo = 0
    self.end = False
    self.kahoot_session = ''
    self.kahoot_raw_session = ''
    self.subId = 12
    self.ackId = 1
    self.challenge = 0


  def ordinal(self, n):
    if 10 <= n % 100 < 20:
        return str(n) + 'th'
    else:
       return  str(n) + {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(n % 10, "th")

  def get_ackID(self):
      self.ackId = self.ackId + 1
      return self.ackId

  def make_first_payload(self):
    data = [{"advice": {"interval": 0, "timeout": 60000}, "channel": "/meta/handshake", "ext": {"ack": True, "timesync": {"l": get_l(), "o": get_o(), "tc": get_tc()}}, "id": "2", "minimumVersion" : "1.0", "supportedConnectionTypes": ["long-polling"], "version": "1.0"}]
    return str(json.dumps(data))

  def make_sub_payload(self, subId, chan, sub):
    chan = str(chan)
    subId = str(int(subId))
    sub = str(sub)
    data = [{"channel": "/meta/"+chan, "clientId": self.clientid, "ext": {"timesync": {"l": get_l(), "o": get_o(), "tc": get_tc()}}, "id": subId, "subscription": "/service/" + sub}]
    return str(json.dumps(data))

  def make_first_con_payload(self, subId):
    subId = str(int(subId))
    data = [{"advice": {"timeout": 0}, "channel": "/meta/connect", "clientId": self.clientid, "connectionType": "long-polling", "ext": {"ack": 1, "timesync": {"l": get_l(), "o": get_o(), "tc": get_tc()}}, "id": subId}]
    return str(json.dumps(data))

  def make_second_con_payload(self, ack):
    subId = str(int(self.subId))
    data = [{"channel": "/meta/connect", "clientId": self.clientid, "connectionType": "long-polling", "ext": {"ack": self.get_ackID(), "timesync": {"l": get_l(), "o": get_o(), "tc": get_tc()}}, "id": subId}]
    return str(json.dumps(data))

  def make_name_sub_payload(self, name):
    name = str(name)
    data = [{"channel": "/service/controller", "clientId": self.clientid, "data": {"gameid": self.pin, "host": "kahoot.it", "name": name, "type": "login"}, "id": "14"}]
    return str(json.dumps(data))


  def reserve_session(self):
    pin = str(self.pin)
    timecode = str(get_tc())
    url = "https://kahoot.it/reserve/session/"+pin+"/?"+timecode
    r = self.s.get(url, verify=False)
    try:
      data = json.loads(r.text)
      self.kahoot_raw_session = r.headers['x-kahoot-session-token']
      self.challenge = self.solve_kahoot_challenge(data['challenge'])
      return True
    except:
      error(909, 'No kahoot Game with that pin', False, False)
      return False

  def solve_kahoot_challenge(self, dataChallenge):
    htmlDataChallenge = urllib.parse.quote_plus(str(dataChallenge))
    url = "http://safeval.pw/eval?code="+htmlDataChallenge
    r = self.s.get(url, verify=False)
    return str(r.text)

  def set_kahoot_session(self):
    kahoot_session_bytes = base64.b64decode(self.kahoot_raw_session)
    challenge_bytes = str(self.challenge).encode("ASCII")
    bytes_list = []
    for i in range(len(kahoot_session_bytes)):
        bytes_list.append(kahoot_session_bytes[i] ^ challenge_bytes[i%len(challenge_bytes)])
    self.kahoot_session = array.array('B',bytes_list).tostring().decode("ASCII")

  def ping_session(self):
    pin = str(self.pin)
    url = "https://kahoot.it/cometd/"+pin+"/"+self.kahoot_session
    try:
      r = self.s.get(url, headers=self.headers, verify=False)
      if r.status_code != 400:
        print(r.text)
        error(1001, str(r.status_code)+str(r.text),False)
    except requests.exceptions.ConnectionError:
      error(subId+200, "Conection error",False)
      print("Connection Refused")



  def handshake(self):
    pin = str(self.pin)
    url = "https://kahoot.it/cometd/"+pin+"/"+self.kahoot_session+"/handshake"
    data = self.make_first_payload()
    try:
      r = self.s.post(url, data=data, headers=self.headers, verify=False)
      if r.status_code != 200:
        print(r.text)
        error(1002, str(r.status_code)+str(r.text),False)
    except requests.exceptions.ConnectionError:
      error(107, "Conection error", True)
      print("Connection Refused")
    except:
      error(108, "handshake error", True)
    response = json.loads(r.text)
    return str(response[0]["clientId"])

  def send(self, func):
    pin = str(self.pin)
    data = func
    url = "https://kahoot.it/cometd/"+pin+"/"+self.kahoot_session+"/"
    try:
      r = self.s.post(url, data=data, headers=self.headers, verify=False)
      if r.status_code != 200:
        error(subId+100, str(r.status_code)+str(r.text),False)
    except requests.exceptions.ConnectionError:
      error(subId+200, "Conection error",False)
      print("Connection Refused")
    response = json.loads(r.text)
    return response[0]["successful"] == True

  def connect_while(self):
    pin = str(self.pin)
    while True:
      self.subId = self.subId + 1
      data = self.make_second_con_payload(self.subId)
      url = "https://kahoot.it/cometd/"+pin+"/"+self.kahoot_session+"/connect"
      try:
        r = self.s.post(url, data=data, headers=self.headers, verify=False)
        if r.status_code != 200:
          error(self.subId+100, str(r.status_code)+str(r.text),False)
      except requests.exceptions.ConnectionError:
        error(self.subId+200, "Conection error",False)
        print("Connection Refused")
      try:
        response = json.loads(r.text)
        if len(response) > 0:
          for i,x in enumerate(response):
            if x['channel'] != "/meta/connect":
              self.queue.append(x)
      except:
        print(r)
        error(12, "self.connect_while error" + str(r.text), False)


  def queue_wait(self):
    while True:
      while len(self.queue) > 0:
        for i, x in enumerate(self.queue):
          if x['channel'] == "/service/player":
            self.service_player(x['data'])
          self.queue.remove(x)
      else:
        time.sleep(0.1)


  def connect_first(self):
    pin = str(self.pin)
    data = self.make_first_con_payload(6)
    url = "https://kahoot.it/cometd/"+pin+"/"+self.kahoot_session+"/connect"
    try:
      r = self.s.post(url, data=data, headers=self.headers, verify=False)
      if r.status_code != 200:
        error(self.subId+100, str(r.status_code)+str(r.text),False)
    except requests.exceptions.ConnectionError:
      error(self.subId+200, "Conection error",False)
      print("Connection Refused")
    try:
      response = json.loads(r.text)
      if len(response) > 1:
        for i,x in enumerate(response):
          if x['channel'] != "/meta/connect":
            self.queue.append(x)
    except:
      print(r)
      error(12, "self.connect_first error" + str(r.text), False)

  def run_connect_while(self):
    t = threading.Thread(target=self.connect_while)
    t.daemon = True
    t.start()

  def run_connect_first(self):
    t = threading.Thread(target=self.connect_first)
    t.daemon = True
    t.start()

  def run_game(self):
    t = threading.Thread(target=self.queue_wait)
    t.daemon = True
    t.start()

  def connect(self):
    if self.reserve_session():
      self.set_kahoot_session()
      self.ping_session()
      self.clientid = self.handshake()
      self.run_connect_first()
      subscribe_order = ["subscribe", "unsubscribe", "subscribe"]
      subscribe_text = ["controller", "player", "status"]
      for x in range(3):
        for y in range(3):
          self.send(self.make_sub_payload(x*3+(y+1), subscribe_text[y], subscribe_order[x]))
      self.run_connect_while()
      self.send(self.make_name_sub_payload(self.name))
    else:
      error(909, "no game with pin", True)
