#include <WiFi.h>
#include <ESP32Servo.h>
#include <WebServer.h>

const char* ssid = "iPhone Danen"; // Ganti dengan SSID WiFi Anda
const char* password = "danenganteng"; // Ganti dengan password WiFi Anda

WebServer server(80);

Servo myServo;
int servoPin = 4; // Pin GPIO yang terhubung ke servo

void setup() {
  Serial.begin(115200);
  myServo.attach(servoPin);
  myServo.write(0); // Posisikan servo di 0 derajat pada awalnya

  // Menghubungkan ke WiFi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");

  // Tunggu sampai terhubung
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }

  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Menyiapkan server
  server.on("/move_servo", []() {
    myServo.write(95);
    delay(5000); // Berhenti selama 5 detik
    myServo.write(0);
    server.send(200, "text/plain", "Servo moved");
  });

  server.begin();
  Serial.println("Server started");
}

void loop() {
  server.handleClient();
}
