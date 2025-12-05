import time
import paho.mqtt.client as mqtt
import circuit
import threading
import base64
from collections import deque

auth_Lock = threading.Lock()
auth_running = False
stop_flag = False
auth_start_flag = False
start_time = 0
endtime = 3 
seattingD = []
seat_base = 50 
state_que = deque(maxlen=10)

def on_connect(client, userdata, flag, rc, prop=None):
        client.subscribe("authReq") # "authReq" 토픽으로 구독 신청

def on_message(client, userdata, msg) :
        global auth_running
        with auth_Lock:
                if not auth_running:
                        auth_running = True
                        threading.Thread(target=auth, args=(client, msg.payload),daemon=True).start()
                      
def auth(client, message):
        print("auth is running")
        global auth_running
        global seattingD
        auth_logfile = open("auth_use_log.txt", "a", encoding="utf-8")
        isAuth = circuit.auth_temp_humi()
        splitmsg = message.decode().split(":")
        if(splitmsg[0] == "checkAuth"):
                client.publish("authResult", "success" if isAuth else "fail")
                log = "success" if isAuth else "fail"
                now = time.time()
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                auth_logfile(f"{timestamp}: 외부 인증 요청 -> 인증에 {log}")
                auth_running = False
        elif(splitmsg[0] == "inputAuth"):
                client.publish("authResult", "Book title:"+splitmsg[1] if isAuth else "reject")
                auth_running = False
        elif(splitmsg[0] == "setDistanceAuth"):
                if isAuth:
                        set_seat_base()
                client.publish("authResult", "sitting_Authed" if isAuth else "sitting_notAuthed")
                auth_running = False
        elif(splitmsg[0] == "notUse"):
                if isAuth:
                        seattingD = []
                client.publish("authResult", "away_Authed" if isAuth else "away_notAuthed")
                auth_running = False

def set_seat_base():
        global seattingD 
        global seat_base 
        seat_base = sum(seattingD) / len(seattingD) + 20 
         
ip = "localhost" # 현재 브로커는 이 컴퓨터에 설치되어 있음

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(ip, 1883) # 브로커에 연결
client.loop_start() # 메시지 루프를 실행하는 스레드 생성

def ultrasonic_loop(client):
        old_state = ""
        global seat_base
        global state_que
        seat_logfile = open("seat_use_log.txt", "a", encoding="utf-8")
        while not stop_flag:
                distance = circuit.measure_distance() # 초음파 센서로부터 거리 읽기
                consistency = True
                state_que.append("착석중") if seat_base > distance else state_que.append("부재중")
                client.publish("ultrasonic", distance) # “ultrasonic” 토픽으로 거리 전송
                if len(state_que) == state_que.maxlen:
                        for s in state_que:
                                if s != state_que[0]:
                                        consistency = False     
                if len(state_que) == state_que.maxlen and consistency:
                        state = state_que[0]
                        if old_state != state:
                                client.publish("seat/state", state, retain=True)
                                old_state = state
                                now = time.time()
                                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                                seat_logfile.write(f"{timestamp}에 {state}\n")
                                seat_logfile.flush()
                global start_time 
                global endtime 
                global seattingD
                global auth_start_flag 
                if auth_running and not auth_start_flag :
                        auth_start_flag = True 
                        start_time = time.time()
                        endtime = time.time() + 3

                if time.time() < endtime:
                        seattingD.append(distance)
                else:
                        start_time = 0
                        endtime = 3 
                        auth_start_flag = False 
                        
                time.sleep(0.5) # 1초 동안 잠자기


def light_shadow_loop(client):
    from collections import deque

    light_result_que = deque(maxlen=10)
    delta_light = 45  
    last_flip_time = 0
    flip_cnt = 0 

    logfile = open("pageflip_log.txt", "a", encoding="utf-8")
    while not stop_flag:
        val = circuit.getLight()  # ADC 채널 0
        client.publish("light", str(val))

        light_result_que.append(val)
        if len(light_result_que) == light_result_que.maxlen:
            avg = sum(light_result_que) / len(light_result_que)
            if val - avg > delta_light:
                    now = time.time()
                    if now - last_flip_time > 1.0:
                            last_flip_time = now
                            flip_cnt += 1
                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                            msg = timestamp+","+str(flip_cnt)+"쪽"
                            print(msg)
                            client.publish("shadowOnBook",str(msg)) 
                            logfile.write(f"{timestamp}페이지 넘김 감지 (조도={val})\n")
                            logfile.flush()

        time.sleep(0.2)

    logfile.close()

t1 = threading.Thread(target=ultrasonic_loop, args=(client, ), daemon=True)
t2 = threading.Thread(target=light_shadow_loop, args=(client, ), daemon=True)
t1.start()
t2.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    stop_flag = True
    client.loop_stop()
    client.disconnect()
