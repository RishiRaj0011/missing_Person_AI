from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file, abort
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, Case, SystemLog, AdminMessage, Announcement, BlogPost, FAQ, AISettings, Sighting
from sqlalchemy import func, desc, and_, or_, case
from datetime import datetime, timedelta, date
import csv
import io
import json

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    # Basic statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_cases = Case.query.count()
    total_sightings = Sighting.query.count()
    
    # Status distribution
    status_counts = db.session.query(Case.status, func.count(Case.id)).group_by(Case.status).all()
    
    # Time-based analytics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    daily_cases = (
        db.session.query(
            func.date(Case.created_at).label("date"), 
            func.count(Case.id).label("count")
        )
        .filter(Case.created_at >= thirty_days_ago)
        .group_by(func.date(Case.created_at))
        .all()
    )
    
    # AI Performance metrics
    avg_processing_time = db.session.query(
        func.avg(func.extract('epoch', Case.updated_at - Case.created_at))
    ).filter(Case.status.in_(['Completed', 'Active'])).scalar() or 0
    
    high_confidence_matches = Sighting.query.filter(Sighting.confidence_score > 0.8).count()
    
    # Geographic data (top locations)
    location_stats = (
        db.session.query(
            Case.last_seen_location,
            func.count(Case.id).label('case_count')
        )
        .filter(Case.last_seen_location.isnot(None))
        .group_by(Case.last_seen_location)
        .order_by(desc('case_count'))
        .limit(10)
        .all()
    )
    
    # Recent activity
    recent_logs = SystemLog.query.order_by(desc(SystemLog.timestamp)).limit(10).all()
    
    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        active_users=active_users,
        total_cases=total_cases,
        total_sightings=total_sightings,
        status_counts=status_counts,
        daily_cases=daily_cases,
        avg_processing_time=avg_processing_time,
        high_confidence_matches=high_confidence_matches,
        location_stats=location_stats,
        recent_logs=recent_logs
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    role_filter = request.args.get('role', '')
    sort_by = request.args.get('sort', 'created_at')
    sort_order = request.args.get('order', 'desc')
    
    query = User.query
    
    # Apply search filter
    if search:
        query = query.filter(or_(
            User.username.contains(search),
            User.email.contains(search)
        ))
    
    # Apply status filter
    if status_filter == 'active':
        query = query.filter(User.last_login.isnot(None))
    elif status_filter == 'inactive':
        query = query.filter(User.last_login.is_(None))
    
    # Apply role filter
    if role_filter == 'admin':
        query = query.filter(User.is_admin == True)
    elif role_filter == 'user':
        query = query.filter(User.is_admin == False)
    
    # Apply sorting
    if sort_by == 'username':
        sort_column = User.username
    elif sort_by == 'email':
        sort_column = User.email
    elif sort_by == 'last_login':
        sort_column = User.last_login
    else:
        sort_column = User.created_at
    
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    users = query.paginate(page=page, per_page=20, error_out=False)
    
    # Calculate statistics
    total_cases_on_page = sum(len(user.cases) for user in users.items)
    active_users = User.query.filter(User.last_login.isnot(None)).count()
    admin_users = User.query.filter(User.is_admin == True).count()
    
    return render_template(
        "admin/users.html", 
        users=users, 
        search=search,
        status_filter=status_filter,
        role_filter=role_filter,
        sort_by=sort_by,
        sort_order=sort_order,
        total_cases=total_cases_on_page,
        active_users=active_users,
        admin_users=admin_users
    )


@admin_bp.route("/users/<int:user_id>/toggle_admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Cannot modify your own admin status")
        return redirect(url_for("admin.users"))

    user.is_admin = not user.is_admin
    db.session.commit()
    flash(
        f'Admin status {"granted" if user.is_admin else "revoked"} for {user.username}'
    )
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("Cannot delete your own account")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.username} deleted successfully")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    
    # Calculate total sightings across all user's cases
    total_sightings = sum(len(case.sightings) for case in user.cases)
    
    # Get recent activity logs for this user
    activity_logs = SystemLog.query.filter_by(user_id=user_id).order_by(desc(SystemLog.timestamp)).limit(10).all()
    
    return render_template(
        "admin/user_detail.html", 
        user=user, 
        total_sightings=total_sightings,
        activity_logs=activity_logs
    )


@admin_bp.route("/impersonate/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def impersonate_user(user_id):
    from flask_login import logout_user, login_user
    from flask import session
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot impersonate yourself'}), 400
    
    # Store admin user ID for later restoration
    session['impersonating_admin_id'] = current_user.id
    session['is_impersonating'] = True
    
    # Log the impersonation
    log = SystemLog(
        user_id=user_id,
        action='admin_impersonation',
        details=f'Admin {current_user.username} logged in as {user.username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    login_user(user)
    
    return jsonify({'success': True})


@admin_bp.route("/stop_impersonation", methods=["POST"])
@login_required
def stop_impersonation():
    from flask_login import logout_user, login_user
    from flask import session
    
    if not session.get('is_impersonating'):
        return jsonify({'error': 'Not currently impersonating'}), 400
    
    admin_id = session.get('impersonating_admin_id')
    if not admin_id:
        return jsonify({'error': 'Admin ID not found'}), 400
    
    admin_user = User.query.get(admin_id)
    if not admin_user:
        return jsonify({'error': 'Admin user not found'}), 400
    
    # Log the end of impersonation
    log = SystemLog(
        user_id=admin_id,
        action='admin_impersonation_end',
        details=f'Admin {admin_user.username} stopped impersonating {current_user.username}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    login_user(admin_user)
    
    session.pop('impersonating_admin_id', None)
    session.pop('is_impersonating', None)
    
    return jsonify({'success': True})


@admin_bp.route("/cases")
@login_required
@admin_required
def cases():
    cases = Case.query.order_by(Case.created_at.desc()).all()
    return render_template("admin/cases.html", cases=cases)


@admin_bp.route("/cases/<int:case_id>")
@login_required
@admin_required
def case_detail(case_id):
    case = Case.query.get_or_404(case_id)
    logs = (
        SystemLog.query.filter_by(case_id=case_id)
        .order_by(SystemLog.timestamp.desc())
        .all()
    )
    return render_template("admin/case_detail.html", case=case, logs=logs)


@admin_bp.route("/cases/<int:case_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_case(case_id):
    case = Case.query.get_or_404(case_id)
    db.session.delete(case)
    db.session.commit()
    flash(f"Case for {case.person_name} deleted successfully")
    return redirect(url_for("admin.cases"))


@admin_bp.route("/cases/<int:case_id>/requeue", methods=["POST"])
@login_required
@admin_required
def requeue_case(case_id):
    case = Case.query.get_or_404(case_id)
    case.status = "Queued"
    case.completed_at = None
    db.session.commit()

    from app.tasks import process_case
    process_case.delay(case_id)

    flash(f"Case for {case.person_name} re-queued for processing")
    return redirect(url_for("admin.case_detail", case_id=case_id))


# ===== ADVANCED ADMIN FEATURES =====

# Data Export Routes
@admin_bp.route("/export/users")
@login_required
@admin_required
def export_users():
    users = User.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    # CSV headers
    writer.writerow(['ID', 'Username', 'Email', 'Is Admin', 'Active', 'Cases Count', 'Created At', 'Last Login', 'Location'])
    
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.is_admin,
            user.is_active,
            len(user.cases),
            user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never',
            user.location or 'Not specified'
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@admin_bp.route("/export/cases")
@login_required
@admin_required
def export_cases():
    cases = Case.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['ID', 'Person Name', 'Age', 'Status', 'Priority', 'Creator', 'Location', 'Sightings', 'Created At'])
    
    for case in cases:
        writer.writerow([
            case.id,
            case.person_name,
            case.age or 'Unknown',
            case.status,
            case.priority,
            case.creator.username,
            case.last_seen_location or 'Not specified',
            case.total_sightings,
            case.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'cases_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


# Analytics Routes
@admin_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    # AI Performance Analytics
    processing_stats = db.session.query(
        Case.status,
        func.count(Case.id).label('count'),
        func.avg(func.extract('epoch', Case.updated_at - Case.created_at)).label('avg_time')
    ).group_by(Case.status).all()
    
    # Confidence score distribution - SQLite compatible
    whens = {
        'Very High (90%+)': Sighting.confidence_score >= 0.90,
        'High (80-89%)': Sighting.confidence_score.between(0.80, 0.899),
        'Medium (60-79%)': Sighting.confidence_score.between(0.60, 0.799),
        'Low (40-59%)': Sighting.confidence_score.between(0.40, 0.599),
    }
    
    confidence_case_statement = case(whens, else_='Very Low (<40%)').label('confidence_range')
    
    confidence_distribution = db.session.query(
        confidence_case_statement,
        func.count(Sighting.id).label('count')
    ).group_by(confidence_case_statement).all()
    
    # Geographic heat map data
    location_data = db.session.query(
        Case.last_seen_location,
        func.count(Case.id).label('case_count')
    ).filter(Case.last_seen_location.isnot(None)).group_by(Case.last_seen_location).all()
    
    return render_template(
        "admin/analytics.html",
        processing_stats=processing_stats,
        confidence_distribution=confidence_distribution,
        location_data=location_data
    )


# User Messaging System
@admin_bp.route("/messages")
@login_required
@admin_required
def messages():
    sent_messages = AdminMessage.query.filter_by(sender_id=current_user.id).order_by(desc(AdminMessage.created_at)).all()
    return render_template("admin/messages.html", sent_messages=sent_messages)


@admin_bp.route("/messages/send/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def send_message(user_id):
    from app.models import Notification
    user = User.query.get_or_404(user_id)
    
    if request.method == "POST":
        subject = request.form.get('subject')
        content = request.form.get('content')
        message_type = request.form.get('type', 'info')
        
        # Create admin message record
        message = AdminMessage(
            sender_id=current_user.id,
            recipient_id=user_id,
            subject=subject,
            content=content
        )
        db.session.add(message)
        
        # Create notification for user
        notification = Notification(
            user_id=user_id,
            sender_id=current_user.id,
            title=subject,
            message=content,
            type=message_type
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f"Message sent to {user.username} successfully!", "success")
        return redirect(url_for("admin.users"))
    
    return render_template("admin/send_message.html", user=user)


# Announcement Management
@admin_bp.route("/announcements")
@login_required
@admin_required
def announcements():
    announcements = Announcement.query.order_by(desc(Announcement.created_at)).all()
    return render_template("admin/announcements.html", announcements=announcements)


@admin_bp.route("/announcements/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_announcement():
    # Calculate tomorrow's date
    tomorrow = date.today() + timedelta(days=1)
    
    if request.method == "POST":
        title = request.form.get('title')
        content = request.form.get('content')
        type = request.form.get('type', 'info')
        expires_at = request.form.get('expires_at')
        
        announcement = Announcement(
            title=title,
            content=content,
            type=type,
            created_by=current_user.id,
            expires_at=datetime.strptime(expires_at, '%Y-%m-%d') if expires_at else None
        )
        db.session.add(announcement)
        db.session.commit()
        
        flash("Announcement created successfully!", "success")
        return redirect(url_for("admin.announcements"))
    
    return render_template("admin/create_announcement.html", tomorrow=tomorrow)


@admin_bp.route("/announcements/<int:announcement_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    
    status = "activated" if announcement.is_active else "deactivated"
    flash(f"Announcement {status} successfully!", "success")
    return redirect(url_for("admin.announcements"))


# AI Settings Management
@admin_bp.route("/ai-settings")
@login_required
@admin_required
def ai_settings():
    settings = AISettings.query.all()
    
    # Initialize default settings if none exist
    if not settings:
        default_settings = [
            ('confidence_threshold', '0.7', 'Minimum confidence score for matches'),
            ('max_processing_time', '300', 'Maximum processing time per video (seconds)'),
            ('face_detection_model', 'hog', 'Face detection model (hog/cnn)'),
            ('enable_clothing_analysis', 'true', 'Enable clothing-based matching')
        ]
        
        for name, value, desc in default_settings:
            setting = AISettings(setting_name=name, setting_value=value, description=desc, updated_by=current_user.id)
            db.session.add(setting)
        
        db.session.commit()
        settings = AISettings.query.all()
    
    return render_template("admin/ai_settings.html", settings=settings)


@admin_bp.route("/ai-settings", methods=["POST"])
@login_required
@admin_required
def update_ai_settings():
    """Handle AI settings form submission"""
    for setting_id, value in request.form.items():
        if setting_id.startswith('setting_'):
            setting_id = setting_id.replace('setting_', '')
            setting = AISettings.query.get(setting_id)
            if setting:
                setting.setting_value = value
                setting.updated_by = current_user.id
                setting.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash("AI settings updated successfully!", "success")
    return redirect(url_for("admin.ai_settings"))


# Content Management
@admin_bp.route("/content")
@login_required
@admin_required
def content_management():
    blog_posts = BlogPost.query.order_by(desc(BlogPost.created_at)).limit(5).all()
    faqs = FAQ.query.order_by(FAQ.order, FAQ.id).all()
    return render_template("admin/content_management.html", blog_posts=blog_posts, faqs=faqs)


@admin_bp.route("/content/faq/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_faq():
    if request.method == "POST":
        question = request.form.get('question')
        answer = request.form.get('answer')
        category = request.form.get('category', 'General')
        order = int(request.form.get('order', 0))
        
        faq = FAQ(
            question=question,
            answer=answer,
            category=category,
            order=order,
            created_by=current_user.id
        )
        db.session.add(faq)
        db.session.commit()
        
        flash("FAQ created successfully!", "success")
        return redirect(url_for("admin.content_management"))
    
    return render_template("admin/create_faq.html")
