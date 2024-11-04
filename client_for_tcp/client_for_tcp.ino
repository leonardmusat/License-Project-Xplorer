#include <WiFi.h>
#include "esp_camera.h"

// Replace with your WiFi credentials
const char* ssid = "DIGI-AG";
const char* password = "12345678";

// Server IP and port (replace with your server's IP and port)
const char* serverIP = "192.168.100.40";  // Replace with your server's IP
const int serverPort = 8888;

// Create a TCP client object
WiFiClient client;

// Camera setup (ESP32-CAM pin configuration)
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27

#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM      5

#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");

  // Initialize the camera
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;


  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA;  // Adjust frame size if needed
    config.jpeg_quality = 35;           // Lower value for higher quality
    config.fb_count = 2;                // Double buffer if PSRAM is available
  } else {
    config.frame_size = FRAMESIZE_QQVGA;
    config.jpeg_quality = 14;           // Higher value for lower quality
    config.fb_count = 1;
  }

  // Camera init
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }

  // Attempt to connect to the server via TCP
  if (client.connect(serverIP, serverPort)) {
    Serial.println("Connected to server!");
  } else {
    Serial.println("Connection to server failed!");
  }
}

void loop() {
  if (!client.connected()) {
    Serial.println("Disconnected from server, trying to reconnect...");
    if (client.connect(serverIP, serverPort)) {
      Serial.println("Reconnected to server!");
    } else {
      Serial.println("Reconnection failed!");
      delay(5000);  // Wait before retrying
      return;
    }
  }

  // Capture a frame
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  // Send the frame size first (4 bytes)
  uint32_t frameSize = fb->len;
  client.write((uint8_t*)&frameSize, sizeof(frameSize));

  // Send the actual frame data
  client.write(fb->buf, fb->len);
  client.flush(); 
  Serial.printf("Frame sent, size: %d bytes\n", fb->len);

  // Return the frame buffer back to the camera driver
  esp_camera_fb_return(fb);

  delay(350);  // Adjust delay based on frame rate needs
}
