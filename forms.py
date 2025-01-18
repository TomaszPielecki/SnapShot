from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp


class AddDomainForm(FlaskForm):
    new_domain = StringField('New Domain', validators=[
        DataRequired(message="Domain is required"),
        Regexp(
            r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$',
            message="Invalid domain format"
        )
    ])
    submit = SubmitField('Submit')
