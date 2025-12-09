import time
import RPi.GPIO as GPIO
from adafruit_htu21d import HTU21D
import busio
import Adafruit_MCP3008

# LED를 켜고 끄는 함수
def controlLED(led, on_off): # led 번호의 핀에 on_off(0: off/1: on) 값 출력하는 함수
        if (on_off):
                print("on") 
        else:
                print("off")
        GPIO.output(led, on_off)
	
#LED가 점점 밝아지는 함수
def increaseLED(): # 1초동안 듀티 사이클을 0~99로 1씩 증가
        pwm_green = GPIO.PWM(led_green, 100)
        pwm_yellow = GPIO.PWM(led_yellow, 100)
        pwm_green.start(0) 
        pwm_yellow.start(0) 
        for value in range(0, 100): # 1초동안 루프
                if(buttonFlag):
                        break
                pwm_green.ChangeDutyCycle(value) 
                pwm_yellow.ChangeDutyCycle(value) 
                time.sleep(0.01)
        pwm_green.stop()
        pwm_yellow.stop() 
        
#LED가 점점 어두워지는 함수
def decreaseLED(): # 1초동안 듀티 사이클을 99~0으로 1씩 감소
        pwm_green = GPIO.PWM(led_green, 100)
        pwm_yellow = GPIO.PWM(led_yellow, 100)
        pwm_green.start(100) 
        pwm_yellow.start(100) 
        for value in range(99, -1, -1): #1초동안 루프
                if(buttonFlag):
                        break
                pwm_green.ChangeDutyCycle(value) 
                pwm_yellow.ChangeDutyCycle(value) 
                time.sleep(0.01)
        pwm_green.stop()
        pwm_yellow.stop() 
        
# LED를 1초에 5번 깜빡이는 함수
def celebrateAuthLED(): 
        for i in range(5):
                controlLED(led_green, 0)
                controlLED(led_yellow, 0)
                time.sleep(0.2)
                controlLED(led_green, 1)
                controlLED(led_yellow, 1)
                time.sleep(0.2)
        controlLED(led_green, 0)
        controlLED(led_yellow, 0)

#스위치 콜백 함수
def isButton_pressed(channel):
        global buttonFlag
        buttonFlag = True 
 
# 초음파 센서를 제어하여 물체와의 거리를 측정하여 거리 값 리턴하는 함수
def measure_distance():
        global trig, echo
        time.sleep(0.2) # 초음파 센서의 준비 시간을 위해 200밀리초 지연
        GPIO.output(trig, 1) # trig 핀에 1(High) 출력
        time.sleep(0.00001)
        GPIO.output(trig, 0) # trig 핀에 0(Low) 출력. High->Low. 초음파 발사 지시

        while(GPIO.input(echo) == 0): # echo 핀 값이 0->1로 바뀔 때까지 루프
                pass

        # echo 핀 값이 1이면 초음파가 발사되었음
        pulse_start = time.time() # 초음파 발사 시간 기록
        while(GPIO.input(echo) == 1): # echo 핀 값이 1->0으로 바뀔 때까지 루프
                pass

        # echo 핀 값이 0이 되면 초음파 수신하였음
        pulse_end = time.time() # 초음파가 되돌아 온 시간 기록
        pulse_duration = pulse_end - pulse_start # 경과 시간 계산
        return pulse_duration*340*100/2 # 거리 계산하여 리턴(단위 cm)

def measure_temp_humi():
        global sensor
        # HTU21D 장치로부터 온도, 습도 값 읽어 리턴
        return float(sensor.temperature), float(sensor.relative_humidity)

def auth_temp_humi():
        global buttonFlag
        THRESHOLD_TEMP = 1 # 온도 변화 기준 
        THRESHOLD_HUMID = 7 # 습도 변화 기준
        THRESHOLD_SWITCH_TEMP = 29 # 스위치 인증으로 바꾸는 기준 온도
        THRESHOLD_SWITCH_HUMID = 55 # 스위치 인증으로 바꾸는 기준 습도
        result = False # 인증 결과를 저장
        base_temp, base_humi = [], [] #인증 요청 직후의 온습도 측정값을 저장
        end_time = time.time() + 2 # 온습도 평균을 구하기 위한 2초 
        while time.time() < end_time:
            time.sleep(1) # 1초 잠자기
            t, h = measure_temp_humi()
            base_temp.append(t)
            base_humi.append(h)
        #이렇게 사용자 몰래 2초동안 온습도 평균을 구해둠
        avrgT = sum(base_temp) / len(base_temp)
        avrgH = sum(base_humi) / len(base_humi)
        # 너무 덥거나 습하면 입김으로 변화폭이 적어지므로 스위치 인증 전환
        if(avrgT > THRESHOLD_SWITCH_TEMP or avrgH  > THRESHOLD_SWITCH_HUMID):
                deadline = time.time() + 20 #입김보다 제한시간이 10초 더 길음
                while time.time() < deadline: #LED가 서서히 점멸하여 스위치 전환을 알림
                    increaseLED()
                    result = buttonFlag #버튼 눌렸나 확인
                    buttonFlag = False # 인증 성공 대비 초기화
                    if(result):
                        celebrateAuthLED() #인증성공 축하등
                        break
                    decreaseLED()
                    result = buttonFlag #버튼 눌렸나 확인
                    buttonFlag = False # 인증 성공 대비 초기화
                    if(result):
                        celebrateAuthLED() #인증성공 축하등
                        break
                return result #인증결과 내어주기

        controlLED(led_green, 1) #입김 인증 준비 끝, LED 켬 
        controlLED(led_yellow, 1) #입김 인증 준비 끝, LED 켬 
        deadline = time.time() + 10 #제한시간 10초
        while time.time() < deadline:
            t, h = measure_temp_humi() #현재 온습도 측정결과
            #온도 습도 둘 중 하나만이라도 기준값 이상 변하면 인증성공
            if (t-avrgT)>=THRESHOLD_TEMP and (h-avrgH)>=THRESHOLD_HUMID: 
                   result = True
                   celebrateAuthLED() # 입김 인증 축하등
                   return result
            time.sleep(1) # 1초 잠자기
        controlLED(led_green, 0)
        controlLED(led_yellow, 0)
        return result # 인증 결과 내어주기

#조도
def getLight(): # MCP3202의 CH0에 연결된 조도 센서로부터 조도값 읽기
       return mcp.read_adc(0)

# 초음파 센서를 다루기 위한 전역 변수 선언 및 초기화
trig = 20 # GPIO20
echo = 16 # GPIO16
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(trig, GPIO.OUT) # GPIO20 핀을 출력으로 지정
GPIO.setup(echo, GPIO.IN) # GPIO16 핀을 입력으로 지정

# LED를 다루기 위한 전역 변수 선언 및 초기화
led_yellow = 5
led_green = 6
GPIO.setup(led_green, GPIO.OUT)
GPIO.setup(led_yellow, GPIO.OUT)

#온도
sda = 2 #GPIO2핀. sda 이름이 붙여진 핀
scl = 3 #GPIO3핀. scl 이름이 붙여진 핀

i2c = busio.I2C(scl, sda) # I2C 버스 통신을 실행하는 객체 생성
sensor = HTU21D(i2c) # I2C 버스에서 HTU21D 장치를 제어하는 객체 생성

#조도
mcp = Adafruit_MCP3008.MCP3008(clk=11, cs=8, miso=9, mosi=10)

#스위치
button = 21 #GPIO21 
GPIO.setup(button, GPIO.IN, GPIO.PUD_DOWN) # button 핀을 입력으로 설정
#스위치를 누르면 10ms의 디바운스 후 isButton_pressed가 호출되도록 설정
GPIO.add_event_detect(button, GPIO.RISING, isButton_pressed, bouncetime=10)
buttonFlag = False #버튼이 눌러진 상태, True면 눌러짐 
