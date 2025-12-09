import time
import paho.mqtt.client as mqtt
import circuit
import threading
from collections import deque

auth_Lock = threading.Lock() #인증 요청이 동시에 들어올 떄 중복 실행 방지용 Lock
auth_running = False # auth()인증이 실행중인지 여부
stop_flag = False #센서 스레드 종료 플래그
auth_start_flag = False
start_time = 0 # 착석/부재 기준 거리 기록 시작 시간, 현재 시간 저장
endtime = 0  # 착석/부재 기준 거리 기록이 끝나는 시간 
seattingD = [] # 착석 기준 거리 계산용 측정값을 저장할 리스트 
seat_base = 50 # 착석 판단 기준 거리 초기값
state_que = deque(maxlen=10) # 착석 여부 상태를 10개 저장해서 안정된 상태 판단

def on_connect(client, userdata, flag, rc, prop=None):
        #"authReq"는 시작하기, 떠나기, 책제목입력, 머무름 인증요청 버튼에서 publish
        client.subscribe("authReq") # "authReq" 토픽으로 구독 신청

def on_message(client, userdata, msg) : # mqttio.js에서 "authReq"토픽이 발행되면 실행 
        global auth_running
        # 블록에 진입할 때 auth_Lock.acquire메서드가 호출, 인증요청은 한 번에 한 개만 처리
        with auth_Lock: 
                if not auth_running:
                        auth_running = True
                        threading.Thread(target=auth, args=(client, msg.payload),daemon=True).start() # 인증을 새 스레드로 실행
        # 블록을 벗어날 때 auth.Lock.release가 호출
                      
def auth(client, message): # 인증하기 
        global auth_running
        global seattingD
        isAuth = circuit.auth_temp_humi() # 입김으로 온습도 인증-온습도 예외시 스위치로 인증
        splitmsg = message.decode().split(":") #"authReq"토픽의 메시지로 할 일을 정하기
        if(splitmsg[0] == "checkAuth"): # 외부 인증에 결과 보내기 
                client.publish("authResult", "success" if isAuth else "fail")
                auth_running = False
        elif(splitmsg[0] == "inputAuth"): # 책제목 입력 인증에 결과 보내기
                client.publish("authResult", "Book title:"+splitmsg[1] if isAuth else "reject")
                auth_running = False
        elif(splitmsg[0] == "setDistanceAuth"): # 착석 시작하기에 결과 보내기
                if isAuth: #인증에 성공하면 저장해둔 거리 측정값으로 착석 기준 거리 재설정
                        set_seat_base()
                client.publish("authResult", "sitting_Authed" if isAuth else "sitting_notAuthed")
                auth_running = False
        elif(splitmsg[0] == "notUse"): # 자리 떠나기에 결과 보내기
                if isAuth:
                        seattingD = [] # 자리 떠나면 착석 기록 초기화
                client.publish("authResult", "away_Authed" if isAuth else "away_notAuthed")
                auth_running = False

def set_seat_base(): #착석/부재 기준 거리 설정
        global seattingD 
        global seat_base 
        # 평균 +20cm 안까지는 착석으로 분류
        seat_base = sum(seattingD) / len(seattingD) + 20 
         
ip = "localhost" # 현재 브로커는 이 컴퓨터에 설치되어 있음

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

client.connect(ip, 1883) # 브로커에 연결
client.loop_start() # 메시지 루프를 실행하는 스레드 생성

def ultrasonic_loop(client):
        old_state = "" #이전 착석 상태 저장 
        global seat_base
        global state_que
        seat_logfile = open("seat_use_log.txt", "a", encoding="utf-8") #텍스트 기록
        while not stop_flag:
                distance = circuit.measure_distance() # 초음파 센서로부터 거리 읽기
                #최근 상태 10개가 모두 같으면 True, 착석중과 부재중이 섞여있으면 False 
                consistency = True
                state_que.append("착석중") if seat_base > distance else state_que.append("부재중")
                client.publish("ultrasonic", distance) # “ultrasonic” 토픽으로 거리 전송
                # 최근 10개 착석 상태가 동일한지 확인하여 튀는 측정값 무시
                if len(state_que) == state_que.maxlen:
                        for s in state_que:
                                if s != state_que[0]:
                                        consistency = False     
                if len(state_que) == state_que.maxlen and consistency:
                        state = state_que[0]
                        # 상태가 변했는지 확인하고 "seat/state" publish
                        if old_state != state:
                                client.publish("seat/state", state, retain=True)
                                old_state = state
                                # txt 파일에 기록 남기기
                                now = time.time()
                                timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                                seat_logfile.write(f"{timestamp}에 {state}\n")
                                seat_logfile.flush()
                global start_time 
                global endtime 
                global seattingD
                global auth_start_flag 
                #사용 시작 인증 시작을 확인, 3초 타이머 설정  
                if auth_running and not auth_start_flag :
                        auth_start_flag = True # 시간 기록을 1번만 실행하도록 막는 boolean
                        start_time = time.time()
                        endtime = time.time() + 3

                if time.time() < endtime:
                        seattingD.append(distance) # 거리 저장 
                else: # 타이머 시간 초기화
                        start_time = 0
                        endtime = 0 
                        auth_start_flag = False 
                        
                time.sleep(0.5) # 0.5초 동안 잠자기


def light_shadow_loop(client): # 독서대 책 넘김 그림자 측정
    from collections import deque # 큐로 이용함 

    light_result_que = deque(maxlen=10) #최근 조도 기록
    flip_cnt = 0 # 

    logfile = open("pageflip_log.txt", "a", encoding="utf-8") # 책장 넘김 저장
    while not stop_flag:
        val = circuit.getLight()  # ADC 채널 0
        client.publish("light", str(val)) #조도 publish

        light_result_que.append(val) # 조도가 10개 모이면 평균을 냄
        if len(light_result_que) == light_result_que.maxlen:
            avg = sum(light_result_que) / len(light_result_que)
            # 조도 급감시 그림자 발생-> 책 넘김으로 간주 
            # "shadowOnBook"publish, 텍스트 파일저장
            if avg - val > (avg/3):
                    now = time.time()
                    flip_cnt += 1
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                    msg = timestamp+","+str(flip_cnt)+"번"
                    client.publish("shadowOnBook",str(msg)) 
                    logfile.write(f"{timestamp}페이지 넘김 감지 (조도={val})\n")
                    logfile.flush()

        time.sleep(0.2)

    logfile.close()
# 초음파 측정, 조도, 페이지플립을 계속 측정받음
t1 = threading.Thread(target=ultrasonic_loop, args=(client, ), daemon=True)
t2 = threading.Thread(target=light_shadow_loop, args=(client, ), daemon=True)
t1.start()
t2.start()

try:
    while True:
        time.sleep(1) #메인 스레드를 쉬게 함
except KeyboardInterrupt:
    pass
finally:
    stop_flag = True #센서 while문 종료, 스레드를 종료시킴
    client.loop_stop() # 메시지 루프를 실행하는 스레드 종료
    client.disconnect()
