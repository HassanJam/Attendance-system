import cv2
import pickle
import numpy as np
import face_recognition
import mysql.connector
from datetime import datetime


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="faceattendancedb"
)

cursor = mydb.cursor()


cap = cv2.VideoCapture(0)
cap.set(3, 1280)  
cap.set(4, 720)   


print("Loading encoded file...")
with open("Encodefile.p", "rb") as file:
    encoding_list_known_with_ids = pickle.load(file)

encoding_list_known, employee_ids = encoding_list_known_with_ids
print("Loaded encoded file")

# Function to log attendance to the database
def log_attendance(employee_id):
    current_date = datetime.now().date()
    current_time = datetime.now().time()

    # Check if the employee already logged in today
    query = "SELECT * FROM attendance WHERE employee_id=%s AND date=%s"
    cursor.execute(query, (employee_id, current_date))
    result = cursor.fetchone()

    if result is None:  
        query = "INSERT INTO attendance (employee_id, date, in_time) VALUES (%s, %s, %s)"
        cursor.execute(query, (employee_id, current_date, current_time))
        mydb.commit()
        print(f"Attendance logged for {employee_id} at {current_time}")
    else:
        print(f"Attendance for {employee_id} has already been logged today.")

while True:
   
    success, img = cap.read()
    if not success:
        print("Failed to capture image")
        break
    img_small = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    img_small = cv2.cvtColor(img_small, cv2.COLOR_BGR2RGB)

   
    face_current_frame = face_recognition.face_locations(img_small)
    encode_current_frame = face_recognition.face_encodings(img_small, face_current_frame)

    
    for encode_face, face_location in zip(encode_current_frame, face_current_frame):
        matches = face_recognition.compare_faces(encoding_list_known, encode_face)
        face_distance = face_recognition.face_distance(encoding_list_known, encode_face)

        
        match_index = np.argmin(face_distance)

        if matches[match_index]:
           
            employee_id = employee_ids[match_index]
            print(f"Known face detected: {employee_id}")

            top, right, bottom, left = face_location
            top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4  
            cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

            
            cv2.putText(img, employee_id, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            
            log_attendance(employee_id)

    cv2.imshow("Face Attendance", img)

    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()
cursor.close()
mydb.close()