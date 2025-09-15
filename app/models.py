from datetime import datetime, timedelta
from flask_login import UserMixin
from flask_bcrypt import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from app import db
from app.utils import sanitize_input


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    details = db.Column(db.Text)
    clothing_description = db.Column(db.Text)
    last_seen_location = db.Column(db.String(200))
    date_missing = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(
        db.String(20), default="Queued"
    )  # Queued, Processing, Active, Resolved, Withdrawn
    priority = db.Column(db.String(10), default="Medium")  # Low, Medium, High, Critical
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at = db.Column(db.DateTime)

    # Relationships
    target_images = db.relationship(
        "TargetImage", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    search_videos = db.relationship(
        "SearchVideo", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    sightings = db.relationship(
        "Sighting", backref="case", lazy=True, cascade="all, delete-orphan"
    )
    case_notes = db.relationship(
        "CaseNote", backref="case", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        safe_name = sanitize_input(self.person_name) if self.person_name else 'Unknown'
        return f"<Case {safe_name} - {self.status}>"

    @property
    def total_sightings(self):
        return len(self.sightings)

    @property
    def high_confidence_sightings(self):
        return len([s for s in self.sightings if s.confidence_score > 0.8])


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Enhanced user fields
    last_login = db.Column(db.DateTime)
    login_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    location = db.Column(db.String(200))
    
    # Relationships
    cases = db.relationship(
        "Case", foreign_keys="Case.user_id", backref="creator", lazy=True
    )
    assigned_cases = db.relationship(
        "Case", foreign_keys="Case.assigned_to", backref="assignee", lazy=True
    )
    
    @property
    def unread_notifications_count(self):
        """Get count of unread notifications for this user"""
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return s.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            user_id = s.loads(token, max_age=expires_sec)["user_id"]
        except:
            return None
        return User.query.get(user_id)


class TargetImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    image_path = db.Column(db.String(200), nullable=False)
    image_type = db.Column(
        db.String(20), default="front"
    )  # front, side, back, full_body
    description = db.Column(db.String(200))
    is_primary = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TargetImage {self.image_type} for Case {self.case_id}>"


class SearchVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    video_path = db.Column(db.String(200), nullable=False)
    video_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200))
    duration = db.Column(db.Float)  # in seconds
    fps = db.Column(db.Float)
    resolution = db.Column(db.String(20))
    file_size = db.Column(db.BigInteger)  # in bytes
    status = db.Column(
        db.String(20), default="Pending"
    )  # Pending, Processing, Completed, Failed
    processed_at = db.Column(db.DateTime)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sightings = db.relationship("Sighting", backref="search_video", lazy=True)

    def __repr__(self):
        safe_name = sanitize_input(self.video_name) if self.video_name else 'Unknown'
        return f"<SearchVideo {safe_name} for Case {self.case_id}>"


class Sighting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    search_video_id = db.Column(
        db.Integer, db.ForeignKey("search_video.id"), nullable=False
    )
    video_name = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # timestamp in video (seconds)
    confidence_score = db.Column(db.Float, nullable=False)  # combined confidence
    face_score = db.Column(db.Float)
    clothing_score = db.Column(db.Float)
    detection_method = db.Column(
        db.String(20), nullable=False
    )  # face, clothing, multi_modal
    thumbnail_path = db.Column(db.String(200))
    bounding_box = db.Column(db.Text)  # JSON string of coordinates
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Sighting Case {self.case_id} at {self.timestamp}s - {self.confidence_score:.2f}>"

    @property
    def formatted_timestamp(self):
        minutes = int(self.timestamp // 60)
        seconds = int(self.timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"


class CaseNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    note_type = db.Column(
        db.String(20), default="General"
    )  # General, Update, Evidence, Contact
    content = db.Column(db.Text, nullable=False)
    is_important = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    author = db.relationship("User", backref="case_notes")

    def __repr__(self):
        safe_type = sanitize_input(self.note_type) if self.note_type else 'Unknown'
        return f"<CaseNote {safe_type} for Case {self.case_id}>"


class SystemLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey("case.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    action = db.Column(
        db.String(50), nullable=False
    )  # case_created, video_uploaded, sighting_found, etc.
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        safe_action = sanitize_input(self.action) if self.action else 'Unknown'
        return f"<SystemLog {safe_action} at {self.timestamp}>"


class AdminMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_messages")


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default="info")  # info, warning, success, danger
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    author = db.relationship("User", backref="announcements")


class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    author = db.relationship("User", backref="blog_posts")


class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="General")
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    author = db.relationship("User", backref="faqs")


class AISettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    setting_name = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    updater = db.relationship("User", backref="ai_settings_updates")


class Notification(db.Model):
    """User notification system for admin messages and system alerts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))  # Null for system messages
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(20), default="info")  # info, warning, success, danger
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recipient = db.relationship("User", foreign_keys=[user_id], backref="notifications")
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_notifications")
    
    def __repr__(self):
        safe_title = sanitize_input(self.title) if self.title else 'Unknown'
        return f"<Notification {safe_title} for User {self.user_id}>"
