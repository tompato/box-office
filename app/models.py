import uuid
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from flask_login import UserMixin
from . import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    name = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset': self.id})

    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.email

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    body = db.Column(db.Text())
    showings = db.relationship('Showing', backref='event', lazy='dynamic')

    def __repr__(self):
        return '<Event %r>' % self.name

class Showing(db.Model):
    __tablename__ = 'showings'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    date = db.Column(db.DateTime())
    num_tickets = db.Column(db.Integer)
    tickets = db.relationship('Ticket', backref='showing', lazy='dynamic')
    ticket_types = db.relationship('TicketType', backref='showing', lazy='dynamic')

    def tickets_available(self):
        booked_tickets = Ticket.query.filter(Ticket.showing_id==self.id, Ticket.booking_id!=None).count()
        session_tickets = Ticket.query.filter(Ticket.showing_id==self.id, Ticket.expiry > datetime.utcnow(), Ticket.booking_id==None).count()
        return self.num_tickets - (booked_tickets + session_tickets)

    def __repr__(self):
        return '<Showing %r>' % self.id

class Ticket(db.Model):
    __tablename__ = 'tickets'
    id = db.Column(db.Integer, primary_key=True)
    expiry = db.Column(db.DateTime(), default=datetime.utcnow() + timedelta(minutes=15))
    paid = db.Column(db.Boolean, default=False)
    showing_id = db.Column(db.Integer, db.ForeignKey('showings.id'))
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    ticket_type_id = db.Column(db.Integer, db.ForeignKey('ticket_types.id'))

    def generate_ticket_token(self, expiration=900):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def __repr__(self):
        return '<Ticket %r>' % self.id

class TicketType(db.Model):
    __tablename__ = 'ticket_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    price = db.Column(db.Numeric)
    showing_id = db.Column(db.Integer, db.ForeignKey('showings.id'))
    tickets = db.relationship('Ticket', backref='ticket_type', lazy='dynamic')

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), index=True)
    name = db.Column(db.String(64))
    date_created = db.Column(db.DateTime(), default=datetime.utcnow())
    booking_ref = db.Column(db.String(36), default=uuid.uuid4())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    tickets = db.relationship('Ticket', backref='booking', lazy='dynamic')

    def total_cost(self):
        total= 0;
        tickets = Ticket.query.filter(Ticket.booking_id==self.id).all()
        for ticket in tickets:
            total += ticket.ticket_type.price
        return total

    def __repr__(self):
        return '<Booking %r>' % self.id
