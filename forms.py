from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Regexp, Email, Length, EqualTo


class AddDomainForm(FlaskForm):
    new_domain = StringField('New Domain', validators=[
        DataRequired(message="Domain is required"),
        Regexp(
            r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$',
            message="Invalid domain format"
        )
    ])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=50, message="Username must be between 3 and 50 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=50, message="Username must be between 3 and 50 characters"),
        Regexp(
            r'^[a-zA-Z0-9_-]+$',
            message="Username can only contain letters, numbers, underscores, and hyphens"
        )
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters"),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$',
            message="Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character"
        )
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    role = SelectField('Role', choices=[
        ('user', 'Standard User'),
        ('admin', 'Administrator')
    ], validators=[DataRequired(message="Role is required")])
    submit = SubmitField('Register')
