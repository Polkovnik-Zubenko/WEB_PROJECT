import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Password(SqlAlchemyBase):
    __tablename__ = 'new_password'

    id_key = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    key = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), unique=True)
