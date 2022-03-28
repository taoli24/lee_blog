from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField


class PostForm(FlaskForm):
    title = StringField(label='Blog Post Title', validators=[DataRequired()], render_kw={'class': 'my-2'})
    subtitle = StringField(label='Subtitle', validators=[DataRequired()], render_kw={'class': 'my-2'})
    image = StringField(label='Blog Image URL', validators=[DataRequired(), URL()], render_kw={'class': 'my-2'})
    body = CKEditorField(label='Blog Content', validators=[DataRequired()], render_kw={'class': 'my-2'})
    submit = SubmitField(label='Submit Post', render_kw={'class': 'btn btn-primary text-uppercase my-2'})


class UserRegisterForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired(), Length(min=10)])
    name = StringField(label='Name', validators=[DataRequired()])
    submit = SubmitField(label='SIGN ME UP', render_kw={'class': 'mt-3'})


class LoginForm(FlaskForm):
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='LET ME IN', render_kw={'class': 'mt-3'})


class CommentForm(FlaskForm):
    comment = CKEditorField(label='Comment', validators=[DataRequired()])
    submit = SubmitField(label='SUBMIT COMMENT', render_kw={'class': 'mt-3'})
