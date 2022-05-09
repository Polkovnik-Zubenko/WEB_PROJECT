import datetime
import sqlalchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin
from .db_session import SqlAlchemyBase


class Collections(SqlAlchemyBase):

    __tablename__ = 'collections'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    href_link = sqlalchemy.Column(sqlalchemy.String, index=True, nullable=True)
    key_btn = sqlalchemy.Column(sqlalchemy.Integer, index=True, nullable=True)