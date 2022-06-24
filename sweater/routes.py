import datetime
import json
import os
import io
import traceback

from flask import render_template, request, redirect, send_from_directory, jsonify, url_for, send_file
from flask_login import login_user, current_user, logout_user
from flask_mail import Message as Mesage
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import cross_origin
from flask_socketio import emit, send, join_room, leave_room
from PIL import Image

from sweater import app, db, mail, token_key, socketio
from sweater.models import User, Talk, Message, Dialog, Media


rooms_list = set()


@app.route('/')
@app.route('/home')
def index():
    return render_template('index.html')


@socketio.on('authorize')
# @cross_origin()
def handle_connection(data):
    try:
        global rooms_list
        user_id = str(data['id'])

        join_room(user_id)
        rooms_list.add(user_id)

        user = db.session.query(User).filter_by(id=int(user_id)).first_or_404()
        user.date_visited = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
        user.user_status = 1
        db.session.commit()

        dialog_ids = json.loads(user.dialogs)
        for dialog_id in dialog_ids:
            dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
            dialog_members = json.loads(dialog.members)

            for member_id in dialog_members:
                if str(member_id) != user_id and str(member_id) in rooms_list:
                    emit('socket_status', {'info': 'status_info',
                                           'dialog_id': int(dialog_id),
                                           'user_id': int(user_id),
                                           "date_visit": user.date_visited,
                                           'user_status': 1},
                         to=str(member_id), namespace='/')

        print("authorize user", user_id)

    except Exception as e:
        print('connect error', str(e) + traceback.format_exc())
        return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@socketio.on('read_messages')
# @cross_origin()
def read_unread(data):
    dialog_id = str(data['dialog_id'])
    user_id = int(current_user.get_id())

    if user_id is not None:
        user_id = int(current_user.get_id())
        user = db.session.query(User).filter_by(id=user_id).first_or_404()

        unread_dialogs_list = json.loads(user.unread_dialogs)
        if dialog_id in unread_dialogs_list:
            unread_dialogs_list.pop(dialog_id)

        user.unread_dialogs = json.dumps(unread_dialogs_list)
        db.session.commit()


@socketio.on('connect')
# @cross_origin()
def connect_socket():
    try:
        global rooms_list
        user_id = current_user.get_id()

        if user_id is not None:
            join_room(user_id)
            rooms_list.add(user_id)

            user = db.session.query(User).filter_by(id=int(user_id)).first_or_404()
            user.date_visited = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
            user.user_status = 1
            db.session.commit()

            dialog_ids = json.loads(user.dialogs)
            for dialog_id in dialog_ids:
                dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
                dialog_members = json.loads(dialog.members)

                for member_id in dialog_members:
                    if str(member_id) != user_id and str(member_id) in rooms_list:
                        emit('socket_status', {'info': 'status_info',
                                               'dialog_id': int(dialog_id),
                                               'user_id': int(user_id),
                                               "date_visit": user.date_visited,
                                               'user_status': 1},
                             to=str(member_id), namespace='/')

        print("connect user", str(user_id), "!")

    except Exception as e:
        print('connect error', str(e) + traceback.format_exc())
        return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@socketio.on('manual_disconnect')
# @cross_origin()
def manual_disconnect(data):
    print('est signal!', 'peredan id', data['user_id'])
    return 'est signal!', 'peredan id', data['user_id']

    # try:
    #
    #     user_id = str(data['user_id'])
    #     leave_room(user_id)
    #
    #     if user_id is not None:
    #         user = db.session.query(User).filter_by(id=user_id).first_or_404()
    #         user.date_visited = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
    #         user.user_status = 0
    #         db.session.commit()
    #
    #         dialog_ids = json.loads(user.dialogs)
    #         for dialog_id in dialog_ids:
    #             dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
    #             dialog_members = json.loads(dialog.members)
    #
    #             for member_id in dialog_members:
    #                 if str(member_id) != user_id and str(member_id) in rooms_list:
    #                     emit('socket_status', {'info': 'status_info',
    #                                            'dialog_id': int(dialog_id),
    #                                            'user_id': int(user_id),
    #                                            'user_status': 0,
    #                                            'date_visit': user.date_visited},
    #                          to=str(member_id), namespace='/')
    #
    #         print("disconnect(", user_id)
    #
    # except Exception as e:
    #     print('connect error', str(e) + traceback.format_exc())
    #     return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@socketio.on('disconnect')
# @cross_origin()
def disconnect_socket():
    try:

        user_id = current_user.get_id()
        leave_room(user_id)

        if user_id is not None:
            user = db.session.query(User).filter_by(id=user_id).first_or_404()
            user.date_visited = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
            user.user_status = 0
            db.session.commit()

            dialog_ids = json.loads(user.dialogs)
            for dialog_id in dialog_ids:
                dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
                dialog_members = json.loads(dialog.members)

                for member_id in dialog_members:
                    if str(member_id) != user_id and str(member_id) in rooms_list:
                        emit('socket_status', {'info': 'status_info',
                                               'dialog_id': int(dialog_id),
                                               'user_id': int(user_id),
                                               'user_status': 0,
                                               'date_visit': user.date_visited},
                             to=str(member_id), namespace='/')

            print("disconnect(", user_id)

    except Exception as e:
        print('disconnect error', str(e) + traceback.format_exc())
        return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/check_name', methods=['GET'])
def check_name():
    if request.method == 'GET':
        checking_name = request.args.get("userName")
        try:
            all_names = db.session.query(User.name).all()

            # print(any(x[0] == checking_name for x in all_names))
            if any(x[0] == checking_name for x in all_names):
                return jsonify({"status": 1, "info": "name already taken"})
            else:
                return jsonify({"status": 0, "info": "ye, this is good"})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/check_mail', methods=['GET'])
def check_mail():
    if request.method == 'GET':
        checking_email = request.args.get("email")
        try:
            all_emails = db.session.query(User.email).all()

            # print(any(x[0] == checking_name for x in all_names))
            if any(x[0] == checking_email for x in all_emails):
                return jsonify({"status": 1, "info": "email already taken"})
            else:
                return jsonify({"status": 0, "info": "ye, this is good"})
        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/register_new_user', methods=['POST'])
def register_new_user():
    if request.method == 'POST':
        response = request.get_json()
        name = response['userName']
        email = response['email']
        password = response['password']

        all_users = db.session.query(User).all()
        if any((x.name == name or x.email == email) for x in all_users):
            return jsonify({"status": 1, "info": "name or email already engaged"})

        user = User(name=name,
                    email=email,
                    password=generate_password_hash(password),
                    date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
        try:
            db.session.add(user)
            db.session.commit()
            last_id = db.session.query(User.id).order_by(User.id.desc()).first()

            token = token_key.dumps(email)
            msg = Mesage('Confirm email', sender="talk", recipients=[email])
            link = url_for('confirm_token', token=str(token), _external=True)
            msg.body = 'Click this link to verify your account on Talk Messenger: ' + link
            mail.send(msg)

            return jsonify({"status": 0, "id": last_id[0]})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/confirm_email/<token>', methods=['GET'])
def confirm_token(token):
    if request.method == 'GET':
        try:
            email = token_key.loads(token, max_age=3600)
            user = db.session.query(User).filter_by(email=email).first_or_404()
            if user is None:
                return "There is no token like that"

            user.is_activated = True
            db.session.commit()
            return redirect("/")

        except Exception as e:
            return str(e) + traceback.format_exc()


def convert_visit_date(date):
    try:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        visit_date = datetime.datetime.fromisoformat(str(date))
        month_str = months[visit_date.month - 1]

        if visit_date.year != datetime.datetime.now().year:
            response = 'last seen ' + str(visit_date.day) + ' ' + month_str + ' ' + str(visit_date.year)

        elif visit_date.day != datetime.datetime.now().day:
            response = 'last seen ' + str(visit_date.day) + ' ' + month_str + ' ' + str(visit_date.hour) + ':' + str(visit_date.minute)

        else:
            response = 'last seen at ' + str(visit_date.hour) + ':' + str(visit_date.minute)

        return response

    except Exception as e:
        return 'last seen recently'


@app.route('/authorize', methods=['POST'])
def login():
    if request.method == 'POST':

        response = request.get_json()
        name_mail = response['email']
        password = response['password']

        users = User.query.all()
        try:
            for user in users:
                if (user.name == name_mail or user.email == name_mail) and \
                        check_password_hash(user.password, password):
                    if user.is_activated:
                        login_user(user, duration=datetime.timedelta(hours=24))

                        user_id = user.id

                        dialogs_ids = json.loads(user.dialogs)
                        dialogs = db.session.query(Dialog).filter(
                            Dialog.id.in_(dialogs_ids)).order_by(Dialog.date_update.desc()).all()

                        response_list = []
                        for dialog in dialogs:
                            members_list = []
                            members = json.loads(dialog.members)
                            members.remove(user_id)
                            for member_id in members:
                                member = db.session.query(User).filter_by(id=member_id).first_or_404()
                                members_list.append({"name": member.name,
                                                     "user_status": member.user_status,
                                                     'date_visit': convert_visit_date(member.date_visited),
                                                     "avatar_id": member.avatar_id,
                                                     'email': member.email})

                            talks_ids = json.loads(dialog.talks)
                            last_message_value = None
                            if len(talks_ids) > 0:

                                talk = db.session.query(Talk).filter(Talk.id.in_(talks_ids)).order_by(
                                    Talk.id.desc()).first_or_404()

                                messages_ids = json.loads(talk.messages)
                                if len(messages_ids) > 0:
                                    message = db.session.query(Message).filter(Message.id.in_(messages_ids)).order_by(
                                        Message.id.desc()).first_or_404()
                                    if message.type == "text":
                                        last_message_value = message.value
                                    else:
                                        media = db.session.query(Media).filter_by(id=message.value).first_or_404()
                                        last_message_value = media.name

                            response_list.append({"id": dialog.id,
                                                  "other_members": members_list,
                                                  "last_message": last_message_value})

                        return jsonify({"status": 0,
                                        "id": user.id,
                                        "name": user.name,
                                        "dialogs": response_list,
                                        "avatar_id": user.avatar_id,
                                        "info": "authorization successful"})
                    else:
                        return jsonify({"status": 1, "info": "email not activated"})

            return jsonify({"status": 1, "info": "user not found"})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/is_authorized', methods=['GET'])
def is_authorized():
    if request.method == 'GET':
        try:
            if current_user.is_authenticated:
                user_id = int(current_user.get_id())
                user = db.session.query(User).filter_by(id=user_id).first_or_404()

                dialogs_ids = json.loads(user.dialogs)
                dialogs = db.session.query(Dialog).filter(
                    Dialog.id.in_(dialogs_ids)).order_by(Dialog.date_update.desc()).all()

                response_list = []
                for dialog in dialogs:
                    members_list = []
                    members = json.loads(dialog.members)
                    members.remove(user_id)

                    for member_id in members:
                        member = db.session.query(User).filter_by(id=member_id).first_or_404()

                        members_list.append({"name": member.name,
                                             "user_status": member.user_status,
                                             'date_visit': convert_visit_date(member.date_visited),
                                             "avatar_id": member.avatar_id,
                                             'email': member.email})

                    talks_ids = json.loads(dialog.talks)
                    last_message_value = None
                    if len(talks_ids) > 0:

                        talk = db.session.query(Talk).filter(Talk.id.in_(talks_ids)).order_by(
                            Talk.id.desc()).first_or_404()

                        messages_ids = json.loads(talk.messages)
                        if len(messages_ids) > 0:
                            message = db.session.query(Message).filter(Message.id.in_(messages_ids)).order_by(
                                Message.id.desc()).first_or_404()
                            if message.type == "text":
                                last_message_value = message.value
                            else:
                                media = db.session.query(Media).filter_by(id=message.value).first_or_404()
                                last_message_value = media.name

                    unread_dialogs_list = json.loads(user.unread_dialogs)
                    unread_count = unread_dialogs_list[str(dialog.id)] if str(dialog.id) in unread_dialogs_list else 0

                    response_list.append(
                        {"id": dialog.id,
                         "other_members": members_list,
                         "last_message": last_message_value,
                         "unread_count": unread_count})

                return jsonify({"status": 0,
                                "is_auth": True,
                                "id": user_id,
                                "avatar_id": user.avatar_id,
                                "name": user.name,
                                "dialogs": response_list})
            else:
                return jsonify({"status": 0, "is_auth": False})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/un_authorize', methods=['GET'])
def log_out():
    if request.method == 'GET':
        try:
            user_id = current_user.get_id()
            print('un_authorize', user_id)
            user = db.session.query(User).filter_by(id=user_id).first_or_404()
            user.date_visited = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
            user.user_status = 0
            db.session.commit()

            dialog_ids = json.loads(user.dialogs)
            for dialog_id in dialog_ids:
                dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
                dialog_members = json.loads(dialog.members)

                for member_id in dialog_members:
                    if str(member_id) != user_id and str(member_id) in rooms_list:
                        emit('socket_status', {'info': 'status_info',
                                               'dialog_id': int(dialog_id),
                                               'user_id': int(user_id),
                                               'date_visit': user.date_visited,
                                               'user_status': 0},
                             to=str(member_id), namespace='/')

            logout_user()
            return redirect("/")
        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/static/<path:static_type>/<path:filename>')
def serve_static(static_type, filename):
    # root_dir = os.path.dirname(os.getcwd())
    return send_from_directory(os.path.join('../', 'build', 'static', static_type), filename)


@app.route('/manifest.json')
def get_manifest():
    return send_from_directory(os.path.join('../', 'build'), 'manifest.json')


@app.route('/icons/<path:filename>')
def get_icon(filename):
    return send_from_directory(os.path.join('../', 'build'), filename)


@app.route('/favicon.ico')
def get_main_icon():
    return send_from_directory(os.path.join('../', 'build'), 'favicon.ico')


@app.route('/search_user', methods=['GET'])
def search_user():
    if request.method == "GET":

        value = request.args.get("value")
        try:
            cur_user = db.session.query(User).filter_by(id=int(current_user.get_id())).first_or_404()
            dialogs = db.session.query(Dialog).filter(Dialog.id.in_(json.loads(cur_user.dialogs))).all()

            own_members = set()
            for dialog in dialogs:
                members_list = json.loads(dialog.members)
                if len(members_list) < 3:
                    for member in members_list:
                        own_members.add(member)

            users = db.session.query(User).filter(User.name.startswith(value)).filter(
                User.id.not_in(own_members)).limit(10).all()

            response = list({"id": user.id,
                             "name": user.name,
                             "avatar_id": user.avatar_id,
                             "date_visit": user.date_visited,
                             "user_status": user.user_status} for user in users)

            return jsonify({"status": 0, "users": response})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


def add_to_json(obj, count):
    lst = json.loads(obj)
    lst.append(count)
    return json.dumps(lst)


@app.route('/create_dialog', methods=['POST'])
def create_dialog():
    if request.method == "POST":
        try:
            global rooms_list

            data = request.get_json()
            title = data["title"]
            members = data["members"]

            cur_id = int(current_user.get_id())
            cur_user = db.session.query(User).filter_by(id=cur_id).first_or_404()
            dialogs = db.session.query(Dialog).filter(Dialog.id.in_(json.loads(cur_user.dialogs))).all()

            own_members = set()
            for dialog in dialogs:
                members_list = json.loads(dialog.members)
                if len(members_list) < 3:
                    for member in members_list:
                        own_members.add(member)

            if len(members) < 3:
                if all(member_id in own_members for member_id in members):
                    return jsonify({"status": 1, "info": "already have dialog with that user"})

            dialog = Dialog(members=json.dumps(members), date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
            db.session.add(dialog)
            db.session.commit()

            for user_id in members:
                user = db.session.query(User).filter_by(id=user_id).first_or_404()
                user.dialogs = add_to_json(user.dialogs, dialog.id)
            db.session.commit()

            dialog_members = json.loads(dialog.members)

            for member_id in dialog_members:
                if member_id != cur_id and str(member_id) in rooms_list:

                    members_list = []
                    other_members = dialog_members.copy()
                    other_members.remove(member_id)

                    for other_member in other_members:
                        member = db.session.query(User).filter_by(id=other_member).first_or_404()

                        members_list.append({"name": member.name,
                                             "user_status": member.user_status,
                                             "date_visit": member.date_visited,
                                             "avatar_id": member.avatar_id})

                    emit('new_dialog', {'info': 'new_dialog',
                                        'dialog_id': dialog.id,
                                        'other_members': members_list},
                         to=str(member_id), namespace='/')

            return jsonify({"status": 0, "id": dialog.id})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/create_talk', methods=['POST'])
def create_talk():
    if request.method == "POST":
        try:
            data = request.get_json()
            title = data["title"]
            dialog_id = data["dialog_id"]
            cur_id = int(current_user.get_id())

            talk = Talk(title=title, date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
            db.session.add(talk)
            db.session.commit()

            dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
            dialog.talks = add_to_json(dialog.talks, talk.id)
            db.session.commit()

            dialog_members = json.loads(dialog.members)
            other_members = dialog_members.copy()
            other_members.remove(cur_id)

            for member_id in other_members:
                if str(member_id) in rooms_list:

                    emit('new_talk', {'info': 'new_talk',
                                      "dialog_id": dialog.id,
                                      "talk_id": talk.id,
                                      "title": talk.title,
                                      "date": talk.date_create},
                         to=str(member_id), namespace='/')

            return jsonify({"status": 0, "id": talk.id, "date": talk.date_create})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/upload_file', methods=['POST'])
def upload_file():
    if request.method == "POST":
        try:
            file = request.files["value"]
            image_extensions = {'txt', 'png', 'jpg', 'jpeg'}
            audio_extensions = {'mp3'}
            video_extensions = {'mpeg', 'avi', 'mpeg4', 'mp4'}

            if file and '.' in file.filename:
                filename = secure_filename(file.filename)
                split_name = filename.rsplit('.', 1)

                if split_name[1] in image_extensions:
                    media = Media(name='image', type=split_name[1], data=file.read(), date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
                    db.session.add(media)
                    db.session.commit()
                    return jsonify({"status": 0, "info": "successful image!", "file_id": media.id})

                elif split_name[1] in audio_extensions:
                    media = Media(name='audio', type=split_name[1], data=file.read(), date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
                    db.session.add(media)
                    db.session.commit()
                    return jsonify({"status": 0, "info": "successful audio!", "file_id": media.id})

                elif split_name[1] in video_extensions:
                    media = Media(name='video', type=split_name[1], data=file.read(), date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
                    db.session.add(media)
                    db.session.commit()
                    return jsonify({"status": 0, "info": "successful video!", "file_id": media.id})

            else:
                raise ValueError('Invalid file struct :-(')

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/send_message', methods=['POST'])
def send_message():
    if request.method == "POST":
        try:
            global rooms_list
            data = request.get_json()
            sender_id = data["sender_id"]
            talk_id = data["talk_id"]
            dialog_id = data["dialog_id"]
            message_type = data["message_type"]
            value = data['value']

            message = Message(sender=sender_id, type=message_type, value=value, date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
            db.session.add(message)
            db.session.commit()

            talk = db.session.query(Talk).filter_by(id=talk_id).first_or_404()
            talk.messages = add_to_json(talk.messages, message.id)

            dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
            dialog.date_update = str(datetime.datetime.utcnow() + datetime.timedelta(hours=3))
            db.session.commit()

            users = db.session.query(User).all()
            for user in users:
                dialogs_ids = json.loads(user.dialogs)
                if dialog.id in dialogs_ids:

                    unread_dialogs_list = json.loads(user.unread_dialogs)

                    if user.id != sender_id:
                        if str(dialog.id) in unread_dialogs_list:
                            unread_dialogs_list[str(dialog.id)] += 1
                        else:
                            unread_dialogs_list[str(dialog.id)] = 1

                    user.unread_dialogs = json.dumps(unread_dialogs_list)
                    db.session.commit()

                    type_message = 'text'
                    if message.type == 'media':
                        media = db.session.query(Media).filter_by(id=message.value).first_or_404()
                        type_message = media.name

                    if str(user.id) in rooms_list:
                        """ and user.id != sender_id """

                        emit('socket_info', {'info': 'new Messages in dialog',
                                             'dialog_id': dialog.id,
                                             'message_id': message.id,
                                             'sender': sender_id,
                                             'type': type_message,
                                             'date': str(datetime.datetime.fromisoformat(message.date_create).time().strftime("%H:%M")),
                                             'value': value,
                                             'unread_count': unread_dialogs_list[str(dialog.id)] if user.id != sender_id else 0},
                             to=str(user.id), namespace='/')

            return jsonify({"status": 0,
                            "id": message.id,
                            "date": str(datetime.datetime.fromisoformat(message.date_create).time().strftime("%H:%M"))})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/get_talks', methods=['GET'])
def get_talks():
    if request.method == "GET":
        try:
            dialog_id = request.args.get("dialog_id")
            dialog = db.session.query(Dialog).filter_by(id=dialog_id).first_or_404()
            talks_ids = json.loads(dialog.talks)

            user_id = int(current_user.get_id())
            user = db.session.query(User).filter_by(id=user_id).first_or_404()

            talks = db.session.query(Talk).filter(Talk.id.in_(talks_ids)).order_by(Talk.id.desc()).all()
            response_list = list({"id": talk.id, "title": talk.title, "date": talk.date_create} for talk in talks)

            unread_dialogs_list = json.loads(user.unread_dialogs)
            if str(dialog_id) in unread_dialogs_list:
                unread_dialogs_list.pop(str(dialog_id))

            user.unread_dialogs = json.dumps(unread_dialogs_list)
            db.session.commit()

            return jsonify({"status": 0, "talks": response_list})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/get_messages', methods=['GET'])
def get_messages():
    if request.method == "GET":
        try:
            talk_id = request.args.get("talk_id")
            talk = db.session.query(Talk).filter_by(id=talk_id).first_or_404()
            messages_ids = json.loads(talk.messages)

            messages = db.session.query(Message).filter(Message.id.in_(messages_ids)).order_by(Message.id).all()

            response_list = []
            for message in messages:
                type_message = 'text'
                if message.type == 'media':
                    media = db.session.query(Media).filter_by(id=message.value).first_or_404()
                    type_message = media.name

                response_list.append({"id": message.id,
                                      "sender": message.sender,
                                      "type": type_message,
                                      "value": message.value,
                                      "date": str(datetime.datetime.fromisoformat(message.date_create).time().strftime("%H:%M"))})

            return jsonify({"status": 0, "messages": response_list})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/get_file', methods=['GET'])
def get_file():
    if request.method == "GET":
        try:
            file_id = request.args.get("file_id")
            file_purpose = request.args.get("purpose")

            media = db.session.query(Media).filter_by(id=file_id).first_or_404()

            if file_purpose == 'avatar' and media.name == 'image':

                original_image = Image.open(io.BytesIO(media.data))
                # w, h = original_image.size

                resized_image = original_image.resize((45, 45))
                img_byte_arr = io.BytesIO()
                resized_image.save(img_byte_arr, 'jpeg' if media.type == 'jpg' else media.type)
                data = img_byte_arr.getvalue()

                # if w != 45 or w != 45:
                #     original_image = Image.open(io.BytesIO(media.data))
                #     resized_image = original_image.resize((45, 45))
                #     img_byte_arr = io.BytesIO()
                #     resized_image.save(img_byte_arr, 'jpeg' if media.type == 'jpg' else media.type)
                #     media.data = img_byte_arr.getvalue()
                #     db.session.commit()

                return send_file(io.BytesIO(data), attachment_filename=(media.name + "." + media.type))

            return send_file(io.BytesIO(media.data), attachment_filename=(media.name + "." + media.type))

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    if request.method == "POST":
        try:
            user_id = current_user.get_id()
            user = db.session.query(User).filter_by(id=user_id).first_or_404()
            file = request.files["file"]
            allowed_extension = ['txt', 'png', 'jpg', 'jpeg']

            if file and '.' in file.filename:
                filename = secure_filename(file.filename)
                split_name = filename.rsplit('.', 1)

                if split_name[1] in allowed_extension:
                    media = Media(name=split_name[0], type=split_name[1], data=file.read(), date_create=str(datetime.datetime.utcnow() + datetime.timedelta(hours=3)))
                    db.session.add(media)
                    db.session.commit()
                    user.avatar_id = media.id
                    db.session.commit()

                    return jsonify({"status": 0, "info": "successful", "avatar_id": media.id})

            return jsonify({"status": 1, "info": "invalid file"})

        except Exception as e:
            return jsonify({"status": 666, "info": str(e) + traceback.format_exc()})


# @app.route('/upload_file', methods=['POST'])
# def upload_file():
#     if request.method == 'POST':
#         allowed_extension = {'txt', 'png', 'jpg', 'jpeg'}
#         response_list = []
#
#         for message in allowed_extension:
#             if message.type == "text":
#                 value = message.value
#             else:
#                 media = db.session.query(Media).filter_by(id=12).first()
#                 value = send_file(io.BytesIO(media.data), attachment_filename=(media.name + "." + media.type))
#
#         # file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(media.id) + "." + split_name[1]))
#         # media = db.session.query(Media).filter_by(id=12).first()
#         # return send_file(io.BytesIO(media.data), attachment_filename=(media.name + "." + media.type))
#
#         return jsonify({"status": 0, "info": "successful"})
#     else:
#         return jsonify({"status": 1, "info": "invalid file"})


@app.route('/reset_password', methods=['POST'])
def reset_password():
    if request.method == "POST":
        data = request.get_json()
        email = data["email"]

        token = token_key.dumps(email)
        msg = Mesage('Password Recovery - Talk Messenger', sender="talk", recipients=[email])
        link = url_for('confirm_token', token=str(token), _external=True)
        msg.body = 'Click this link to verify your account on Talk Messenger: ' + link
        mail.send(msg)

        user = db.session.query(User).filter_by(id=user_id).first_or_404()


@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')

