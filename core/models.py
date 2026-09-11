"""Модели данных (SQLAlchemy ORM)"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from .database import Base
import enum

class UserRole(str, enum.Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    grades = relationship("Grade", back_populates="student")
    courses_as_teacher = relationship("Course", back_populates="teacher")
    attendance = relationship("Attendance", back_populates="student")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    semester = Column(String(20), nullable=False)
    credits = Column(Integer, default=3)
    teacher = relationship("User", back_populates="courses_as_teacher")
    schedules = relationship("Schedule", back_populates="course")
    grades = relationship("Grade", back_populates="course")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    day_of_week = Column(String(20), nullable=False)
    time_start = Column(String(10), nullable=False)
    time_end = Column(String(10), nullable=False)
    room = Column(String(20), nullable=False)
    building = Column(String(50))
    course = relationship("Course", back_populates="schedules")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    grade = Column(Float, nullable=False)
    comment = Column(Text)
    graded_at = Column(DateTime, default=datetime.utcnow)
    graded_by = Column(Integer, ForeignKey("users.id"))
    student = relationship("User", back_populates="grades")
    course = relationship("Course", back_populates="grades")

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)
    comment = Column(Text)
    student = relationship("User", back_populates="attendance")
