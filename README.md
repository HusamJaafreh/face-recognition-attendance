# Face Recognition Attendance System

Automatic classroom attendance using face recognition. Cameras mounted in lecture halls identify registered students during their scheduled lectures and record absences in a university database. Admins, instructors and students each get their own desktop dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?logo=opencv&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)

## Features

- **Face registration:** captures a student's photo from the webcam, detects the face with **MTCNN** and stores a 512-d **FaceNet (InceptionResnetV1, VGGFace2)** embedding in an HDF5 store.
- **Schedule-aware recognition:** each camera is bound to a lecture hall. During a scheduled lecture, the system only compares faces against the students enrolled in that section, using cosine similarity.
- **Automatic absence tracking:** students not seen during the lecture window are marked absent.
- **Multi-camera, multi-monitor:** runs several halls in parallel threads, each with its own live "recognized students" display.
- **Role-based dashboards (Tkinter):**
  - *Admin:* register or re-register student faces.
  - *Instructor:* view, edit and delete absences for their courses.
  - *Student:* view their own attendance record.

## Architecture

```
main.py               → attendance loop: camera → MTCNN → FaceNet → cosine match → mark absences
face_registration.py  → login + admin/instructor/student dashboards, face enrolment
db_manager.py         → data-access layer (CRUD + attendance queries)
models.py             → SQLAlchemy ORM schema (College, Course, Schedule, Student, Registration, Absence…)
university.db         → SQLite demo database seeded with synthetic (Faker-generated) data
```

## Getting started

```bash
git clone https://github.com/HusamJaafreh/face-recognition-attendance.git
cd face-recognition-attendance
python -m venv .venv && .venv\Scripts\activate   # Windows (use source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
```

Set the admin password (required for the admin login):

```bash
set ADMIN_PASSWORD=your-password        # Windows
export ADMIN_PASSWORD=your-password     # macOS/Linux
```

1. **Register faces:** run `python face_registration.py`, log in as admin and enrol students. This creates `face_embeddings.h5` locally.
2. **Start attendance:** run `python main.py`. Hall/camera mapping is configured at the bottom of `main.py`.

> **Privacy note:** face embeddings are biometric data, so they are deliberately **not** committed to this repository (see `.gitignore`). Generate your own by registering faces locally.

## Tech stack

Python · PyTorch · facenet-pytorch (MTCNN + InceptionResnetV1) · OpenCV · scikit-learn · SQLAlchemy · SQLite · h5py · Tkinter

## License

[MIT](LICENSE)
