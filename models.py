import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, CHAR
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
engine = create_engine("sqlite:///university.db", echo=True)
Base = declarative_base()

class College(Base):
    __tablename__ = 'College'
    name = Column(CHAR(50), primary_key=True, unique=True)
    main_office = Column(CHAR(50))
    phone = Column(CHAR(12))
    dean = Column(CHAR(50))

class Department(Base):
    __tablename__ = 'Department'
    code_number = Column(Integer, primary_key=True)
    name = Column(CHAR(50), unique=True)
    main_office = Column(CHAR(50))
    phone = Column(CHAR(50))
    chairman = Column(CHAR(50))
    chairman_start_date = Column(Date)

class Course(Base):
    __tablename__ = 'Course'
    course_id = Column(Integer, primary_key=True)
    course_name = Column(CHAR(50), unique=True)

class Instructor(Base):
    __tablename__ = 'Instructor'
    id = Column(Integer, primary_key=True)
    name = Column(CHAR(50))

class Student(Base):
    __tablename__ = 'Student'
    id = Column(Integer, primary_key=True)
    first_name = Column(CHAR(50))
    last_name = Column(CHAR(50))
    address = Column(CHAR(50))
    phone = Column(CHAR(50))
    major_id = Column(Integer, ForeignKey('Major.major_id', onupdate="CASCADE", ondelete="SET NULL"))
    birth_date = Column(Date)

class Major(Base):
    __tablename__ = 'Major'
    major_id = Column(Integer, primary_key=True)
    major_name = Column(CHAR(50), unique=True)
    school_id = Column(Integer, ForeignKey('School.school_id', onupdate="CASCADE", ondelete="SET NULL"))

class Classroom(Base):
    __tablename__ = 'Classroom'
    id = Column(Integer, primary_key=True)
    building_code = Column(CHAR(50))
    room_number = Column(Integer)

class Schedual(Base):
    __tablename__ = 'Schedual'
    schedual_id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('Course.course_id', onupdate="CASCADE", ondelete="SET NULL"))
    sec_id = Column(Integer)
    instructor_id = Column(Integer, ForeignKey('Instructor.id', onupdate="CASCADE", ondelete="SET NULL"))
    semester = Column(CHAR(50))
    year = Column(Integer)

class Schedual_days(Base):
    __tablename__ = 'Schedual_days'
    id = Column(Integer, primary_key=True)
    schedual_id = Column(Integer, ForeignKey('Schedual.schedual_id', onupdate="CASCADE", ondelete="SET NULL"), primary_key=True)
    day_num = Column(Integer)
    start_time = Column(CHAR(50))
    end_time = Column(CHAR(50))
    classroom_id = Column(Integer, ForeignKey('Classroom.id', onupdate="CASCADE", ondelete="SET NULL"))

class School(Base):
    __tablename__ = 'School'
    school_id = Column(Integer, primary_key=True)
    school_name = Column(CHAR(50), unique=True)

class Std_reg(Base):
    __tablename__ = 'Std_reg'
    schedual_id = Column(Integer, ForeignKey('Schedual.schedual_id', onupdate="CASCADE", ondelete="SET NULL"), primary_key=True)
    std_id = Column(Integer, ForeignKey('Student.id', onupdate="CASCADE", ondelete="SET NULL"), primary_key=True)

class Std_abb(Base):
    __tablename__ = 'Std_abb'
    std_abb_id = Column(Integer, primary_key=True)
    schedual_id = Column(Integer, ForeignKey('Schedual.schedual_id', onupdate="CASCADE", ondelete="SET NULL"))
    std_id = Column(Integer, ForeignKey('Student.id', onupdate="CASCADE", ondelete="SET NULL"))
    notes = Column(CHAR(100))
    date = Column(Date)



Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

