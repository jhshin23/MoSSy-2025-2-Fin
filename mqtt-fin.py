import time
import serial
import paho.mqtt.client as mqtt
import threading
from collections import deque

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 115200

auth_lock = threading.Lock()
auth_running = False
auth_request = None   # 인증 요청 메시지 저장
button_pressed = False

stop_flag = False
seat_base = 50
state_que = deque(maxlen=10)
seattingD = []
auth_start_flag = False
endtime = 0

def on_connect(client, userdata, flag, rc, prop=None):
    client.subscribe("authReq")

def on_message(client, userdata, msg):
    global auth_running, auth_request
    with auth_lock:
        if not auth_running:
            auth_running = True
            auth_request = msg.payload.decode()
            threading.Thread(target=auth, args=(client,), daemon=True).start()

def auth(client):
    global auth_running, button_pressed
    ser.write(b"LED:ON\n")
    button_pressed = False
    deadline = time.time() + 20
    while time.time() < deadline:
        if button_pressed:
            break
        time.sleep(0.1)
    isAuth = button_pressed
    button_pressed = False
    ser.write(b"LED:OFF\n")

    splitmsg = auth_request.split(":")
    if splitmsg[0] == "checkAuth":
        client.publish("authResult", "success" if isAuth else "fail")
    elif splitmsg[0] == "inputAuth":
        client.publish("authResult", "Book title:" + splitmsg[1] if isAuth else "reject")
    elif splitmsg[0] == "setDistanceAuth":
        if isAuth:
            set_seat_base()
        seattingD.clear()
        client.publish("authResult", "sitting_Authed" if isAuth else "sitting_notAuthed")
    elif splitmsg[0] == "notUse":
        if isAuth:
            seattingD.clear()
        client.publish("authResult", "away_Authed" if isAuth else "away_notAuthed")
    elif splitmsg[0] == "closeBook":
        client.publish("authResult", "book_closed" if isAuth else "book_close_notAuthed")
    auth_running = False

def set_seat_base():
    global seat_base
    if seattingD:
        seat_base = sum(seattingD) / len(seattingD) + 20

ip = "localhost"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(ip, 1883)
client.loop_start()

# 시리얼 읽기 + 센서 처리 루프
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

seat_logfile = open("seat_use_log.txt", "a", encoding="utf-8")
pageflip_logfile = open("pageflip_log.txt", "a", encoding="utf-8")
light_que = deque(maxlen=10)
flip_cnt = 0
old_state = ""
last_flip_time = 0
endtime = 0
auth_start_flag = False

try:
    while True:
        line = ser.readline().decode(errors='ignore').strip()
        if not line or not line.startswith('DIST:'):
            continue

        try:
            parts = {}
            for item in line.split(','):
                k, v = item.split(':')
                parts[k] = v

            distance = float(parts['DIST'])
            pir = int(parts['PIR'])
            btn = int(parts['BTN'])
            light = int(parts['LIGHT'])
        except Exception:
            continue

        # 버튼 눌림 감지
        if btn == 1:
            button_pressed = True

        # 초음파 publish
        client.publish("ultrasonic", distance)

        # 착석 판단
        state_que.append("착석중" if (seat_base > distance or pir == 1) else "부재중")
        if len(state_que) == state_que.maxlen and len(set(state_que)) == 1:
            state = state_que[0]
            if old_state != state:
                client.publish("seat/state", state, retain=True)
                old_state = state
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                seat_logfile.write(f"{timestamp}에 {state}\n")
                seat_logfile.flush()

        # 착석 기준 거리 측정 타이머
        if auth_running and not auth_start_flag:
            auth_start_flag = True
            endtime = time.time() + 3
        if time.time() < endtime:
            seattingD.append(distance)
        else:
            endtime = 0
            auth_start_flag = False

        # 조도 publish
        client.publish("light", light)

        # 페이지 플립 감지
        light_que.append(light)
        if len(light_que) == light_que.maxlen:
            avg = sum(light_que) / len(light_que)
            now = time.time()
            if avg - light > (avg / 3) and now - last_flip_time > 0.4:
                last_flip_time = now
                flip_cnt += 1
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                msg = f"{timestamp},{flip_cnt}번"
                client.publish("shadowOnBook", msg)
                pageflip_logfile.write(f"{timestamp} 페이지 넘김 감지 (조도={light})\n")
                pageflip_logfile.flush()

except KeyboardInterrupt:
    pass
finally:
    stop_flag = True
    ser.close()
    seat_logfile.close()
    pageflip_logfile.close()
    client.loop_stop()
    client.disconnect()
