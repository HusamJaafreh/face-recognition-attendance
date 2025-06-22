import time
from datetime import datetime, date
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.metrics.pairwise import cosine_similarity
import cv2
from db_manager import DatabaseManager
import h5py
import threading
import tkinter as tk
from screeninfo import get_monitors


class StudentDisplay(tk.Toplevel):
    def __init__(self, master, monitor_index=0, width_ratio=0.5, height_ratio=0.5, pos_ratio_x=0.0, pos_ratio_y=0.0):
        super().__init__(master)
        self.title("Recognized Students")
        self.configure(bg="white")

        monitors = get_monitors()
        if monitor_index >= len(monitors):
            raise ValueError(f"Monitor index {monitor_index} is out of range.")
        monitor = monitors[monitor_index]
        screen_x, screen_y = monitor.x, monitor.y
        screen_width, screen_height = monitor.width, monitor.height

        win_width = int(screen_width * width_ratio)
        win_height = int(screen_height * height_ratio)
        win_x = int(screen_x + screen_width * pos_ratio_x)
        win_y = int(screen_y + screen_height * pos_ratio_y)

        self.geometry(f"{win_width}x{win_height}+{win_x}+{win_y}")
        self.overrideredirect(True)
        self.bind("<Escape>", lambda e: self.destroy())

        self.listbox = tk.Listbox(
            self, font=("Arial", 40), justify="center", bg="white", fg="black",
            activestyle="none", highlightthickness=0, selectbackground="white"
        )
        self.listbox.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.recognized_ids = []

    def add_student(self, student_id):
        if student_id not in self.recognized_ids:
            self.recognized_ids.insert(0, str(student_id))

            def update_listbox():
                self.listbox.delete(0, tk.END)
                for sid in self.recognized_ids:
                    self.listbox.insert(tk.END, sid.center(20))

            self.after(0, update_listbox)




db = DatabaseManager()
class FaceAuthenticationSystem:
    def __init__(self, hall_id, day_num, display_window=None, camera_index=0):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.mtcnn = MTCNN(keep_all=True, device=self.device)
        self.inception = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        self.camera_index = camera_index

        self.hall_id = hall_id
        self.display_window = display_window

        self.student_ids_for_current_section = []
        self.student_embeddings_for_current_section = {}
        self.recognized_faces = []
        self.cap = cv2.VideoCapture(self.camera_index)

        self.data = db.get_students_schedule_by_classroom_and_day(classroom_id=self.hall_id, day_num=day_num)
        

        self.terminate = False

    def take_photo(self):
        if not self.cap.isOpened():
            print("Cannot open camera.")
            return None
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to capture image.")
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def record_absences(self, sec_id):
        if sec_id:
            absent_ids = list(set(self.student_ids_for_current_section) - set(self.recognized_faces))
            db.mark_absence(schedual_id=sec_id, std_ids=absent_ids, date_value=date.today())

    def get_face_embedding(self, image):
        faces = self.mtcnn(image)
        if faces is not None:
            return [self.inception(face.unsqueeze(0).to(self.device))[0].detach().cpu().numpy() for face in faces]
        return []

    def get_students_embeddings(self, ids):
        with h5py.File("face_embeddings.h5", "r") as f:
            self.student_embeddings_for_current_section = {
                id: f[str(id)][:] for id in ids if str(id) in f
            }

    def recognize_face_step(self):
        img = self.take_photo()
        test_embeddings = self.get_face_embedding(img)
        if test_embeddings:
            for test_embedding in test_embeddings:
                best_match = None
                highest_similarity = 0
                for id, stored_embedding in self.student_embeddings_for_current_section.items():
                    similarity_score = cosine_similarity([stored_embedding], [test_embedding])[0][0]
                    if similarity_score > highest_similarity:
                        highest_similarity = similarity_score
                        best_match = id
                if highest_similarity > 0.5 and best_match not in self.recognized_faces:
                    print(f"✅ Face match: {best_match} (score: {highest_similarity:.2f})")
                    self.recognized_faces.append(best_match)
                    if self.display_window:
                        self.display_window.add_student(best_match)

    def run_attendance_loop(self, check_interval=60):
        from datetime import datetime
        counter = 1
        current_sec = None
        total_time = 0

        def time_in_range(start_str, end_str):
            nonlocal counter
            now = datetime.strptime("09:00", "%H:%M").time() if counter < 102 else datetime.strptime("20:00", "%H:%M").time()
            #counter += 1
            start = datetime.strptime(start_str, '%H:%M').time()
            end = datetime.strptime(end_str, '%H:%M').time()
            return start <= now <= end

        print("Starting attendance loop...")
        while not self.terminate:#while True:
            test_time_start = time.time()
            active_sec = next((item['schedual_id'] for item in self.data if time_in_range(item['start_time'], item['end_time'])), None)

            if active_sec:
                if active_sec != current_sec:
                    self.record_absences(current_sec)
                    self.cap = cv2.VideoCapture(self.camera_index)
                    self.student_ids_for_current_section = db.get_student_ids_by_schedule(active_sec)
                    current_sec = active_sec
                    self.get_students_embeddings(self.student_ids_for_current_section)
                    print(f'num of students: {self.student_ids_for_current_section}')
                print(f"🕒 Class in session (schedual_id={active_sec})")
                print(f"camera id = {self.camera_index}")
                self.recognize_face_step()
            else:
                if current_sec is not None:
                    self.record_absences(current_sec)
                    current_sec = None
                print('average time per loop:', total_time/100)
                print("No classes at this time. Waiting...")
                time.sleep(check_interval)
                self.cap.release()

            loop_time = time.time() - test_time_start
            total_time += loop_time
            print('⏱ Time per loop:', loop_time)
            if self.terminate:
                break
        if self.cap.isOpened():
            self.cap.release()
        print("Camera loop terminated.")




if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    display1 = StudentDisplay(
        root,
        monitor_index=0,
        width_ratio=0.5, 
        height_ratio=1,
        pos_ratio_x=0.0,
        pos_ratio_y=0.05
    )

    display2 = StudentDisplay(
        root,
        monitor_index=0,
        width_ratio=0.5,
        height_ratio=1,
        pos_ratio_x=0.5,  
        pos_ratio_y=0.05
    )

    def run_cam1():
        system1 = FaceAuthenticationSystem(hall_id=1, day_num=1, display_window=display1, camera_index=0)
        system1.run_attendance_loop()

    def run_cam2():
        system2 = FaceAuthenticationSystem(hall_id=2, day_num=4, display_window=display2, camera_index=1)
        system2.run_attendance_loop()

    threading.Thread(target=run_cam1, daemon=True).start()
    threading.Thread(target=run_cam2, daemon=True).start()


    root.mainloop()




















