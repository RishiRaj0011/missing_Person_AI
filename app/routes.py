import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps

from app import db
from app.models import User, Case, TargetImage, SearchVideo, Sighting
from app.forms import (
    RegistrationForm,
    LoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    NewCaseForm,
    ContactForm,
)

# File validation helper functions
def _is_allowed_image_file(filename):
    """Check if uploaded file is an allowed image type"""
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def _is_allowed_video_file(filename):
    """Check if uploaded file is an allowed video type"""
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

# Authorization helper functions
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def case_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        case_id = kwargs.get('case_id')
        if case_id:
            case = Case.query.get_or_404(case_id)
            if case.user_id != current_user.id and not current_user.is_admin:
                abort(403)
        return f(*args, **kwargs)
    return decorated_function

# The 'process_case' import is moved inside the function to prevent a circular import.

# This 'bp' variable is what the error is looking for.
bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    """Public landing page for all visitors"""
    return render_template("index.html")


@bp.route("/dashboard")
@login_required
def dashboard():
    """Secure dashboard for authenticated users"""
    # Get user statistics
    user_cases = Case.query.filter_by(user_id=current_user.id).all()
    total_cases = len(user_cases)
    active_cases = len([c for c in user_cases if c.status in ['Queued', 'Processing']])
    completed_cases = len([c for c in user_cases if c.status == 'Completed'])
    total_sightings = sum(len(c.sightings) for c in user_cases)
    
    # Get recent cases (last 5)
    recent_cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.created_at.desc()).limit(5).all()
    
    user_stats = {
        'total_cases': total_cases,
        'active_cases': active_cases,
        'completed_cases': completed_cases,
        'total_sightings': total_sightings
    }
    
    return render_template('dashboard.html', user_stats=user_stats, recent_cases=recent_cases)


@bp.route("/register_case", methods=["GET", "POST"])
@login_required
def register_case():
    form = NewCaseForm()
    if form.validate_on_submit():
        # Create new case with comprehensive data
        new_case = Case(
            person_name=form.full_name.data,
            age=form.age.data,
            details=f"Nickname: {form.nickname.data or 'N/A'}\n"
                   f"Gender: {form.gender.data}\n"
                   f"Height: {form.height_cm.data}cm\n"
                   f"Weight: {form.weight_kg.data}kg\n"
                   f"Distinguishing Marks: {form.distinguishing_marks.data}\n"
                   f"Contact Person: {form.contact_person_name.data}\n"
                   f"Contact Phone: {form.contact_person_phone.data}\n"
                   f"Contact Email: {form.contact_person_email.data}\n"
                   f"Additional Info: {form.additional_info.data or 'None'}",
            last_seen_location=form.last_seen_location.data,
            date_missing=form.last_seen_date.data,
            priority="High",  # Default priority for new comprehensive form
            user_id=current_user.id,
        )
        db.session.add(new_case)
        db.session.commit()

        # Handle multiple photo uploads with enhanced security
        photo_files = request.files.getlist("photos")
        for photo_file in photo_files:
            if photo_file and photo_file.filename != "":
                # Validate file type
                if not _is_allowed_image_file(photo_file.filename):
                    flash(f"Invalid image file type: {photo_file.filename}", "error")
                    continue
                
                # Create secure unique filename
                from app.utils import sanitize_filename
                original_filename = sanitize_filename(photo_file.filename)
                if not original_filename:
                    flash("Invalid filename", "error")
                    continue
                
                # Generate unique filename to prevent conflicts
                from app.utils import create_safe_filename
                file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'jpg'
                unique_filename = create_safe_filename(f"case_{new_case.id}_photo", file_ext)
                
                # Ensure uploads directory exists
                upload_dir = os.path.join("app", "static", "uploads")
                os.makedirs(upload_dir, exist_ok=True)
                
                save_path = os.path.join(upload_dir, unique_filename)
                
                # Validate file size (already handled by Flask config, but double-check)
                photo_file.seek(0, 2)  # Seek to end
                file_size = photo_file.tell()
                photo_file.seek(0)  # Reset to beginning
                
                if file_size > 16 * 1024 * 1024:  # 16MB limit
                    flash(f"File too large: {original_filename}", "error")
                    continue
                
                photo_file.save(save_path)
                
                # Validate file content after upload
                from app.utils import validate_file_content
                if not validate_file_content(save_path, 'image'):
                    os.remove(save_path)  # Remove invalid file
                    flash(f"Invalid image file content: {original_filename}", "error")
                    continue
                
                db_path = os.path.join("static", "uploads", unique_filename).replace("\\", "/")
                target_image = TargetImage(case_id=new_case.id, image_path=db_path)
                db.session.add(target_image)

        # Handle optional video upload with enhanced security
        video_file = form.video.data
        if video_file and video_file.filename != "":
            # Validate file type
            if not _is_allowed_video_file(video_file.filename):
                flash(f"Invalid video file type: {video_file.filename}", "error")
            else:
                # Create secure unique filename
                from app.utils import sanitize_filename
                original_filename = sanitize_filename(video_file.filename)
                if not original_filename:
                    flash("Invalid video filename", "error")
                else:
                    # Generate unique filename to prevent conflicts
                    from app.utils import create_safe_filename
                    file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'mp4'
                    unique_filename = create_safe_filename(f"case_{new_case.id}_video", file_ext)
                    
                    upload_dir = os.path.join("app", "static", "uploads")
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    save_path = os.path.join(upload_dir, unique_filename)
                    
                    # Validate file size
                    video_file.seek(0, 2)
                    file_size = video_file.tell()
                    video_file.seek(0)
                    
                    if file_size > 100 * 1024 * 1024:  # 100MB limit for videos
                        flash(f"Video file too large: {original_filename}", "error")
                    else:
                        video_file.save(save_path)
                        
                        # Validate file content after upload
                        from app.utils import validate_file_content
                        if not validate_file_content(save_path, 'video'):
                            os.remove(save_path)  # Remove invalid file
                            flash(f"Invalid video file content: {original_filename}", "error")
                        else:
                            db_path = os.path.join("static", "uploads", unique_filename).replace("\\", "/")
                            search_video = SearchVideo(case_id=new_case.id, video_path=db_path, video_name=original_filename)
                            db.session.add(search_video)

        db.session.commit()

        # Process the case with AI
        from app.tasks import process_case
        process_case.delay(new_case.id)

        flash("Missing person case has been successfully registered and is now being processed by our AI system!", "success")
        return redirect(url_for("main.profile"))

    return render_template("register_case.html", title="Register Missing Person Case", form=form)


# ... (The rest of the file is the same, including all other routes)





@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Account created successfully!")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("main.login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("main.dashboard"))
    return render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash(
                "Password reset link would be sent to your email (email sending not implemented)."
            )
        else:
            flash("Email not found")
        return redirect(url_for("main.login"))
    return render_template("forgot_password.html", form=form)


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    user = User.verify_reset_token(token)
    if not user:
        flash("Invalid or expired token")
        return redirect(url_for("main.forgot_password"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Password has been reset successfully")
        return redirect(url_for("main.login"))
    return render_template("reset_password.html", form=form)


@bp.route("/profile")
@login_required
def profile():
    cases = Case.query.filter_by(user_id=current_user.id).order_by(Case.id.desc()).all()
    return render_template("profile.html", cases=cases)


@bp.route("/case/<int:case_id>")
@login_required
@case_owner_required
def case_details(case_id):
    """View detailed information about a specific case"""
    case = Case.query.get_or_404(case_id)
    return render_template("case_details.html", case=case)

@bp.route("/case/<int:case_id>/withdraw", methods=["POST"])
@login_required
@case_owner_required
def withdraw_case(case_id):
    """Withdraw a case - change status to Withdrawn"""
    case = Case.query.get_or_404(case_id)
    
    if case.status in ['Resolved', 'Withdrawn']:
        flash(f"Cannot withdraw a case that is already {case.status.lower()}.", "warning")
    else:
        case.status = 'Withdrawn'
        case.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f"Case for {case.person_name} has been successfully withdrawn.", "success")
    
    return redirect(url_for("main.dashboard"))

@bp.route("/case_status/<int:case_id>")
@login_required
@case_owner_required
def case_status(case_id):
    case = Case.query.get_or_404(case_id)
    sightings = []
    for s in case.sightings:
        video_name = (
            s.search_video.video_path.split("/")[-1] if s.search_video else "N/A"
        )
        sightings.append(
            {
                "video_name": video_name,
                "timestamp": s.timestamp,
                "confidence_score": round(s.confidence_score, 2),
                "thumbnail_path": url_for(
                    "static", filename=s.thumbnail_path.replace("static\\", "/")
                ),
            }
        )
    response_data = {"status": case.status, "sightings": sightings}
    return jsonify(response_data)








@bp.route("/notifications")
@login_required
def notifications():
    """User notifications page"""
    from app.models import Notification
    
    # Get all notifications for current user, ordered by newest first
    user_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).all()
    
    # Mark all notifications as read
    Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    
    return render_template("notifications.html", 
                         title="Notifications", 
                         notifications=user_notifications)


@bp.route("/missing_persons")
@login_required
def missing_persons():
    """Public directory of missing persons cases"""
    cases = Case.query.filter(Case.status.in_(['Queued', 'Processing', 'Completed'])).order_by(Case.created_at.desc()).all()
    return render_template("missing_persons.html", cases=cases, title="Missing Persons Directory")


@bp.route("/about")
@login_required
def about():
    """About page - detailed platform information"""
    return render_template("about.html", title="About the Platform")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page - available to all users"""
    form = ContactForm()
    
    # Pre-populate form with user data if logged in
    if current_user.is_authenticated and request.method == "GET":
        form.name.data = current_user.username
        form.email.data = current_user.email
    
    if form.validate_on_submit():
        flash("Thank you for your message! We will get back to you shortly.", "success")
        return redirect(url_for("main.contact"))
    
    return render_template("contact.html", title="Contact & Help", form=form)
