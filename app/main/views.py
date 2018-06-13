from datetime import datetime, timedelta
from flask import render_template, flash, session, redirect, url_for, request, current_app, abort
from flask_login import login_required, current_user
from . import main
from .forms import AddTicketsForm, BookingForm
from ..email import send_email
from .. import db
from ..models import User, Event, Showing, Ticket, Booking

@main.before_app_request
def before_request():
    if 'tickets' in session:
        tickets = Ticket.query.filter(Ticket.id.in_(session['tickets'])).filter(Ticket.expiry <= datetime.utcnow()).all()
        if len(tickets) > 0:
            for ticket in tickets:
                if ticket.id in session['tickets']:
                    session['tickets'].remove(ticket.id)
                db.session.delete(ticket)
            db.session.commit()
            flash('Tickets in your cart have expired. Please check your cart.')
            return redirect(url_for('.booking'))

@main.route('/')
def index():
    showings = Showing.query.order_by(Showing.date.asc()).all()
    return render_template('index.html', showings=showings)

@main.route('/event/<int:id>')
def event(id):
    event = Event.query.get_or_404(id)
    showings = Showing.query.filter_by(event_id=event.id).order_by(Showing.date.asc())
    return render_template('event.html', event=event, showings=showings)

@main.route('/booking', methods=['GET', 'POST'])
def booking():
    form = BookingForm()
    if 'tickets' not in session:
        flash('You have selected no tickets.')
        return redirect(url_for('.index'))
    if form.validate_on_submit():
        booking = Booking(email=form.email.data, name=form.name.data, user_id=current_user.id)
        db.session.add(booking)
        db.session.commit()
        for id in session['tickets']:
            ticket = Ticket.query.filter_by(id=id).first()
            ticket.booking_id = booking.id
            db.session.commit()
        tickets = Ticket.query.filter_by(booking_id=booking.id).all()
        send_email(form.email.data, 'Booking Confirmation', 'email/booking_confirmation', booking=booking, tickets=tickets)
        flash('Booking complete, you have been emailed your booking details.')
        return redirect(url_for('.confirmation'))
    if current_user.is_authenticated:
        if form.name.data is None:
            form.name.data = current_user.name
        if form.email.data is None:
            form.email.data = current_user.email
        if form.email_repeat.data is None:
            form.email_repeat.data = current_user.email
    tickets = Ticket.query.filter(Ticket.id.in_(session['tickets'])).filter(Ticket.expiry > datetime.utcnow()).all()
    return render_template('booking.html', tickets=tickets, current_time=datetime.utcnow(), form=form)

@main.route('/booking/confirmation/')
def confirmation():
    session['tickets'] = []
    return render_template('confirmation.html')

@main.route('/booking/edit/<int:id>')
def edit_booking(id):
    booking = Booking.query.get_or_404(id)
    tickets = Ticket.query.filter_by(booking_id=id).order_by(Ticket.showing_id.asc(), Ticket.id.asc())
    return render_template('edit-booking.html', booking=booking, tickets=tickets)

@main.route('/showing/<int:id>', methods=['GET', 'POST'])
def showing(id):
    showing = Showing.query.get_or_404(id)
    booked_tickets = showing.tickets.filter(Ticket.booking_id!=None).all()
    bookings = Booking.query.join(Ticket, Ticket.booking_id == Booking.id).filter(Ticket.showing_id==id)
    ticket_types = showing.ticket_types
    tickets = []
    for ticket_type in ticket_types:
        tickets.append({'ticket_type':ticket_type.id, 'ticket_type_label':ticket_type.name, 'num_tickets':0})
    form = AddTicketsForm(tickets=tickets, showing_id=showing.id)
    if form.validate_on_submit():
        num_tickets = 0;
        tickets_list = []
        for tickets in form.tickets.data:
            tickets_list.extend([tickets['ticket_type']] * tickets['num_tickets'])
        tickets_available = showing.tickets_available()
        if len(tickets_list) <= tickets_available:
            expiry = datetime.utcnow() + timedelta(minutes=15)
            tickets = []
            for ticket_type_id in tickets_list:
                ticket = Ticket(expiry=expiry, paid=False, showing_id=showing.id, ticket_type_id=ticket_type_id)
                db.session.add(ticket)
                db.session.commit()
                tickets.append(ticket.id)
            if 'tickets' in session:
                session['tickets'].extend(tickets)
            else:
                session['tickets'] = tickets
            flash('Tickets added, please complete your booking to confirm tickets')
            return redirect(url_for('.booking'))
        else:
            flash('You have selected more tickets than are currently available.')
    return render_template('showing.html', showing=showing, tickets=booked_tickets, bookings=bookings, form=form)

@main.route('/my-bookings/')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.date_created.desc()).all();
    return render_template('my-bookings.html', bookings=bookings)

@main.route('/ticket/cancel/<int:id>')
@login_required
def cancel_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    if current_user != ticket.booking.user:
        abort(403)
    db.session.delete(ticket)
    db.session.commit()
    flash('The selected ticket has been deleted.')
    return redirect(url_for('.my_bookings'))
