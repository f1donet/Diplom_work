from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


db = SQLAlchemy()

class Employee(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.Text, nullable=False)
    position = db.Column(db.Text, nullable=False)
    hire_date = db.Column(db.Date, nullable=False, default=func.now())
    salary = db.Column(db.Integer, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)
    manager = db.relationship('Employee', remote_side=[id], backref='subordinates')

    def __repr__(self):
        return f"User(full_name={self.full_name!r})"

