# backend/config.py
import os

class Config:
    # Update the connection string as needed, or set DATABASE_URL in your environment.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:password@localhost:5433/meetingdb'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '00ab9f90984adb36a6b0326625399a0e3c6f2f5b9098b64d860f3a6ac8bf1b74')
