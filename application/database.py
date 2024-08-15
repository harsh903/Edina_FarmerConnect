from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User table (Common details for both Farmers and Experts)
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # Store roles as strings: 'farmer' or 'expert'
    location = db.Column(db.String(100), nullable=False)
    primary_language = db.Column(db.String(50), nullable=False)
    
    # Relationships
    farmer_profile = db.relationship('Farmer', back_populates='user', uselist=False)
    expert_profile = db.relationship('Expert', back_populates='user', uselist=False)
    posts = db.relationship('Post', back_populates='user')
    chat_sessions = db.relationship('Chat', back_populates='user', foreign_keys='Chat.user_id')

# Farmer table (Details specific to Farmers)
class Farmer(db.Model):
    __tablename__ = 'farmers'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    land_size = db.Column(db.String(50), nullable=False)  # Example: 'small', 'medium', 'large', etc.
    farmer_bio = db.Column(db.Text)
    major_crops = db.Column(db.String(255))  # Crops the farmer typically grows
    
    # Relationship with User
    user = db.relationship('User', back_populates='farmer_profile')

# Expert table (Details specific to Experts)
class Expert(db.Model):
    __tablename__ = 'experts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), primary_key=True)
    expert_bio = db.Column(db.Text)
    experience = db.Column(db.Integer)  # Experience in years
    domain = db.Column(db.String(100))  # Domain expertise (e.g., agronomy, crop management)
    
    # Relationship with User
    user = db.relationship('User', back_populates='expert_profile')

# Post table (For both Farmers and Experts)
class Post(db.Model):
    __tablename__ = 'posts'
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship with User
    user = db.relationship('User', back_populates='posts')
    comments = db.relationship('PostCommentLikes', back_populates='post')

# PostCommentLikes table (For comments and likes/dislikes on posts)
class PostCommentLikes(db.Model):
    __tablename__ = 'post_comment_likes'
    comment_id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.post_id'))
    commenter_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # The user who commented
    creator_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))  # The original creator of the post
    comment = db.Column(db.Text, nullable=False)
    total_likes = db.Column(db.Integer, default=0)
    total_dislikes = db.Column(db.Integer, default=0)
    
    # Relationships
    post = db.relationship('Post', back_populates='comments')

    

class Chat(db.Model):
    __tablename__ = 'chats'
    chat_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    expert_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'accepted', 'declined'
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    user = db.relationship('User', back_populates='chat_sessions', foreign_keys=[user_id])
    expert = db.relationship('User', foreign_keys=[expert_id])
    replies = db.relationship('ChatReply', back_populates='chat')

class ChatReply(db.Model):
    __tablename__ = 'chat_replies'
    reply_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.chat_id'))
    expert_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    reply_message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationships
    chat = db.relationship('Chat', back_populates='replies')
    expert = db.relationship('User', foreign_keys=[expert_id])

class Appointment(db.Model):
    __tablename__ = 'appointments'
    appointment_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    expert_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    appointment_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'accepted', 'declined'
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    expert = db.relationship('User', foreign_keys=[expert_id])




with app.app_context():
    db.create_all()
    print("Database tables created.")
