#!/usr/bin/env python

from flask import Flask, request, flash, redirect, url_for, jsonify
from flask import render_template

from database import db, Employee
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = '1234'
#Адрес расположения базы данных
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///C:/Users/anton/Desktop/Education/Projects/Portfolio/lLine part 2/My_project/employees.db"
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route("/")
def all_employees():
    employees = Employee.query.all()
    return render_template("all_employees.html", employees=employees)

@app.route("/manager/<manager_id>")
def employees_by_manager(manager_id):
# Находим начальника
    manager = Employee.query.filter(Employee.id == manager_id).first()
# Получаем всех его подчинённых (через связь subordinates)
    employees = manager.subordinates if manager else []
    return render_template("employees_by_manager.html", manager=manager, employees=employees)

@app.route("/sort/name")
def sort_name():
    employees = Employee.query.order_by(Employee.full_name.asc()).all()
    return render_template("sort_name.html", employees=employees)

@app.route("/sort/salary_asc")
def sort_salary_asc():
    employees = Employee.query.order_by(Employee.salary.asc()).all()
    return render_template("sort_salary_asc.html", employees=employees)

@app.route("/sort/salary_desc")
def sort_salary_desc():
    employees = Employee.query.order_by(Employee.salary.desc()).all()
    return render_template("sort_salary_desc.html", employees=employees)

@app.route("/sort/hire_date_asc")
def sort_hire_date_asc():
    employees = Employee.query.order_by(Employee.hire_date.asc()).all()
    return render_template("sort_hire_date_asc.html", employees=employees)

@app.route("/sort/hire_date_desc")
def sort_hire_date_desc():
    employees = Employee.query.order_by(Employee.hire_date.desc()).all()
    return render_template("sort_hire_date_desc.html", employees=employees)

@app.route("/search/")
def search_employees():
    search = request.args.get('search', '')
    if not search:
        employees = Employee.query.all()
    else:
        employees = Employee.query.filter(Employee.full_name.ilike(f'%{search}%')).all()
    return render_template("search_employees.html", employees=employees)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    managers = Employee.query.all()
    if request.method == 'POST':
        # Получаем данные из формы
        full_name = request.form['full_name']
        position = request.form['position']
        hire_date_str = request.form['hire_date']
        salary = request.form['salary']
        manager_id = request.form.get('manager_id')

        try:
            salary = int(salary)
        except ValueError:
            flash('Ошибка: зарплата должна быть числом.', 'error')
            return render_template('add_employee.html', employee=None, managers=managers)

        if manager_id:
            try:
                manager_id = int(manager_id)
            except ValueError:
                flash('Ошибка: ID менеджера должен быть числом.', 'error')
                return render_template('add_employee.html', employee=None, managers=managers)
        else:
            manager_id = None

        try:
            hire_date = datetime.strptime(hire_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Ошибка: неверный формат даты. Используйте формат ГГГГ-ММ-ДД.', 'error')
            return render_template('add_employee.html', employee=None, managers=managers)


        new_employee = Employee(
            full_name=full_name,
            position=position,
            hire_date=hire_date,
            salary=salary,
            manager_id=manager_id
        )

        db.session.add(new_employee)
        try:
            db.session.commit()
            flash('Сотрудник успешно добавлен!', 'success')
            return redirect(url_for('all_employees'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка при добавлении сотрудника: ' + str(e), 'error')

    # Для GET-запроса показываем форму
    return render_template('add_employee.html', employee=None, managers=managers)

@app.route('/delete_employee/', methods=['GET', 'POST'])
def delete_employee():
    managers = Employee.query.all()
    if request.method == 'POST':
        employee_id_str = request.form.get('id')
        if not employee_id_str:
            flash('Ошибка: не указан ID сотрудника.', 'error')
            return redirect(url_for('all_employees'))

        try:
            employee_id = int(employee_id_str)
        except ValueError:
            flash('Ошибка: некорректный ID сотрудника.', 'error')
            return redirect(url_for('all_employees'))

        employee = Employee.query.get(employee_id)
        if not employee:
            flash('Ошибка: сотрудник с таким ID не найден.', 'error')
            return redirect(url_for('all_employees'))

        try:
            db.session.delete(employee)
            db.session.commit()
            flash('Сотрудник успешно удалён!', 'success')
            return redirect(url_for('all_employees'))
        except Exception as e:
            db.session.rollback()
            flash('Произошла ошибка при удалении сотрудника.', 'error')
            return redirect(url_for('all_employees'))

    return render_template('delete_employee.html', employee=None, managers=managers)

@app.route('/employee/<employee_id>/change_manager', methods=['GET', 'POST'])
def change_manager(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    new_manager_id = request.form.get('manager_id')

    if request.method == 'GET':
        managers = Employee.query.filter(Employee.id != employee.id).all()
        return render_template(
            "change_manager.html",
            employee=employee,
            managers=managers
        )
    try:
        if new_manager_id and new_manager_id.strip() != '':
            try:
                new_manager_id_int = int(new_manager_id)
            except ValueError:
                flash('Ошибка: ID начальника должен быть числом.', 'error')
                return redirect(url_for('all_employees'))

            new_manager = Employee.query.get(new_manager_id_int)
            if not new_manager:
                flash(f'Ошибка: начальник с ID {new_manager_id_int} не найден.', 'error')
                return redirect(url_for('all_employees'))

            if new_manager.id == employee.id:
                flash('Сотрудник не может быть своим собственным начальником.', 'error')
                return redirect(url_for('all_employees'))

            employee.manager_id = new_manager_id_int
            # Сохраняем ссылку на найденного менеджера для сообщения
            target_manager = new_manager
        else:
            employee.manager_id = None
            target_manager = None

        db.session.commit()

        # Безопасное формирование сообщения
        if target_manager:
            flash(f'Начальник для {employee.full_name} успешно изменён на {target_manager.full_name}.', 'success')
        else:
            flash(f'Начальник для {employee.full_name} успешно удалён.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при сохранении: {str(e)}', 'error')
        managers = Employee.query.filter(Employee.id != employee.id).all()
        return render_template(
            "change_manager.html",
            employee=employee,
            managers=managers
        )
    return redirect(url_for('all_employees'))

if __name__ == '__main__':
    app.run()


