import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Task_t(SqlAlchemyBase):
    __tablename__ = 'task_t'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    input_text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    output_text = sqlalchemy.Column(sqlalchemy.Text, nullable=False)