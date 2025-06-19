from sqlalchemy.exc import NoResultFound
from models import Session, Schedual, Schedual_days, Std_reg, Student, Std_abb, Course
from datetime import date
from sqlalchemy import func
from sqlalchemy import distinct

class DatabaseManager:
    def __init__(self):
      self.Session = Session

    def add(self, obj):
        with self.Session() as session:
            session.add(obj)
            session.commit()

    def get_all(self, model):
        with self.Session() as session:
            return session.query(model).all()

    def get_by_id(self, model, pk):
        with self.Session() as session:
            try:
                return session.query(model).get(pk)
            except NoResultFound:
                return None

    def update(self, model, pk, update_dict):
        with self.Session() as session:
            obj = session.query(model).get(pk)
            if not obj:
                return False
            for key, value in update_dict.items():
                setattr(obj, key, value)
            session.commit()
            return True

    def delete(self, model, pk):
        with self.Session() as session:
            obj = session.query(model).get(pk)
            if not obj:
                return False
            session.delete(obj)
            session.commit()
            return True


    def get_students_schedule_by_classroom_and_day(self, classroom_id, day_num):
      with self.Session() as session:
        results = (
            session.query(Std_reg.std_id, Schedual.schedual_id, Schedual_days.start_time, Schedual_days.end_time)
            .join(Schedual, Schedual.schedual_id == Std_reg.schedual_id)
            .join(Schedual_days, Schedual.schedual_id == Schedual_days.schedual_id)
            .filter(Schedual_days.classroom_id == classroom_id, Schedual_days.day_num == day_num)
            .all()
        )

        grouped = {}
        for std_id, schedual_id, start_time, end_time in results:
            if schedual_id not in grouped:
                grouped[schedual_id] = {
                    "schedual_id": schedual_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "std_ids": []
                }
            grouped[schedual_id]["std_ids"].append(std_id)

        return list(grouped.values())
          

    def get_student_ids_by_schedule(self, schedual_id):
      with self.Session() as session:
          result = (
              session.query(Std_reg.std_id)
              .filter(Std_reg.schedual_id == schedual_id)
              .all()
          )
          return [r.std_id for r in result]

    def mark_absence(self, schedual_id, std_ids, date_value=None):
      with self.Session() as session:
        records = [
            Std_abb(
                schedual_id=schedual_id,
                std_id=std_id,
                date=date_value,
                notes=""
            )
            for std_id in std_ids
        ]
        session.add_all(records)
        session.commit()

    def get_absences_by_schedule_and_student(self, schedual_id, std_id):
      with self.Session() as session:
          result = (
              session.query(Std_abb)
              .filter(Std_abb.schedual_id == schedual_id, Std_abb.std_id == std_id)
              .all()
          )
          return result
    def get_course_name_and_section(self, schedual_id):
        with self.Session() as session:
            result = (
                session.query(Schedual.sec_id, Course.course_name)
                .join(Course, Course.course_id == Schedual.course_id)
                .filter(Schedual.schedual_id == schedual_id)
                .first()
            )
            return {
                "sec_id": result.sec_id,
                "course_name": result.course_name
            } if result else None

    def get_students_in_course(self, course_id):
        with self.Session() as session:
            schedual_ids = (
                session.query(Schedual.schedual_id)
                .filter(Schedual.course_id == course_id)
                .subquery()
            )
    
            result = (
                session.query(
                    Student.id.label("std_id"),
                    Student.first_name.label("student_name"),
                    func.count(Std_abb.std_abb_id).label("num_absences")
                )
                .join(Std_reg, Student.id == Std_reg.std_id)
                .join(Schedual, Schedual.schedual_id == Std_reg.schedual_id)
                .outerjoin(
                    Std_abb,
                    (Std_abb.std_id == Student.id) &
                    (Std_abb.schedual_id.in_(schedual_ids))
                )
                .filter(Schedual.course_id == course_id)
                .group_by(Student.id, Student.first_name)
                .all()
            )
    
            return [(r.std_id, r.student_name, r.num_absences) for r in result]

    def get_schedual_ids_by_course_id(self, course_id):
        with self.Session() as session:
            result = (
                session.query(Schedual.schedual_id)
                .filter(Schedual.course_id == course_id)
                .all()
            )
            return [r.schedual_id for r in result]

    def delete_absence(self, schedual_id, std_id, date_value):
        with self.Session() as session:
            session.query(Std_abb).filter(
                Std_abb.schedual_id == schedual_id,
                Std_abb.std_id == std_id,
                Std_abb.date == date_value
            ).delete()
            session.commit()







    def get_courses_by_instructor(self, instructor_id):
        with self.Session() as session:
            results = (
                session.query(distinct(Schedual.course_id), Course.course_name)
                .join(Course, Course.course_id == Schedual.course_id)
                .filter(Schedual.instructor_id == instructor_id)
                .all()
            )
            return results

    def get_student_attendance(self, student_id: int):
        with self.Session() as session:
            rows = (
                session.query(
                    Course.course_name,
                    Schedual.sec_id,
                    func.count(Std_abb.std_abb_id).label("absences")
                )
                .join(Schedual, Schedual.course_id == Course.course_id)
                .join(Std_reg, Std_reg.schedual_id == Schedual.schedual_id)
                .outerjoin(
                    Std_abb,
                    (Std_abb.schedual_id == Schedual.schedual_id) &
                    (Std_abb.std_id == Std_reg.std_id)
                )
                .filter(Std_reg.std_id == student_id)
                .group_by(Course.course_name, Schedual.sec_id)
                .all()
            )
    
            attendance = {}
            for course_name, sec_id, absences in rows:
                attendance.setdefault(course_name, {})[sec_id] = absences
    
            return attendance