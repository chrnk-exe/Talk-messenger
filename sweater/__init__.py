from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy import create_engine
import argparse

app = Flask(__name__, static_folder='../build', static_url_path='/static', template_folder="../build")


# CORS CONFIG
app.config['CORS_HEADERS'] = 'Content-Type'

# DB CONFIG
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://jnhswycjcswlst:9b5195df03aa3102858be27dc5f5c2b1577f1c057ccd72c089ee76169f99ab60@ec2-54-220-166-184.eu-west-1.compute.amazonaws.com:5432/ddbk0hhom9sktr'

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://kbjqzvudqjenhr:a8de169a9e725cb5131f652cb713e9ec454c0011f0bd5c00e3d39df14f243fd1@ec2-52-211-158-144.eu-west-1.compute.amazonaws.com:5432/dui2neaevnm15'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:zxcursed@localhost/boxPostgres'

app.config['SECRET_KEY'] = 'YSAFDB978WH8AYIFHSNUSIJDFK'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# MAIL CONFIG
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_USERNAME'] = "talk.messenger.app@gmail.com"
app.config['MAIL_PASSWORD'] = "xfusuyaxpbhncetq"
app.config['MAIL_DEFAULT_SENDER'] = ("talk", "talk.messenger.app@gmail.com")
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False

# UPLOAD CONFIG
app.config['UPLOAD_FOLDER'] = 'uploads'


socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
mail = Mail(app)
token_key = URLSafeTimedSerializer(app.config['SECRET_KEY'])


engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
conn = engine.connect()

# count = conn.execute("SELECT * FROM information_schema.columns WHERE (column_name) = ('user_status')")

# count = conn.execute("SELECT * FROM public.user")

# count = conn.execute("SELECT column_name, column_default "
#                      "FROM information_schema.columns "
#                      "WHERE (table_schema, table_name) = ('public', 'user') "
#                      # "WHERE (table_schema) = ('public')"
#                      "ORDER BY ordinal_position;")

# count = conn.execute("SELECT * FROM TABLE USER;")


# count = conn.execute("ALTER TABLE public.user ADD user_status integer NOT NULL DEFAULT '0';")
# count = conn.execute("ALTER TABLE public.user DROP COLUMN user_status;")

# print(count)

# for i in count:
#     print(i)


# import psycopg2
# from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
#
# # Устанавливаем соединение с postgres
# connection = psycopg2.connect(user="postgres", password="zxcursed")
# connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
#
# # Создаем курсор для выполнения операций с базой данных
# cursor = connection.cursor()
# # sql_create_database =
# # Создаем базу данных
# cursor.execute('create database sqlalchemy_tuts')
# # Закрываем соединение
# cursor.close()
# connection.close()


from sweater import models, routes

# import eventlet
# eventlet.monkey_patch()

# app.run(debug=True)
# socketio.run(app, debug=True, host='0.0.0.0', port=8080)

if __name__ == "__main__":
    socketio.run(app, debug=True)
