#define TRIG 32
#define ECHO 33
#define PIR  27
#define BTN  26
#define CDS  34
#define LED  25

void setup() {
  Serial.begin(115200);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(PIR, INPUT);
  pinMode(BTN, INPUT_PULLUP);
  pinMode(LED, OUTPUT);
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
  float distance = getDistance();
  int pir = digitalRead(PIR);
  int btn = digitalRead(BTN) == LOW ? 1 : 0;
  int light = analogRead(CDS);

  // LED: 버튼 누르면 켜짐
  digitalWrite(LED, btn);

  Serial.print("DIST:");
  Serial.print(distance);
  Serial.print(",PIR:");
  Serial.print(pir);
  Serial.print(",BTN:");
  Serial.print(btn);
  Serial.print(",LIGHT:");
  Serial.println(light);

  delay(500);
}
