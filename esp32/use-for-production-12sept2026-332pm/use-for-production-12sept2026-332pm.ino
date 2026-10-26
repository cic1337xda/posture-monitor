/**
 * ==============================================================================
 * ENTERPRISE POSTURE MONITORING - WEARABLE CLIENT (ESP32-C3)
 * Description: Establishes a connection to the external MQTT broker via custom
 *              port 1888. Bypasses Cloudflare proxy via DNS-only subdomain. 
 *              Handles incoming telemetry payloads to trigger haptic feedback.
 * ==============================================================================
 */

#include <WiFi.h>
#include <WiFiManager.h> 
#include <PubSubClient.h>

// --- HARDWARE CONFIGURATION ---
// GPIO pin designated for the vibration motor module
// Configured to 8 to synchronize with the built-in LED
const int MOTOR_PIN = 8; 

// --- NETWORK & MQTT CONFIGURATION ---
WiFiClient espClient;
PubSubClient mqttClient(espClient);

// Default configuration for the broker (Override via WiFiManager Captive Portal)
char mqtt_server[60] = "YOUR_MQTT_BROKER_IP"; 
char mqtt_port[6] = "1888"; 
String macAddress;
String commandTopic;

// --- VIBRATION STATE MACHINE ---
bool isVibrating = false;
unsigned long previousMillis = 0;
const long pulseInterval = 400; // Duty cycle for the haptic pulse
int motorState = LOW;

/**
 * Callback function triggered upon receiving a payload from the subscribed topic.
 * Evaluates the payload string to determine the haptic feedback state.
 */
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String message = "";
  for (unsigned int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  Serial.print("[MQTT] Payload received: ");
  Serial.println(message);

  if (message == "vibrate_heavy") {
    isVibrating = true;
  } 
  else if (message == "stop" || message == "linked") {
    isVibrating = false;
    digitalWrite(MOTOR_PIN, LOW); // Terminate haptic loop immediately
    
    // Execute a brief acknowledgment pulse for successful pairing integration
    if (message == "linked") {
      digitalWrite(MOTOR_PIN, HIGH);
      delay(300);
      digitalWrite(MOTOR_PIN, LOW);
    }
  }
}

/**
 * Handles reconnections to the MQTT broker in the event of connection loss.
 * Implements a backoff strategy to prevent network flooding.
 */
void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Establishing connection to ");
    Serial.print(mqtt_server);
    Serial.print(":");
    Serial.print(mqtt_port);
    Serial.print("... ");
    
    // Generate a unique client identifier derived from the hardware MAC address
    String clientId = "Wearable-";
    clientId += macAddress;
    
    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("CONNECTED.");
      mqttClient.subscribe(commandTopic.c_str());
      Serial.print("[MQTT] Subscribed to topic: ");
      Serial.println(commandTopic);
    } else {
      Serial.print("FAILED, status code = ");
      Serial.print(mqttClient.state());
      Serial.println(". Retrying connection in 5 seconds...");
      delay(5000);
    }
  }
}

void setup() {
  // --- IMMEDIATE HARDWARE OVERRIDE ---
  // Force the designated pin to LOW instantly at boot-up sequence
  pinMode(MOTOR_PIN, OUTPUT);
  digitalWrite(MOTOR_PIN, LOW);

  Serial.begin(115200);
  Serial.println("\n[SYSTEM] Initializing Wearable Client Architecture...");

  // --- HARDWARE FLAW WORKAROUNDS (POWER & RF STABILITY) ---
  
  // 1. Matikan radio Bluetooth sepenuhnya untuk jimat arus puncak dan elak gangguan RF
  btStop(); 

  // 2. Bangunkan radio WiFi dalam mod Station
  WiFi.mode(WIFI_STA); 
  delay(100); 
  
  // 3. Hadkan kuasa pemancar (TX Power) kepada 8.5dBm untuk elak pengawal voltan terbeban
  WiFi.setTxPower(WIFI_POWER_8_5dBm); 
  
  // --------------------------------------------------------

  // Retrieve hardware MAC Address to construct the localized MQTT Topic
  macAddress = WiFi.macAddress();
  macAddress.toUpperCase(); 
  commandTopic = "posture/wearable/" + macAddress + "/command";
  
  // --- WIFIMANAGER CAPTIVE PORTAL DEPLOYMENT ---
  WiFiManager wm;
  
  // Define strict connection timeout rules
  wm.setConnectTimeout(10); // Attempt to connect to saved WiFi for max 10 seconds
  wm.setConfigPortalTimeout(180); // Keep Captive Portal open for max 3 minutes to preserve battery
  
  // Dynamic HTML parameter to inject the external Server Domain/IP
  WiFiManagerParameter custom_mqtt_server("server", "MQTT Server", mqtt_server, 60);
  wm.addParameter(&custom_mqtt_server);

  // Configure Access Point SSID utilizing the last segment of the MAC address
  String apName = "Posture_Watch_" + macAddress.substring(12, 17);
  
  Serial.println("[NETWORK] Deploying Captive Portal...");
  Serial.print("[INFO] Target MAC Address for Web UI configuration: ");
  Serial.println(macAddress);

  // Halt execution thread until network connection is established
  if (!wm.autoConnect(apName.c_str())) {
    Serial.println("[NETWORK] Connection timeout or failure. Restarting hardware to refresh portal...");
    ESP.restart(); 
  }

  // Persist the updated server domain if modified via the Captive Portal UI
  strcpy(mqtt_server, custom_mqtt_server.getValue());
  
  Serial.println("\n[NETWORK] Connection Established Successfully.");
  Serial.print("[NETWORK] Assigned IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("[NETWORK] Configured Broker: ");
  Serial.println(mqtt_server);

  // Initialize MQTT parameters with the custom port configuration
  mqttClient.setServer(mqtt_server, atoi(mqtt_port));
  mqttClient.setCallback(mqttCallback);
}

void loop() {
  // Maintain MQTT session integrity and process incoming packets
  if (!mqttClient.connected()) {
    reconnectMQTT();
  }
  mqttClient.loop();

  // Execute Non-Blocking Haptic Vibration Pulse
  if (isVibrating) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= pulseInterval) {
      previousMillis = currentMillis;
      motorState = (motorState == LOW) ? HIGH : LOW;
      digitalWrite(MOTOR_PIN, motorState);
    }
  } else {
    digitalWrite(MOTOR_PIN, LOW);
  }
}