import math
import cv2
import mediapipe as mp
import time


class handDetector:
    def __init__(self, mode=False, maxHands=2, detectionConfidence=0.5, trackingConfidence=0.5):
        self.locationsList = []
        self.results = None
        self.trackingConfidence = trackingConfidence
        self.detectionConfidence = detectionConfidence
        self.maxHands = maxHands
        self.mode = mode

        self.tipIds = [4, 8, 12, 16, 20]

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(self.mode, self.maxHands, 1, self.detectionConfidence, self.trackingConfidence)
        self.mpDraw = mp.solutions.drawing_utils

    def detectHands(self, vid, draw=True, flipType=True):
        vidRGB = cv2.cvtColor(vid, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(vidRGB)
        bothHands = []
        h, w, c = vid.shape
        if self.results.multi_hand_landmarks:
            for handType, handLms in zip(self.results.multi_handedness, self.results.multi_hand_landmarks):
                myHand = {}
                myLocationList = []
                xList = []
                yList = []
                for iD, lm in enumerate(handLms.landmark):
                    px, py, pz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                    myLocationList.append([iD, px, py])
                    xList.append(px)
                    yList.append(py)
                xMin, xMax = min(xList), max(xList)
                yMin, yMax = min(yList), max(yList)
                boxW, boxH = xMax - xMin, yMax - yMin
                bbox = xMin, yMin, boxW, boxH
                cx, cy = bbox[0] + (bbox[2] // 2), bbox[1] + (bbox[3] // 2)
                myHand["LocationList"] = myLocationList

                if flipType:
                    if handType.classification[0].label == "Right":
                        myHand["type"] = "Left"
                    else:
                        myHand["type"] = "Right"
                else:
                    myHand["type"] = handType.classification[0].label
                bothHands.append(myHand)

                if draw:
                    self.mpDraw.draw_landmarks(vid, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
                    cv2.rectangle(vid, (bbox[0] - 20, bbox[1] - 20),
                                  (bbox[0] + bbox[2] + 20, bbox[1] + bbox[3] + 20),
                                  (255, 0, 255), 2)
        if draw:
            return bothHands, vid
        else:
            return bothHands

    def findLocations(self, vid, hand=0, draw=True):
        self.locationsList = []
        xList = []
        yList = []
        bbox = []
        if self.results.multi_hand_landmarks:
            HandFound = self.results.multi_hand_landmarks[hand]
            for iD, lm in enumerate(HandFound.landmark):
                h, w, c = vid.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.locationsList.append([iD, cx, cy])
                if draw:
                    cv2.circle(vid, (cx, cy), 4, (255, 0, 255), cv2.FILLED)
            xMin, xMax = min(xList), max(xList)
            yMin, yMax = min(yList), max(yList)
            bbox = xMin, yMin, xMax, yMax

            if draw:
                cv2.rectangle(vid, (xMin - 20, yMin - 20), (xMax + 20, yMax + 20),
                              (0, 255, 0), 2)
        return self.locationsList, bbox

    def fingersUp(self, myHand):
        myHandType = myHand["type"]
        myLmList = myHand["LocationList"]
        if self.results.multi_hand_landmarks:
            fingers = []
            # Thumb
            if myHandType == "Right":
                if myLmList[self.tipIds[0]][1] > myLmList[self.tipIds[0] - 1][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
            else:
                if myLmList[self.tipIds[0]][1] < myLmList[self.tipIds[0] - 1][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)

            # 4 Fingers
            for iD in range(1, 5):
                if myLmList[self.tipIds[iD]][2] < myLmList[self.tipIds[iD] - 2][2]:
                    fingers.append(1)
                else:
                    fingers.append(0)
        return fingers
        # fingers = []
        # # Thumb
        # try:
        #     if self.locationsList[self.tipIds[0]][2] < self.locationsList[self.tipIds[0] - 1][2]:
        #         fingers.append(1)
        #     else:
        #         fingers.append(0)
        # except IndexError:
        #     fingers.append(0)
        # # Fingers
        # for iD in range(1, 5):
        #     try:
        #         if self.locationsList[self.tipIds[iD]][2] < self.locationsList[self.tipIds[iD] - 2][2]:
        #             fingers.append(1)
        #         else:
        #             fingers.append(0)
        #     except IndexError:
        #         fingers.append(0)
        #
        # return fingers

    def findDistance(self, p1, p2, img, draw=True, r=4, t=2):
        x1, y1 = self.locationsList[p1][1:]
        x2, y2 = self.locationsList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]


def main():
    capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    prevTime = 0
    detector = handDetector()
    while capture.isOpened():
        success, vid = capture.read()
        detector.detectHands(vid)
        locations, _ = detector.findLocations(vid)
        if len(locations):
            print(locations[4])
        currTime = time.time()
        fps = 1 / (currTime - prevTime)
        prevTime = currTime
        cv2.putText(vid, str(int(fps)), org=(20, 50), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=2, color=(255, 0, 255), thickness=3)
        cv2.imshow("Video", vid)

        cv2.waitKey(1)
    vid.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
