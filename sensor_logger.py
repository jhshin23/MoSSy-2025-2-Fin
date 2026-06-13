import serial
import csv
import time
from datetime import datetime

PORT = '/dev/ttyACM0'
BAUDRATE = 115200
LOG_FILE = '/home/pi/sensor_log.csv'

s = serial.Serial(PORT, BAUDRATE, timeout=1)
time.sleep(2)

with open(LOG_FILE, 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'distance', 'pir', 'button', 'light'])
    print(f"로깅 시작: {LOG_FILE}")

    while True:
        line = s.readline().decode(errors='ignore').strip()
        if not line or not line.startswith('DIST:'):
            continue

        try:
            parts = {}
            for item in line.split(','):
                k, v = item.split(':')
                parts[k] = v

            row = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                parts['DIST'],
                parts['PIR'],
                parts['BTN'],
                parts['LIGHT']
            ]
            writer.writerow(row)
            f.flush()
            print(row)
        except Exception as e:
            print(f"파싱 오류: {e}")
