#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Wire.h>
#include <EEPROM.h>

// --- EEPROM Layout ---
// Byte 0-1: uint16_t sample count
// Byte 2+:  24 bytes per sample (6 x float)
#define EEPROM_COUNT_ADDR 0
#define EEPROM_DATA_START 2
#define BYTES_PER_SAMPLE  24
#define MAX_SAMPLES       ((EEPROM.length() - EEPROM_DATA_START) / BYTES_PER_SAMPLE)

Adafruit_MPU6050 mpu;

unsigned long lastSensor = 0;
uint16_t sampleCount = 0;
bool storageFull = false;

// ---- EEPROM helpers ----

void eepromWriteFloat(int addr, float val) {
  byte* p = (byte*)&val;
  for (int i = 0; i < 4; i++) EEPROM.update(addr + i, p[i]);
}

float eepromReadFloat(int addr) {
  float val;
  byte* p = (byte*)&val;
  for (int i = 0; i < 4; i++) p[i] = EEPROM.read(addr + i);
  return val;
}

void saveSample(float ax, float ay, float az, float gx, float gy, float gz) {
  if (storageFull) return;

  int addr = EEPROM_DATA_START + sampleCount * BYTES_PER_SAMPLE;
  eepromWriteFloat(addr + 0,  ax);
  eepromWriteFloat(addr + 4,  ay);
  eepromWriteFloat(addr + 8,  az);
  eepromWriteFloat(addr + 12, gx);
  eepromWriteFloat(addr + 16, gy);
  eepromWriteFloat(addr + 20, gz);

  sampleCount++;
  EEPROM.update(EEPROM_COUNT_ADDR,     lowByte(sampleCount));
  EEPROM.update(EEPROM_COUNT_ADDR + 1, highByte(sampleCount));

  if (sampleCount >= MAX_SAMPLES) {
    storageFull = true;
    Serial.println(">>> EEPROM FULL - recording stopped <<<");
  }
}

void dumpEEPROM() {
  uint16_t count;
  count  = EEPROM.read(EEPROM_COUNT_ADDR);
  count |= (uint16_t)EEPROM.read(EEPROM_COUNT_ADDR + 1) << 8;

  Serial.println("=== EEPROM DUMP START ===");
  Serial.print("Samples stored: ");
  Serial.println(count);
  Serial.println("ax,ay,az,gx,gy,gz");

  for (uint16_t i = 0; i < count; i++) {
    int addr = EEPROM_DATA_START + i * BYTES_PER_SAMPLE;
    Serial.print(eepromReadFloat(addr + 0),  4); Serial.print(",");
    Serial.print(eepromReadFloat(addr + 4),  4); Serial.print(",");
    Serial.print(eepromReadFloat(addr + 8),  4); Serial.print(",");
    Serial.print(eepromReadFloat(addr + 12), 4); Serial.print(",");
    Serial.print(eepromReadFloat(addr + 16), 4); Serial.print(",");
    Serial.println(eepromReadFloat(addr + 20), 4);
  }
  Serial.println("=== EEPROM DUMP END ===");
}

void clearEEPROM() {
  EEPROM.update(EEPROM_COUNT_ADDR,     0);
  EEPROM.update(EEPROM_COUNT_ADDR + 1, 0);
  sampleCount = 0;
  storageFull = false;
  Serial.println("EEPROM cleared.");
}

// ---- Setup / Loop ----

void setup(void) {
  Serial.begin(115200);

  if (!mpu.begin()) {
    Serial.println("Failed to find MPU6050 chip");
    while (1) {}
  }
  Serial.println("MPU6050 Found!");
  getRanges();

  sampleCount  = EEPROM.read(EEPROM_COUNT_ADDR);
  sampleCount |= (uint16_t)EEPROM.read(EEPROM_COUNT_ADDR + 1) << 8;
  if (sampleCount >= MAX_SAMPLES) storageFull = true;

  Serial.print("MAX_SAMPLES: "); Serial.println(MAX_SAMPLES);
  Serial.print("Resuming from sample #"); Serial.println(sampleCount);
  Serial.println("Send 'd' to dump, 'c' to clear.");
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();
    if (cmd == 'd') dumpEEPROM();
    if (cmd == 'c') clearEEPROM();
  }

  unsigned long now = millis();
  if (now - lastSensor >= 200) {
    lastSensor = now;

    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);

    saveSample(
      a.acceleration.x, a.acceleration.y, a.acceleration.z,
      g.gyro.x,         g.gyro.y,         g.gyro.z
    );

    Serial.print(a.acceleration.x); Serial.print(",");
    Serial.print(a.acceleration.y); Serial.print(",");
    Serial.print(a.acceleration.z); Serial.print(",");
    Serial.print(g.gyro.x);         Serial.print(",");
    Serial.print(g.gyro.y);         Serial.print(",");
    Serial.println(g.gyro.z);
  }
}

void getRanges() {
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
}