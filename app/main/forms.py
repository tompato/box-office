from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, HiddenField, SubmitField, FormField, FieldList
from wtforms.validators import Required, Length, Email, EqualTo
from wtforms import ValidationError

class NumberOfTicketsForm(FlaskForm):
    num_tickets = IntegerField('How many tickets?')
    ticket_type = HiddenField()

    def __init__(self, ticket_type_label, *args, **kwargs):
        super(NumberOfTicketsForm, self).__init__(*args, **kwargs)
        self.num_tickets.label.text = 'How many %s tickets?' % ticket_type_label

class AddTicketsForm(FlaskForm):
    tickets = FieldList(FormField(NumberOfTicketsForm), min_entries=1, validators=[Required()])
    showing_id = HiddenField('Showing', validators=[Required()])
    submit = SubmitField('Submit')

class BookingForm(FlaskForm):
    name = StringField('Name', validators=[Required(), Length(1, 64)])
    email = StringField('Email', validators=[Required(), Length(1, 64), Email(), EqualTo('email_repeat', message='Emails do not match.')])
    email_repeat = StringField('Repeat Email', validators=[Required(), Length(1, 64), Email()])
    submit = SubmitField('Submit')
