#define LEFT 10
#define RIGHT 12

void setup() {
  // put your setup code here, to run once:
  pinMode(LEFT, OUTPUT);
  pinMode(RIGHT, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(LEFT, HIGH);
}
