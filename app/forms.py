from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, 
    IntegerField, 
    TextAreaField, 
    DateTimeField, 
    SubmitField, 
    PasswordField, 
    BooleanField, 
    SelectField, 
    DateField, 
    EmailField,
    MultipleFileField
)
from wtforms.validators import DataRequired, Optional, Email, EqualTo, Length, ValidationError, NumberRange, Regexp
from app.models import User

# Custom file validators
def validate_image_file(form, field):
    """Custom validator for image files"""
    if field.data:
        filename = field.data.filename
        if not filename:
            raise ValidationError('No file selected')
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            raise ValidationError('Invalid file type. Only PNG, JPG, JPEG, GIF, BMP, and WEBP files are allowed.')

def validate_video_file(form, field):
    """Custom validator for video files"""
    if field.data:
        filename = field.data.filename
        if not filename:
            return  # Optional field
        
        allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
        if not ('.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            raise ValidationError('Invalid file type. Only MP4, AVI, MOV, MKV, WMV, FLV, and WEBM files are allowed.')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class NewCaseForm(FlaskForm):
    # Section 1: Personal Details
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    nickname = StringField('Nickname (Optional)', validators=[Optional(), Length(max=50)])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=0, max=120)])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other'), ('prefer_not_to_say', 'Prefer not to say')], validators=[DataRequired()])
    
    # Section 2: Physical Characteristics
    height_cm = IntegerField('Height (cm)', validators=[DataRequired(), NumberRange(min=30, max=250)])
    weight_kg = IntegerField('Weight (kg)', validators=[DataRequired(), NumberRange(min=2, max=300)])
    distinguishing_marks = TextAreaField('Distinguishing Marks', validators=[DataRequired(), Length(min=10, max=500)], render_kw={'placeholder': 'e.g., Scar on left cheek, tattoo of a rose on right arm, birthmark on forehead'})
    
    # Section 3: Contact Information (of the reporter)
    contact_person_name = StringField('Your Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    contact_person_phone = StringField('Your Phone Number', validators=[DataRequired(), Regexp(r'^[\+]?[1-9]?\d{9,15}$', message='Please enter a valid phone number')])
    contact_person_email = EmailField('Your Email Address', validators=[DataRequired(), Email()])
    
    # Section 4: Case Details
    last_seen_date = DateField('Last Seen Date', validators=[DataRequired()])
    last_seen_location = StringField('Last Seen Location', validators=[DataRequired(), Length(min=5, max=200)])
    additional_info = TextAreaField('Additional Information (Optional)', validators=[Optional(), Length(max=1000)], render_kw={'placeholder': 'Any other relevant details that might help in the search...'})
    
    # Section 5: Media Uploads
    photos = MultipleFileField('Upload Photos (Multiple clear, front-facing photos are best)', validators=[DataRequired(), validate_image_file], render_kw={'accept': '.jpg,.jpeg,.png,.gif,.bmp,.webp'})
    video = FileField('Upload a Short Video (Optional, helps AI analysis)', validators=[Optional(), validate_video_file], render_kw={'accept': '.mp4,.avi,.mov,.mkv,.wmv,.flv,.webm'})
    
    submit = SubmitField('Submit Case')

class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    subject = SelectField('Subject', choices=[
        ('technical_issue', 'Technical Issue'),
        ('suggestion', 'Feedback / Suggestion'),
        ('general_inquiry', 'General Inquiry'),
        ('case_help', 'Help with My Case'),
        ('feature_request', 'Feature Request'),
        ('bug_report', 'Bug Report')
    ], validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('Send Message')

# Legacy form for backward compatibility
class RegistrationCaseForm(NewCaseForm):
    pass