import time
import RPi.GPIO as GPIO
from adafruit_htu21d import HTU21D
import busio
import Adafruit_MCP3008

# LED를 켜고 끄는 함수
def controlLED(led, on_off): # led 번호의 핀에 on_off(0/1) 값 출력하는 함수
        if (on_off):
                print("on") 
        else:
                print("off")
        GPIO.output(led, on_off)
	
def increaseLED():
        pwm_green = GPIO.PWM(led_green, 100)
        pwm_yellow = GPIO.PWM(led_yellow, 100)
        pwm_green.start(0) 
        pwm_yellow.start(0) 
        for value in range(0, 100):
                if(buttonFlag):
                        break
                pwm_green.ChangeDutyCycle(value) 
                pwm_yellow.ChangeDutyCycle(value) 
                time.sleep(0.01)
        pwm_green.stop()
        pwm_yellow.stop() 
        

def decreaseLED():
        pwm_green = GPIO.PWM(led_green, 100)
        pwm_yellow = GPIO.PWM(led_yellow, 100)
        pwm_green.start(100) 
        pwm_yellow.start(100) 
        for value in range(99, -1, -1):
                if(buttonFlag):
                        break
                pwm_green.ChangeDutyCycle(value) 
                pwm_yellow.ChangeDutyCycle(value) 
                time.sleep(0.01)
        pwm_green.stop()
        pwm_yellow.stop() 
        
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
        print(float(sensor.temperature), float(sensor.relative_humidity))
        return float(sensor.temperature), float(sensor.relative_humidity)

def auth_temp_humi():
        global buttonFlag
        gapT = 1
        gapH = 7
        hotT = 29
        humidH = 55
        result = False
        base_temp, base_humi = [], []
        end_time = time.time() + 2
        while time.time() < end_time:
            time.sleep(1)
            t, h = measure_temp_humi()
            base_temp.append(t)
            base_humi.append(h)

        avrgT = sum(base_temp) / len(base_temp)
        avrgH = sum(base_humi) / len(base_humi)

        if(avrgT > hotT or avrgH  > humidH):
                deadline = time.time() + 20
                while time.time() < deadline:
                    increaseLED()
                    result = buttonFlag
                    buttonFlag = False
                    if(result):
                        celebrateAuthLED()
                        break
                    decreaseLED()
                    result = buttonFlag
                    buttonFlag = False
                    if(result):
                        celebrateAuthLED()
                        break
                return result

        controlLED(led_green, 1) #인증 준비 끝, 학생에게 알린다
        controlLED(led_yellow, 1) #인증 준비 끝, 학생에게 알린다
        deadline = time.time() + 10
        while time.time() < deadline:
            t, h = measure_temp_humi()
            if (t-avrgT)>=gapT and (h-avrgH)>=gapH:
                   result = True
                   celebrateAuthLED()
                   return result
        controlLED(led_green, 0)
        controlLED(led_yellow, 0)
        return result

#조도
def getLight():
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
sda = 2
scl = 3

i2c = busio.I2C(scl, sda)
sensor = HTU21D(i2c)

#조도
mcp = Adafruit_MCP3008.MCP3008(clk=11, cs=8, miso=9, mosi=10)

#스위치
button = 21
GPIO.setup(button, GPIO.IN, GPIO.PUD_DOWN)
GPIO.add_event_detect(button, GPIO.RISING, isButton_pressed, bouncetime=10)
buttonFlag = False 
