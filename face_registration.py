import tkinter as tk
from tkinter import messagebox, ttk
import cv2
from PIL import Image, ImageTk
import h5py
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
from db_manager import DatabaseManager
from datetime import date
import os

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
INSTRUCTOR_PASSWORD = os.getenv("INSTRUCTOR_PASSWORD", "")
STUDENT_PASSWORD = os.getenv("STUDENT_PASSWORD", "")

selected_role = None

def create_embedding(image, student_id):
    mtcnn = MTCNN(keep_all=True)
    inception = InceptionResnetV1(pretrained='vggface2').eval()
    faces = mtcnn(image)
    if faces is not None:
        embeddings = []
        for face in faces:
            embedding = inception(face.unsqueeze(0))
            embeddings.append(embedding[0].detach().cpu().numpy())
        with h5py.File("face_embeddings.h5", "a") as f:
            if student_id in f:
                del f[student_id]
            f[student_id] = embeddings[0]
        print(f"\u2705 Face registered for student {student_id}!")

def select_user_type():
    global selected_role
    root = tk.Tk()
    root.title("Select User Type")
    root.geometry("300x250")

    tk.Label(root, text="Login As", font=("Arial", 14)).pack(pady=20)

    def select(role):
        global selected_role
        selected_role = role
        root.destroy()
        show_login_screen()

    tk.Button(root, text="Admin", command=lambda: select("admin"), width=20).pack(pady=5)
    tk.Button(root, text="Instructor", command=lambda: select("instructor"), width=20).pack(pady=5)
    tk.Button(root, text="Student", command=lambda: select("student"), width=20).pack(pady=5)

    root.mainloop()

def show_login_screen():
    login_win = tk.Tk()
    login_win.title("Login")
    login_win.geometry("300x200")

    tk.Label(login_win, text=f"{selected_role.capitalize()} Login").pack(pady=10)
    tk.Label(login_win, text="Username").pack()
    username_entry = tk.Entry(login_win)
    username_entry.pack()

    tk.Label(login_win, text="Password").pack()
    password_entry = tk.Entry(login_win, show="*")
    password_entry.pack()

    def login():
        username = username_entry.get()
        password = password_entry.get()

        if selected_role == "admin" and ADMIN_PASSWORD and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            login_win.destroy()
            open_dashboard_window()
        elif selected_role == "instructor" and password == INSTRUCTOR_PASSWORD:
            login_win.destroy()
            open_instructor_dashboard(username)
        elif selected_role == "student" and password == STUDENT_PASSWORD:
            login_win.destroy()
            open_student_dashboard(username)
        else:
            messagebox.showerror("Login Failed", "Invalid credentials.")

    tk.Button(login_win, text="Login", command=login).pack(pady=15)
    login_win.mainloop()

def open_dashboard_window():
    dash = tk.Tk()
    dash.title("Admin Dashboard")
    dash.geometry("300x150")
    tk.Label(dash, text="Welcome, Admin!").pack(pady=10)
    tk.Button(dash, text="Registration", command=open_registration_window).pack(pady=20)
    dash.mainloop()

def open_student_dashboard(student_id):
    student_win = tk.Tk()
    student_win.title("Student Dashboard")
    student_win.geometry("1000x700")
    tk.Label(student_win, text=f"Welcome, Student {student_id}", font=("Arial", 14)).pack(pady=10)

    text_box = tk.Text(student_win, width=60, height=25, font=("Courier New", 12))
    text_box.pack(padx=20, pady=20)

    db = DatabaseManager()
    attendance = db.get_student_attendance(student_id)

    for course, sections in attendance.items():
        for sec_id, absence_count in sections.items():
            text_box.insert(tk.END, f"Course: {course}, Section: {sec_id}, Absences: {absence_count}\n")

    student_win.mainloop()

def open_instructor_dashboard(instructor_id):
    instr_win = tk.Tk()
    instr_win.title("Instructor Dashboard")
    instr_win.geometry("400x350")
    tk.Label(instr_win, text=f"Instructor: {instructor_id}").pack(pady=10)

    db = DatabaseManager()
    courses = db.get_courses_by_instructor(instructor_id)  
    selected_course = tk.StringVar()

    course_map = {f"{cid} - {cname}": cid for cid, cname in courses}
    course_names = list(course_map.keys())
    
    selected_course.set(course_names[0])  
    tk.OptionMenu(instr_win, selected_course, *course_names).pack(pady=5)


    tree = ttk.Treeview(instr_win, columns=("ID", "Name", "Absences"), show='headings')
    tree.heading("ID", text="Student ID")
    tree.heading("Name", text="Name")
    tree.heading("Absences", text="Absences")
    tree.pack(pady=10)

    def load_data():
        tree.delete(*tree.get_children())
        course_id = course_map[selected_course.get()]
        for student_id, name, absences in db.get_students_in_course(course_id):
            tree.insert("", "end", values=(student_id, name, absences))

    def edit_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Select a row", "No student selected.")
            return

        item = tree.item(selected[0])
        student_id = item['values'][0]
        course_id = course_map[selected_course.get()]

        edit_win = tk.Toplevel()
        edit_win.title(f"Edit Absences for {student_id}")
        edit_win.geometry("400x300")

        tk.Label(edit_win, text=f"Absence Records for {student_id}").pack(pady=10)

        absences_tree = ttk.Treeview(edit_win, columns=("Date",), show='headings')
        absences_tree.heading("Date", text="Date")
        absences_tree.pack(pady=10, fill=tk.BOTH, expand=True)

        schedual_ids = db.get_schedual_ids_by_course_id(course_id)
        all_absences = []
        for sid in schedual_ids:
            records = db.get_absences_by_schedule_and_student(sid, student_id)
            for rec in records:
                absences_tree.insert("", "end", values=(rec.date,))
                all_absences.append((sid, rec.date))

        def delete_selected_absence():
            selected_item = absences_tree.selection()
            if not selected_item:
                messagebox.showerror("Error", "No absence selected.")
                return
            date_value = absences_tree.item(selected_item[0])['values'][0]
            for sid, d in all_absences:
                if str(d) == str(date_value):
                    db.delete_absence(sid, student_id, d)
                    absences_tree.delete(selected_item[0])
                    messagebox.showinfo("Deleted", f"Absence on {d} deleted.")
                    break

        tk.Button(edit_win, text="Delete Selected", command=delete_selected_absence).pack(pady=10)

    tk.Button(instr_win, text="Load Students", command=load_data).pack(pady=5)
    tk.Button(instr_win, text="Edit Absence", command=edit_selected).pack(pady=5)

    instr_win.mainloop()
    
def open_registration_window():
    reg_win = tk.Toplevel()
    reg_win.title("Student Registration")
    reg_win.geometry("640x700")

    tk.Label(reg_win, text="Student ID").pack(pady=5)
    student_id_entry = tk.Entry(reg_win)
    student_id_entry.pack()

    camera_label = tk.Label(reg_win)
    camera_label.pack(pady=10)

    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    running = [True]
    frame_loop = [None]

    def show_frame():
        if not running[0]:
            return
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (500, 300))
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(rgb))
            camera_label.imgtk = img
            camera_label.configure(image=img)
        frame_loop[0] = camera_label.after(10, show_frame)

    def stop_frame_loop():
        if frame_loop[0]:
            camera_label.after_cancel(frame_loop[0])
            frame_loop[0] = None

    def retake():
        retake_button.pack_forget()
        running[0] = True
        show_frame()

    def capture_and_save(overwrite=False):
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture image.")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)

        if len(faces) == 0:
            messagebox.showerror("Error", "No face detected. Try again.")
            return

        student_id = student_id_entry.get().strip()
        if not student_id:
            messagebox.showwarning("Warning", "Enter Student ID")
            return

        if not overwrite:
            with h5py.File('face_embeddings.h5', 'r') as f:
                if student_id in f.keys():
                    messagebox.showerror("Error", "Photo already exists for this ID.")
                    return
                
        frame = cv2.resize(frame, (500, 300))

        stop_frame_loop()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        create_embedding(rgb, student_id)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        camera_label.imgtk = img
        camera_label.configure(image=img)
        running[0] = False

        msg = "Photo updated." if overwrite else "Photo saved."
        messagebox.showinfo("Success", msg)
        retake_button.pack(pady=10)

    def new_photo():
        capture_and_save(overwrite=False)

    def update_photo():
        capture_and_save(overwrite=True)

    def on_close():
        stop_frame_loop()
        cap.release()
        cv2.destroyAllWindows()
        reg_win.destroy()

    reg_win.protocol("WM_DELETE_WINDOW", on_close)

    btn_frame = tk.Frame(reg_win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="New", width=10, command=new_photo).pack(side=tk.LEFT, padx=10)
    tk.Button(btn_frame, text="Update", width=10, command=update_photo).pack(side=tk.LEFT, padx=10)

    retake_button = tk.Button(reg_win, text="Retake", command=retake)
    retake_button.pack_forget()

    show_frame()

select_user_type()
