#define TRIG 32
#define ECHO 33
#define PIR  27
#define BTN  26
#define CDS  34
#define LED  25

bool ledAuth = false;
volatile bool btnPressed = false;
volatile unsigned long lastBtnTime = 0;
unsigned long lastSend = 0;

void IRAM_ATTR handleBtn() {
  unsigned long now = millis();
  if (now - lastBtnTime > 50) {
    btnPressed = true;
    lastBtnTime = now;
  }
}

void setup() {
  Serial.begin(115200);
  Serial.setTimeout(10);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(PIR, INPUT);
  pinMode(BTN, INPUT_PULLUP);
  pinMode(LED, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(BTN), handleBtn, FALLING);
}

float getDistance() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duration = pulseIn(ECHO, HIGH, 30000);
  return duration * 0.034 / 2;
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "LED:ON") ledAuth = true;
    else if (cmd == "LED:OFF") ledAuth = false;
  }

  // 버튼 인터럽트 감지 시 축하 블링크 후 LED 끔
  if (ledAuth) {
    if (btnPressed) {
      ledAuth = false;
      for (int i = 0; i < 6; i++) {
        digitalWrite(LED, HIGH);
        delay(80);
        digitalWrite(LED, LOW);
        delay(80);
      }
    } else {
      digitalWrite(LED, HIGH);
    }
  } else {
    digitalWrite(LED, LOW);
  }

  // 500ms마다 센서 데이터 전송
  if (millis() - lastSend >= 500) {
    lastSend = millis();
    float distance = getDistance();
    int pir = digitalRead(PIR);
    int btn = btnPressed ? 1 : 0;
    int light = analogRead(CDS);
    btnPressed = false;

    Serial.print("DIST:"); Serial.print(distance);
    Serial.print(",PIR:"); Serial.print(pir);
    Serial.print(",BTN:"); Serial.print(btn);
    Serial.print(",LIGHT:"); Serial.println(light);
  }
}
