from app import app, db
from flask import render_template, url_for, redirect, flash, request
from app.forms import LoginForm, RegistrationForm, PostForm, EditProfileForm, EmptyForm, PasswordReset, PasswordResetRequest, SendMessage, SendMessageChat
from flask_login import login_user, current_user, login_required, logout_user, fresh_login_required
from app.models import User, Post, Message, Notification
from sqlalchemy import select, func
from urllib.parse import urlsplit
from datetime import datetime, timezone


@app.before_request
def last_seen():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/', methods=["GET", "POST"])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    posts = db.session.scalars(current_user.following_posts()).all()
    return render_template('index.html', form=form, title='home', posts=posts)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        query = select(User).where(User.username == form.username.data)
        user = db.session.scalar(query)
        if user is None or not user.check_password_hash(form.password.data):
            flash('Username or password is incorrect.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next = request.args.get('next')
        if not next or urlsplit(next).netloc != '':
            return redirect(url_for('index'))
        return redirect(url_for(next))
    return render_template('login.html', form=form, title='Log In')
        

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password_hash(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations! Your account has been created. Pleas log in with your username and password.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, title='register')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/profile/<username>', methods=["GET", "POST"])
def profile(username):
    user = db.first_or_404(select(User).where(User.username==username))
    form = EmptyForm()
    posts = db.session.scalars(user.posts.select()).all()
    return render_template('profile.html', title='User Profile', user=user, posts=posts, form=form)


@app.route('/edit_profile', methods=["GET", "POST"])
def edit_profile():
    form = EditProfileForm(current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your changes has been saved.")
        return redirect(url_for('index'))
    if request.method == "GET":
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', user=current_user, form=form)


@app.route('/follow/<username>', methods=["POST"])
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} does not exist!')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You can not follow youself!')
            return redirect(url_for('index'))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are now following {username}')
        return redirect(url_for('profile', username=username))
    return redirect(url_for('profile', username=username))


@app.route('/unfollow/<username>', methods=["POST"])
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} does not exist.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You can not unfollow youself.')
            return redirect(url_for('index'))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You unfollowed {username}.')
        return redirect(url_for('profile', username=username))
    return redirect(url_for('profile', username=username))


@app.route('/explore')
@login_required
def explore():
    query = select(Post).order_by(Post.timstamp.desc())
    page = request.args.get('page', 1, type=int)
    posts = db.paginate(query, page=page, per_page=app.config['POST_PER_PAGE'], error_out=False)
    if page > posts.pages:
        flash(f"Max page number is {posts.pages}")
        prev_page = url_for('explore', page=posts.pages)
        next_page = None
    else:
        next_page = url_for('explore', page=posts.next_num) if posts.has_next else None
        prev_page = url_for('explore', page=posts.prev_num) if posts.has_prev else None
    return render_template('explore.html', title='Explore', posts=posts.items, next_page=next_page, prev_page=prev_page)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    token = request.args.get('token')
    if token is None:
        form = PasswordResetRequest()
        if form.validate_on_submit():
            user = db.session.scalar(select(User).where(User.email == form.email.data))
            if user is None:
                flash('Email address is incorrect!')
                return redirect('reset_password')
            user.send_password_reset_email()
            flash(f'An email has been sent to {user.email}')
            return redirect('login')
        return render_template('reset_password_request.html', title='Reset Password Request', form=form)
    user = User.validate_password_reset_token(token)
    if user is None:
        flash('Token is incorrect!')
        return redirect(url_for('index'))
    form = PasswordReset()
    if form.validate_on_submit():
        user.set_password_hash(form.password.data)
        db.session.commit()
        flash('Your password changed successfully.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Reset your password', form=form)


@app.route('/send_message/<username>', methods=["GET", "POST"])
@login_required
def send_message(username):
    if username == current_user.username:
        flash('You can\'t send youself a message')
        return redirect(url_for('index'))
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        flash('User not found!')
        return redirect(url_for('index'))
    form = SendMessage()
    if form.validate_on_submit():
        message = Message(message=form.message.data, author=current_user, recipient=user)
        db.session.add(message)
        db.session.commit()
        flash(f'Your message has been sent to the user {username}')
        return redirect(url_for('profile', username=username))
    return render_template('send_message.html', title='Send a Message', form=form)


@app.route('/messages')
@login_required
def chats():
    page = request.args.get('page', 1, type=int)
    chat_list = current_user.get_chat_list()
    return render_template('chats.html', title="Private Messages", chat_list=chat_list)


@app.route('/messages/<username>', methods=["GET", "POST"])
def conversation(username):
    user = db.session.scalar(select(User).where(User.username==username))
    if user is None:
        flash(f'User {username} does not exist.')
        return redirect(url_for('index'))
    if user == current_user:
        flash(f'You can\'t send a message to yourself!')
        return redirect(url_for('index'))
    form = SendMessageChat()

    messages = current_user.get_conversation(user)

    for message in messages:
        if message.author == user:
            message.is_read = True
    db.session.commit()

    current_user.add_notification(name='unread_message_count', data=current_user.get_unread_message_count())
    
    db.session.commit() 
    if form.validate_on_submit():
        message = Message(message=form.message.data, author=current_user, recipient=user)
        db.session.add(message)
        user.add_notification('unread_message_count', user.get_unread_message_count())
        db.session.commit()
        return redirect(url_for('conversation', username=user.username))
    
    return render_template('conversation.html', title='Conversation', messages=messages, username=username, form=form)


@app.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query).all()
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]


@app.errorhandler(404)
def not_found_error(error):
    return render_template('not_found.html'), 404

