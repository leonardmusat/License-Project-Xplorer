#include <WiFi.h>

#define sound_speed 0.034f

// Replace these with your network credentials
const char* ssid = "DIGI-AG";
const char* password = "12345678";

// Server IP and port (replace with your server's local IP and UDP port)
const char* serverIP = "192.168.100.37";
const int serverPort = 8889;

WiFiClient client;

int motor1Pin1 = 27; 
int motor1Pin2 = 26; 
int enable1Pin = 25; 
int motor2Pin1 = 4; 
int motor2Pin2 = 5; 
int enable2Pin = 32; 
int motor3Pin1 = 17; 
int motor3Pin2 = 18; 
int enable3Pin = 33; 
int motor4Pin1 = 21; 
int motor4Pin2 = 22; 
int enable4Pin = 23; 

int trigPin = 12;
int echoPin = 13;
int trigPin_left = 19;
int echoPin_left = 2;

long duration;
float distanceCm;
float distanceCm_left;

void verify_distance(float *dist, long *duration, int trigPin, int echoPin);

void setup() {
  // Start the serial monitor
  Serial.begin(115200);
  delay(10);

  // Connect to Wi-Fi
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("WiFi connected.");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  if (client.connect(serverIP, serverPort)) {
    Serial.println("Connected to the server");
  }
  else {
    Serial.println("Connection to server failed");
}

  pinMode(motor1Pin1, OUTPUT);
  pinMode(motor1Pin2, OUTPUT);
  pinMode(enable1Pin, OUTPUT);

  pinMode(motor2Pin1, OUTPUT);
  pinMode(motor2Pin2, OUTPUT);
  pinMode(enable2Pin, OUTPUT);

  pinMode(motor3Pin1, OUTPUT);
  pinMode(motor3Pin2, OUTPUT);
  pinMode(enable3Pin, OUTPUT);

  pinMode(motor4Pin1, OUTPUT);
  pinMode(motor4Pin2, OUTPUT);
  pinMode(enable4Pin, OUTPUT);

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  pinMode(trigPin_left, OUTPUT);
  pinMode(echoPin_left, INPUT);
}

void loop(){
  while (true){
      if (client.connected()) {
    // Check if the client is connected
        if (client.available()) {
          // Read the binary string from the server
          String response = client.readStringUntil('\n');
          Serial.print("Received from server: ");
          Serial.println(response);

          // Convert the binary string to an integer
          int command = strtol(response.c_str(), nullptr, 2);

          if (response.charAt(response.length() - 1) == '1'){
            verify_distance(&distanceCm, &duration, trigPin, echoPin);
            if (distanceCm < 10){
              command = command - 1;
            }
          }
          else if(response.charAt(1) == '1'){
            verify_distance(&distanceCm_left, &duration, trigPin_left, echoPin_left);
            if (distanceCm_left < 10){
              Serial.println(distanceCm);
               Serial.println(distanceCm_left);
              command = command - 4;
            }
          }

          // Now you can use `command` as an integer with binary bits
          Serial.print("Converted command: ");
          Serial.println(command, BIN);  // Print it in binary form to verify

          switch (command) {
              case 0b1000:
              //move forward
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, LOW);
                digitalWrite(motor1Pin2, HIGH);
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, LOW);
                digitalWrite(motor2Pin2, HIGH);
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, LOW);
                digitalWrite(motor3Pin2, HIGH);
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, LOW);
                digitalWrite(motor4Pin2, HIGH);
                break;
              case 0b0100:
              // move left
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, HIGH);
                digitalWrite(motor1Pin2, LOW);
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, LOW);
                digitalWrite(motor2Pin2, HIGH);
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, HIGH);
                digitalWrite(motor3Pin2, LOW);
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, LOW);
                digitalWrite(motor4Pin2, HIGH);               
                break;
              case 0b0010:
              //MOVE BACKWARDS
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, HIGH);
                digitalWrite(motor1Pin2, LOW);
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, HIGH);
                digitalWrite(motor2Pin2, LOW);
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, HIGH);
                digitalWrite(motor3Pin2, LOW);
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, HIGH);
                digitalWrite(motor4Pin2, LOW); 
                break;
              case 0b0001:
                //MOVE RIGHT
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, LOW);
                digitalWrite(motor1Pin2, HIGH);
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, HIGH);
                digitalWrite(motor2Pin2, LOW);
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, LOW);
                digitalWrite(motor3Pin2, HIGH);
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, HIGH);
                digitalWrite(motor4Pin2, LOW); 
                break;
              case 0b1010:
                //turn around 
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, LOW);
                digitalWrite(motor1Pin2, HIGH);
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, HIGH);
                digitalWrite(motor2Pin2, LOW);
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, HIGH);
                digitalWrite(motor3Pin2, LOW);
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, LOW);
                digitalWrite(motor4Pin2, HIGH);
                break;
              case 0b0101:
                //turn around
                digitalWrite(enable1Pin, LOW);
                digitalWrite(motor1Pin1, HIGH);
                digitalWrite(motor1Pin2, LOW);
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, LOW);
                digitalWrite(motor2Pin2, HIGH);
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, LOW);
                digitalWrite(motor3Pin2, HIGH);
                digitalWrite(enable4Pin, LOW);
                digitalWrite(motor4Pin1, HIGH);
                digitalWrite(motor4Pin2, LOW);
              case 0b1001:
                //FORWARD-RIGHT
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, LOW);
                digitalWrite(motor1Pin2, HIGH);
                digitalWrite(enable2Pin, LOW);
                digitalWrite(motor2Pin1, LOW); //TO BE DELETED 
                digitalWrite(motor2Pin2, HIGH); //TO BE DELETED
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, LOW);
                digitalWrite(motor3Pin2, HIGH);
                digitalWrite(enable4Pin, LOW); 
                digitalWrite(motor4Pin1, LOW);  //TO BE DELETED
                digitalWrite(motor4Pin2, HIGH);  //TO BE DELETED
                break;
              case 0b0110:
                //BACKWARD LEFT
                digitalWrite(enable1Pin, HIGH);
                digitalWrite(motor1Pin1, HIGH);
                digitalWrite(motor1Pin2, LOW);
                digitalWrite(enable2Pin, LOW);
                digitalWrite(motor2Pin1, HIGH); //TO BE DELETED
                digitalWrite(motor2Pin2, LOW); //TO BE DELETED
                digitalWrite(enable3Pin, HIGH);
                digitalWrite(motor3Pin1, HIGH);
                digitalWrite(motor3Pin2, LOW); 
                digitalWrite(enable4Pin, LOW);
                digitalWrite(motor4Pin1, HIGH); //TO BE DELETED
                digitalWrite(motor4Pin2, LOW); //TO BE DELETED
                break;
              case 0b1100:
                //forward left
                digitalWrite(enable1Pin, LOW);
                digitalWrite(motor1Pin1, LOW); //TO BE DELETED
                digitalWrite(motor1Pin2, HIGH); //TO BE DELETED
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, LOW);
                digitalWrite(motor2Pin2, HIGH);
                digitalWrite(enable3Pin, LOW);
                digitalWrite(motor3Pin1, LOW); //TO BE DELETED
                digitalWrite(motor3Pin2, HIGH); //TO BE DELETED
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, LOW); 
                digitalWrite(motor4Pin2, HIGH);              
                break;
              case 0b0011:
                //BACKWARDS RIGHT
                digitalWrite(enable1Pin, LOW); 
                digitalWrite(motor1Pin1, HIGH); //TO BE DELETED
                digitalWrite(motor1Pin2, LOW); //TO BE DELETED
                digitalWrite(enable2Pin, HIGH);
                digitalWrite(motor2Pin1, HIGH);
                digitalWrite(motor2Pin2, LOW);
                digitalWrite(enable3Pin, LOW);
                digitalWrite(motor3Pin1, HIGH);
                digitalWrite(motor3Pin2, LOW);
                digitalWrite(enable4Pin, HIGH);
                digitalWrite(motor4Pin1, HIGH); //TO BE DELETED
                digitalWrite(motor4Pin2, LOW); //TO BE DELETED
                break;
              case 0b1111:
                Serial.println("Emergency Stop or Special Behavior");
                break;
              default:
                  digitalWrite(enable1Pin, LOW);
                  digitalWrite(enable2Pin, LOW);
                  digitalWrite(enable3Pin, LOW);
                  digitalWrite(enable4Pin, LOW);
                break;
          }
        }

    }
    else {
        // Try to reconnect if the connection was lost
        Serial.println("Disconnected from server, trying to reconnect...");
        if (client.connect(serverIP, serverPort)) {
          Serial.println("Reconnected to the server");
        } else {
          delay(5000); // Wait a bit before trying to reconnect again
        }
      }
      delay(100);  // Small delay to avoid excessive checking
}
}

void verify_distance(float *dist, long *duration, int trigPin, int echoPin){
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  *duration = pulseIn(echoPin, HIGH);
  *dist = (*duration) * sound_speed/2.0;
}