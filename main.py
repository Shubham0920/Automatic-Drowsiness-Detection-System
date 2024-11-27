import threading
from scipy.spatial import distance
from imutils import face_utils
# from playsound import playsound
from pygame import mixer
import time
import RPi.GPIO as GPIO
import imutils
import dlib
import paho.mqtt.client as mqtt
import cv2
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import base64
from datetime import datetime

global mqtt_msg
cred = credentials.Certificate("/home/test/Group9/account.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
import paho.mqtt.client as mqtt
mqtt_msg = ""
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code " + str(rc))
    # Subscribe to MQTT topic
    client.subscribe("sensor/reading")

def on_message(client, userdata, msg):
	global mqtt_msg
	mqtt_msg = msg
	print("Received message: " + msg.payload.decode())

# Configure MQTT Broker
broker_address = "192.168.119.167"
broker_port = 1883

# Initialize MQTT Client
client = mqtt.Client("RaspberryPi")
client.on_connect = on_connect
client.on_message = on_message


# Connect to MQTT Broker
client.connect(broker_address, broker_port, 60)

def store_data(data):
	_, buffer = cv2.imencode('.png', data["frame"])
	print("-======")
	image_base64 = base64.b64encode(buffer).decode('utf-8')
	timestamp = datetime.now()
	print(type(data["mqtt_msg"].payload.decode()))
	msg = str(data["mqtt_msg"].payload.decode())
	msg = list(msg.split(','))
	print(msg)
	data = {
		'image': image_base64,
		'timestamp': timestamp,
		'heatIndex' : msg[0],
		'mq3':msg[1],
		'mq7':msg[2],
		'mq135':msg[3]
		
	}
	db.collection('images').add(data)
    

buzzerOn = False
def buzzer():
    buzzerOn = True
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(2, GPIO.OUT)
    number = 0.001
    timer = 200
    while timer != 0:
            GPIO.output(2, True)
            time.sleep(number)
            GPIO.output(2, False)
            time.sleep(number)
            timer = timer - 1
    buzzerOn = False





# Your other code in main.py goes here

# Call the function to run the MQTT broker



def eye_aspect_ratio(eye):
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	ear = (A + B) / (2.0 * C)
	return ear
	
thresh = 0.25
frame_check = 5
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("/home/test/Group9/shape_predictor_68_face_landmarks (1).dat") # Dat file is the crux of the code

(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
cap=cv2.VideoCapture(-1)
flag=0
mqtt_thread = threading.Thread(target = client.loop_forever)
mqtt_thread.start()
#mqtt_thread.join()
print("thread")
while True:
	ret, frame=cap.read()
	frame = imutils.resize(frame, width=450)
	gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
	subjects = detect(gray, 0)
	for subject in subjects:
		shape = predict(gray, subject)
		shape = face_utils.shape_to_np(shape)#converting to NumPy Array
		leftEye = shape[lStart:lEnd]
		rightEye = shape[rStart:rEnd]
		leftEAR = eye_aspect_ratio(leftEye)
		rightEAR = eye_aspect_ratio(rightEye)
		ear = (leftEAR + rightEAR) / 2.0
		leftEyeHull = cv2.convexHull(leftEye)
		rightEyeHull = cv2.convexHull(rightEye)
		#cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
		#cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
		#if flag < frame_check:
			#buzzer.off()
		if ear < thresh:
			flag += 1
			print (flag, end = ">")
			print (frame_check)
			if flag >= frame_check:
				# playsound("alarm.wav")
				# sound.play()
				cv2.putText(frame, "****************ALERT!****************", (10, 30),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
				cv2.putText(frame, "****************ALERT!****************", (10,325),
					cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
				print ("Drowsy")
				print(mqtt_msg)
				data = {
				"frame" : frame,
				"mqtt_msg" :mqtt_msg
				}
				thread = threading.Thread(target=store_data, args=(data,))
				thread.start()
				if(buzzerOn == False):
					buzzer()
		else:
			flag = 0
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	if key == ord("q"):
		break
cv2.destroyAllWindows()
cap.release() 
mqtt_thread.stop()

