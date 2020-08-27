import numpy as np
import time
import cv2
import os
import imutils
import subprocess
import threading
from gtts import gTTS 
from pydub import AudioSegment
AudioSegment.converter = "C:\\Users\\Bhupesh\\Desktop\\pro\\ffmpeg\\bin\\ffmpeg.exe"
AudioSegment.ffmpeg = "C:\\Users\\Bhupesh\\Desktop\\pro\\ffmpeg\\bin\\ffmpeg.exe"
AudioSegment.ffprobe ="C:\\Users\\Bhupesh\\Desktop\\pro\\ffmpeg\\bin\\ffprobe.exe"

LABELS = open("obj.names").read().strip().split("\n")
COLORS = np.random.uniform(0, 255, size=(44, 3))

print("[INFO] loading YOLO from disk...")
net = cv2.dnn.readNetFromDarknet("yolov3-tiny-obj.cfg", "yolov3-tiny-obj_last.weights")

ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]


#Your input video goes here . 1-trim.mp4 is our input file.
cap = cv2.VideoCapture("1-trim.mp4") 
#cap = cv2.VideoCapture(0)


#frame_count = 0
start = time.time()
first = True
frames = []

#Process inputs
winName = 'AI based Traffic Assistant'
cv2.namedWindow(winName, cv2.WINDOW_NORMAL)
cv2.resizeWindow(winName, 1000,1000)

def speed_change(sound, speed):
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
         "frame_rate": int(sound.frame_rate * speed)
      })
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

def subset(text1,prev1):
	for i in range(len(text1)):
		if text1[i] not in prev1:
			return 0
	return 1

def playaudio(texts):
	description = ', '.join(texts)
	tts = gTTS(description, lang='en')
	tts.save('tts.mp3')
	tts = AudioSegment.from_mp3("tts.mp3")
	tts = speed_change(tts, 5.0)
	subprocess.call(["ffplay", "-nodisp", "-autoexit", "tts.mp3"])


#def th():
prev = []
buffer = []
ctr = 1
count=1
while True:
	if cv2.waitKey(25)&0xFF == ord('q'):
		break
	#frame_count += 1
	# Capture frame-by-frameq
	ret, frame = cap.read()
	frames.append(frame)

	if ret:
		key = cv2.waitKey(1)
		if cv2.waitKey(1) < 0:
			end = time.time()
			(H, W) = frame.shape[:2]
			blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),
				swapRB=True, crop=False)
			net.setInput(blob)
			layerOutputs = net.forward(ln)

			boxes = []
			confidences = []
			classIDs = []
			centers = []

			# loop over each of the layer outputs
			for output in layerOutputs:
				# loop over each of the detections
				for detection in output:
					# extract the class ID and confidence (i.e., probability) of
					# the current object detection
					scores = detection[5:]
					classID = np.argmax(scores)
					confidence = scores[classID]

					# filter out weak predictions by ensuring the detected
					# probability is greater than the minimum probability
					if confidence > 0.5:
						# scale the bounding box coordinates back relative to the
						# size of the image, keeping in mind that YOLO actually
						# returns the center (x, y)-coordinates of the bounding
						# box followed by the boxes' width and height
						box = detection[0:4] * np.array([W, H, W, H])
						(centerX, centerY, width, height) = box.astype("int")

						# use the center (x, y)-coordinates to derive the top and
						# and left corner of the bounding box
						x = int(centerX - (width / 2))
						y = int(centerY - (height / 2))

						left, top = x,y
						right = int(centerX + (width / 2))
						bottom = int(centerY + (height / 2))
						# update our list of bounding box coordinates, confidences,
						# and class IDs
						boxes.append([x, y, int(width), int(height)])
						confidences.append(float(confidence))
						classIDs.append(classID)
						centers.append((centerX, centerY))
						color = COLORS[classID]
						cv2.rectangle(frame, (left, top), (right, bottom), color, 3)
						label = '%.2f' % confidence
						if LABELS:
							assert (classID < len(LABELS))
							label = '%s:%s' % (LABELS[classID], label)
						cv2.putText(frame, label, (left,top), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)

			# apply non-maxima suppression to suppress weak, overlapping bounding
			# boxes
			idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.3)

			texts = []
			# ensure at least one detection exists
			if len(idxs) > 0:
				# loop over the indexes we are keeping
				for i in idxs.flatten():
					# find positions
					centerX, centerY = centers[i][0], centers[i][1]
					
					if centerX <= W/3:
						W_pos = "left "
					elif centerX <= (W/3 * 2):
						W_pos = "center "
					else:
						W_pos = "right "
					
					if centerY <= H/3:
						H_pos = "top "
					elif centerY <= (H/3 * 2):
						H_pos = "mid "
					else:
						H_pos = "bottom "

					#texts.append(H_pos + W_pos + LABELS[classIDs[i]])
					texts.append(LABELS[classIDs[i]])
			

			texts.sort()
			prev.sort()
			texts = list(set(texts))
			print(texts)
			if count == 1:
				count -= 1
			else:
				cv2.imshow(winName, frame)
				if texts != prev and len(texts) > 0:
					if subset(texts,buffer) == 0:				
						if texts:
							t1 = threading.Thread(target=playaudio,args=(texts,), daemon=True,name='t1') 
							t1.start()
							#time.sleep(2)

							"""
							description = ', '.join(texts)
							tts = gTTS(description, lang='en')
							tts.save('tts.mp3')
							tts = AudioSegment.from_mp3("tts.mp3")
							subprocess.call(["ffplay", "-nodisp", "-autoexit", "tts.mp3"])
						"""
			prev = texts
			buffer.extend(texts)
			ctr += 1
			if ctr % 20 == 0:
				buffer.clear()

'''
t = threading.Thread(target=th,daemon=True, name='t') 
t.start()
'''


cap.release()
cv2.destroyAllWindows()
os.remove("tts.mp3")