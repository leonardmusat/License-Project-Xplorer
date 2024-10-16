#include <WiFi.h>
#include <WiFiUdp.h>
#include "esp_camera.h"

// Replace with your WiFi credentials
const char* ssid = "DIGI-AG";
const char* password = "12345678";

// Server IP and port (replace with your server's local IP and UDP port)
const char* serverIP = "192.168.100.40";
const int serverPort = 8888;
const int CHUNK_LENGTH = 1024; // Set your chunk size

// Create a UDP object
WiFiUDP udp;

// Frame buffer and settings
camera_fb_t* fb = NULL;
boolean connected = false;

// ESP32-CAM pin definitions
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

void sendPacketData(const char* buf, uint16_t len, uint16_t chunkLength);

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  connected = true;

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
  
  // Init with high specs to make sure you get the best streaming quality
  if (psramFound()) {
    config.frame_size = FRAMESIZE_QVGA; // Try FRAMESIZE_QVGA (320x240) to start
    config.jpeg_quality = 10;          // Lower quality for smaller size
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_QQVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }

  // Camera init
  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed");
    return;
  }

  // Begin UDP connection
  udp.begin(serverPort);
  Serial.println("UDP Client started");
}

void loop() {
  // Only send data when connected
  if (connected) {
    camera_fb_t* fb = NULL;
    esp_err_t res = ESP_OK;
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed");
      esp_camera_fb_return(fb);
      return;
    }

    if (fb->format != PIXFORMAT_JPEG) {
      Serial.println("PIXFORMAT_JPEG not implemented");
      esp_camera_fb_return(fb);
      return;
    }

    // Send frame data in chunks
    sendPacketData((const char*)fb->buf, fb->len, CHUNK_LENGTH);

    // Return the frame buffer
    esp_camera_fb_return(fb);
  }
}

void sendPacketData(const char* buf, uint16_t len, uint16_t chunkLength) {
  uint8_t buffer[chunkLength];
  size_t blen = sizeof(buffer);
  size_t rest = len % blen;

  // Send chunks of the frame
  for (size_t i = 0; i < len / blen; ++i) {
    memcpy(buffer, buf + (i * blen), blen);
    udp.beginPacket(serverIP, serverPort); // Use serverIP and serverPort
    udp.write(buffer, chunkLength);
    udp.endPacket();
  }

  // Send the remaining part of the frame
  if (rest) {
    memcpy(buffer, buf + (len - rest), rest);
    udp.beginPacket(serverIP, serverPort); // Use serverIP and serverPort
    udp.write(buffer, rest);
    udp.endPacket();
  }
}
