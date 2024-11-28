from crewai_tools import BaseTool
import cv2
from openai import OpenAI
import base64
import time
from ultralytics import YOLO
import math

class HumanTool(BaseTool):
    name: str = "Human interact"
    description: str = (
        "Ask the user questions to gather information."
    )

    def _run(self, argument: str) -> str:
        print("########")
        res = input(f"{argument} \n")
        return res

class AppointmentTool(BaseTool):
    name: str = "Human interaction for futher procedure"
    description: str = (
        """Ask the user the best time for an appointment with a doctors.
        """
    )

    def _run(self, argument: str = '', string: str = '') -> str:
        print("########")
        if string: print(string)
        if argument: res = input(f"{argument} \n")
        return res

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