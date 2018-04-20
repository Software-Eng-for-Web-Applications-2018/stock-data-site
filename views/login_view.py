# written by: Kevin Pielacki
# debugged by: Kevin Pielacki


import datetime
from app import db
from flask import (request, url_for, redirect, flash, current_app)
from flask_admin import (BaseView, expose)
from flask_login import (current_user, login_user)
from models import User
from wtforms import Form
from wtforms.fields import (DateField, HiddenField, PasswordField, StringField)
from wtforms.validators import (Length, Required, Regexp, Email)
from werkzeug.security import (generate_password_hash, check_password_hash)


class LoginForm(Form):
    email = StringField(u'Email', [Required()])
    password = PasswordField(u'Password', [Required()])
    next = HiddenField(u'Next')


class SignupForm(Form):

    email = StringField(u'Email', [Required(), Email()])
    '''Email form field.'''

    pass_len_msg = 'Must be between 7 and 50 characters long.'
    valid_pass_len = Length(min=7, max=50, message=pass_len_msg)
    '''Password length validator.'''

    pass_regex_msg = 'Password must contain at least one uppercase, ' \
                     'lowercase, and number character.'
    valid_pass= Regexp(
        '^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$',
        message=pass_regex_msg
    )
    '''Password expression validator.'''

    password = PasswordField(
        u'Password',
        [Required(), valid_pass_len, valid_pass]
    )
    '''Password form field.'''

    # Birth date field
    birth_date = DateField(
        'Birth Date',
        format='%Y-%m-%d',
        validators=[Required()]
    )
    '''Birth date form field.'''


class LoginView(BaseView):

    def is_visible(self):
        return not(current_user.is_authenticated)

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        next = request.args.get("next")
        form = LoginForm(request.form)

        # Return to portal if user already logged in
        if current_user.is_authenticated:
            return redirect('/realtimeportal')

        # Validate posted form
        if (request.method == 'POST') and form.validate():
            passwd = request.form['password']
            email = request.form['email'].lower()
            next = form.next.data
            valid_user = User.query.filter_by(email=email).first()

            if not valid_user:
                # No account found for user.
                flash('Access Denied - Must Request Access', 'error')
                return redirect(url_for('login.index', next=next))
            elif valid_user.active:
                if not check_password_hash(valid_user.password, passwd):
                    flash('Email or password is not correct.', 'error')
                    return redirect(url_for('login.index', next=next))
                else:
                    valid_user.last_login_date = datetime.datetime.now()
                    db.session.commit()
                    login_user(valid_user)
                    return redirect(request.args.get("next") or "/")
            else:
                # Account has not been activated.
                flash('Your account has not been activated yet.', 'error')
                return redirect(url_for('login.index', next=next))
        return self.render('login.html', next=next, form=form)

    @expose('/signup/', methods=('GET', 'POST'))
    def signup(self):
        form = SignupForm(request.form)

        if (request.method == 'POST') and form.validate():
            email = request.form.get('email').lower()
            pw_hash = generate_password_hash(request.form['password'])
            birth_date = request.form['birth_date']

            if User.query.filter_by(email=email).first():
                flash('You already have access.', 'error')
                return redirect(url_for('login.index'))
            elif User.query.filter_by(email=email).first():
                flash('There is already an account with that email.', 'error')
                return redirect(url_for('login.index'))
            else:
                # Add new user requesting asccess.
                new_user = User(
                    email=email,
                    password=pw_hash,
                    user_group='user',
                    active=True,
                    birth_date=birth_date,
                    last_login_date=None
                )
                db.session.add(new_user)
                db.session.commit()

                # Send email to admins.
                flash('Account Created!')
                return redirect(url_for('login.index'))
        return self.render('login.html', signup=True, form=form)
