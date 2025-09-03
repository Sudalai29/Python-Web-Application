from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class UserForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(), Length(max=255)])
    quote = TextAreaField('Favorite Quote', validators=[DataRequired()])
    advice = TextAreaField('Advice', validators=[DataRequired()])
    submit = SubmitField('Submit')
