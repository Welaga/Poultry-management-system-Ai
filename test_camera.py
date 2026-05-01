import cv2

cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("❌ Cannot access webcam")
    exit()

print("✅ Webcam detected. Press 'q' to exit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame")
        break

    cv2.imshow("Webcam Test", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()