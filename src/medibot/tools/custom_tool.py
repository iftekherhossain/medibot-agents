from crewai_tools import BaseTool
import cv2
from openai import OpenAI
import base64
import time
from ultralytics import YOLO
import math
from typing import List

##calender API Imports
import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
##
import cv2
import time 
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
##
import pyttsx3
import speech_recognition as sr
##for tremor
import mediapipe as mp
import statistics
class HumanTool(BaseTool):
    name: str = "Human interact"
    description: str = (
        "Ask the user questions to gather information."
    )

    def _run(self, argument: str) -> str:
        print("########")
        res = input(f"{argument} \n")
        return res

class SpeakingTool(BaseTool):
    name: str = "Text to Speach"
    description: str = (
        "Speak what is written to the patient"
    )

    def _run(self, argument: str):
        engine = pyttsx3.init()
        # engine._driver._proxy = engine._driver._proxy
        engine.setProperty('rate', 150)  # Adjust speech speed
        engine.setProperty('volume', 0.9)  # Set volume (0.0 to 1.0)
        engine.say(argument)
        engine.runAndWait()
        engine.stop()
        # return res

class TremorCheck(BaseTool):
    name: str = "Check Tremor"
    description: str = (
        "capture videos for 10 seconds and save it and analyze the video for tremor analysis"
    )
    def has_tremor(self):
        self.record_video()
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles
        mp_hands = mp.solutions.hands
        x_list = []
        cap = cv2.VideoCapture("output.avi")
        with mp_hands.Hands(model_complexity=0,max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    print("Ignoring empty camera frame.")
                    break

                # To improve performance, optionally mark the image as not writeable to
                # pass by reference.
                image.flags.writeable = False
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = hands.process(image)
                # print(results)
                # Draw the hand annotations on the image.
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        x = float(f'{hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y}')
                        x_list.append(x)
                        mp_drawing.draw_landmarks(
                            image,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS,
                            mp_drawing_styles.get_default_hand_landmarks_style(),
                            mp_drawing_styles.get_default_hand_connections_style())
                    # Flip the image horizontally for a selfie-view display.
                cv2.imshow('MediaPipe Hands', cv2.flip(image, 1))
                if cv2.waitKey(5) & 0xFF == 27:
                    break
            cap.release()
            cv2.destroyAllWindows()
            print(x_list)
            Q1 = np.percentile(x_list, 45)
            Q3 = np.percentile(x_list, 55)
            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            filtered_values = [x for x in x_list if lower_bound <= x <= upper_bound]
            variance = statistics.variance(filtered_values)
            std = statistics.stdev(filtered_values)
            print(std)
            count = self.count_direction_changes(filtered_values,0.005)
            print("count",count)
            if count> 10:
                print("Tremon")
                return True
            else:
                print("Normal")
                return False
            
    def count_direction_changes(self,values, threshold):
        # Initialize variables
        direction_changes = 0
        current_direction = None  # Track current direction, either "up" or "down"

        # Loop through each pair of consecutive values
        for i in range(1, len(values)):
            # Calculate the difference between consecutive values
            diff = values[i] - values[i - 1]
            if abs(diff) >= threshold:
                # Determine the direction: "up" or "down"
                if diff > 0:
                    new_direction = "up"
                elif diff < 0:
                    new_direction = "down"
                else:
                    new_direction = None  

                # Count change in direction
                if current_direction and new_direction and current_direction != new_direction:
                    direction_changes += 1

                # Update the current direction
                current_direction = new_direction

        return direction_changes
    
    def record_video(self,output_file='output.avi', duration=10, fps=20, resolution=(640, 480)):
        # Initialize the webcam
        cap = cv2.VideoCapture(0)  # 0 is the default webcam
        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        # Set the resolution
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Codec for .avi files
        out = cv2.VideoWriter(output_file, fourcc, fps, resolution)

        # Start recording
        print("Recording...")
        start_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Could not read frame.")
                break

            # Write the frame to the output file
            out.write(frame)

            # Display the frame (optional)
            cv2.imshow('Recording', frame)

            # Break the loop after the specified duration
            if time.time() - start_time > duration:
                print("Recording complete.")
                break

            # Press 'q' to stop recording manually
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("Recording stopped by user.")
                break

        # Release resources
        cap.release()
        out.release()
        cv2.destroyAllWindows()

    
    def _run(self):
        print("########")
        res = self.has_tremor()
        return res

class PoseCheck(BaseTool):
    name: str = "Check Pose"
    description: str = (
        "Check wheather the pose is good or not"
    )
    def angle_between_lines(self,A, B, C, D):
        v1x, v1y = B[0] - A[0], B[1] - A[1]
        v2x, v2y = D[0] - C[0], D[1] - C[1]
        
        
        dot_product = v1x * v2x + v1y * v2y
        magnitude_v1 = math.sqrt(v1x**2 + v1y**2)
        magnitude_v2 = math.sqrt(v2x**2 + v2y**2)
        
        cos_theta = dot_product / (magnitude_v1 * magnitude_v2)
        
        theta_radians = math.acos(cos_theta)
        theta_degrees = math.degrees(theta_radians)
        
        return theta_degrees
    
    def pose_check(self):
        time.sleep(10)
        try:
            body_parts = {
                    "Nose": 0,
                    "Left Eye": 1,
                    "Right Eye": 2,
                    "Left Ear": 3,
                    "Right Ear": 4,
                    "Left Shoulder": 5,
                    "Right Shoulder": 6,
                    "Left Elbow": 7,
                    "Right Elbow": 8,
                    "Left Wrist": 9,
                    "Right Wrist": 10,
                    "Left Hip": 11,
                    "Right Hip": 12,
                    "Left Knee": 13,
                    "Right Knee": 14,
                    "Left Ankle": 15,
                    "Right Ankle": 16
                }
            filename = "pose_image.png"
            cam = cv2.VideoCapture(0) 
            result, image = cam.read()
            
            if result:
                cv2.imwrite(filename,image)
                image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
                model = YOLO('yolov8l-pose.pt')
                results = model(filename,save=False)
                res_list = results[0].keypoints.data.tolist()[0]
                res_list = [list(map(int,l)) for l in res_list]
                direction = "Left" if res_list[body_parts["Right Shoulder"]][0] > res_list[body_parts["Nose"]][0] else "Right"
                A = res_list[body_parts[f"{direction} Hip"]]
                B = res_list[body_parts[f"{direction} Shoulder"]]
                C = res_list[body_parts[f"{direction} Ear"]]
                angle = self.angle_between_lines((0,350),(0,0),B,C)
                print("ANGGGGGGGGGGGGGGGGGGGGGLEEEEEEEEEEEEEEEEEEEEEEEE",angle)
                if angle<15:
                    return True
                else:
                    return False
        except:
            return "An error occured"

    def _run(self):
        print("########")
        res = self.pose_check()
        return res

class AvailableSlot(BaseTool):
    name: str = "Available Slot"
    description: str = (
        """This function returns available slots
        """
    )
    def list_of_upcoming_events(self) -> List:
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None
        if os.path.exists("src/medibot/tools/token.json"):
            print("path found")
            creds = Credentials.from_authorized_user_file("src/medibot/tools/token.json")
        else:
            print("path not found")
        try:
            print("Hellooooo3 caalllllllllllllllleeeeeeeeeeeeeeeender",creds)
            service = build("calendar", "v3", credentials=creds)

            # Call the Calendar API
            now = datetime.datetime.now().isoformat() + "Z"  # 'Z' indicates UTC time
            print("Getting the upcoming 10 events")
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=10,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                print("No upcoming events found.")
                return []
            event_names = []
            event_times = []                 
            for event in events:
                # event_names.append(event['summary'])
                start = event["start"].get("dateTime", event["start"].get("date"))
                if event['summary'] =="Available":
                    event_times.append(start)
                    event_names.append(event['id'])
                print(start, len(event['id']))
            # Prints the start and name of the next 10 events
            return event_times, event_names
        except HttpError as error:
            print("An error occured:", error)
            return []
        
    def _run(self) -> str:
        print("########")
        res, event_names = self.list_of_upcoming_events()
        return res,event_names


class BookSlot(BaseTool):
    name: str = "Book Slot"
    description: str = (
        """This function books slot in calendar
        """
    )
    def book_slot(self,event_id) -> List:
        SCOPES = ["https://www.googleapis.com/auth/calendar"]
        creds = None
        if os.path.exists("src/medibot/tools/token.json"):
            print("path found")
            creds = Credentials.from_authorized_user_file("src/medibot/tools/token.json")
        else:
            print("Path Not Found")
        try:
            service = build("calendar", "v3", credentials=creds)
            print("-----------event_id------------",event_id)
            event_id = str(event_id)
            calendar_id = 'primary'  # Default is the primary calendar

            # Fetch the current event details
            event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()

            # Modify event details
            event['summary'] = 'Booked'
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event
            ).execute()
            return True
            
        except HttpError as error:
            print("An error occured:", error)
            return False
        
    def _run(self, event_id) -> bool:
        print("########")
        res = self.book_slot(event_id)
        return res
        

# class AppointmentTool(BaseTool):
#     name: str = "Human interaction for futher procedure"
#     description: str = (
#         """Ask the user the best time for an appointment with a doctors.
#         """
#     )

#     def _run(self, argument: str = '', string: str = '') -> str:
#         print("########")
#         if string: print(string)
#         if argument: res = input(f"{argument} \n")
#         return res

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def on_camera():
    frameWidth = 640
    frameHeight = 480
    cap = cv2.VideoCapture(0)
    cap.set(3, frameWidth)
    cap.set(4, frameHeight)
    cap.set(10, 150)
    # client = OpenAI()

    model = YOLO("yolov8n-wounds.pt")  # load a pretrained model (recommended for training)
    # model = YOLO("yolo-Weights/yolov8n.pt")
    classNames = ["wound"]
    i = 1
    time = 1
    imgs = []

    while i <= 15 and time <= 600:
        success, img = cap.read()
        results = model(img, stream=True)

        # coordinates
        for r in results:
            boxes = r.boxes

            for box in boxes:
                # bounding box
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values

                # confidence
                confidence = math.ceil((box.conf[0] * 100)) / 100
                print("Confidence --->", confidence)

                # class name
                cls = int(box.cls[0])
                print("Class name -->", classNames[cls])

                if (confidence > 0.7):
                    # put box in cam
                    print(x1, y1, x2, y2)
                    cropped = img[y1:y2, x1:x2]
                    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
                    i += 1
                    # object details
                    org = [x1, y1]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    fontScale = 1
                    color = (255, 0, 0)
                    thickness = 1

                    cv2.putText(img, classNames[cls], org, font, fontScale, color, thickness)
                    cv2.imwrite(f"GeeksForGeeks_{i}.png", img)
                    cv2.imwrite(f"GeeksForGeeks_{i}_cropped.png", cropped)
                    imgs.append(f"GeeksForGeeks_{i}_cropped.png")
        cv2.imshow('Webcam', img)
        time += 1
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("image saved.")
    return imgs

class EyeTool(BaseTool):
    name: str = "Human eyes"
    description: str = (
        "Capture some images about open wounds."
    )

    def _run(self, argument: str) -> str:
        return on_camera()
        # return ''