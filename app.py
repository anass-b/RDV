from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL

app = Flask(__name__)

app.secret_key = 'Nenziffz8202Khanibal'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'doctor_appointments'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        mdp = request.form['mdp']

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM admins WHERE email = %s AND mdp = %s', (email, mdp,))
        admin = cur.fetchone()
        cur.close()

        if admin:
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            flash('Admin connecté avec succès', 'success')
            return redirect(url_for('admin_dashboard'))

        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM patients WHERE email = %s AND mdp = %s', (email, mdp,))
        patient = cur.fetchone()
        cur.close()

        if patient:
            session['patient_id'] = patient['id']
            flash('Patient Connecté avec succès', 'success')
            return redirect(url_for('user_dashboard'))
        else:
            return 'La connexion a échoué. Veuillez vérifier votre email et votre mot de passe.'

    return render_template('login.html')


@app.route('/user/logout')
def logout_user():
    session.clear() 
    return redirect(url_for('login'))


@app.route('/admin/logout')
def logout_admin():
    session.clear()  
    return redirect(url_for('login'))
 





@app.route('/admin/create_patient', methods=['GET', 'POST'])
def create_patient():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        mdp = request.form['mdp']
        date_naissance = request.form['date_naissance']
        CNIE = request.form['CNIE']
        Telephone = request.form['CNIE']

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO patients (nom,prenom,email,mdp,date_naissance,CNIE,num_tel) VALUES (%s, %s,%s,%s,%s,%s,%s)", (nom,prenom,email,mdp,date_naissance,CNIE,Telephone))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('show_patients'))
        except Exception as e:
            return str(e)

    return render_template('create_patient.html')


@app.route('/admin/show_patients')
def show_patients():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM patients")
        patients = cur.fetchall()
        cur.close()

        return render_template('show_patients.html', patients=patients)

    except Exception as e:
        return str(e)



@app.route('/admin/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        date_naissance = request.form['date_naissance']
        CNIE = request.form['CNIE']
        num_tel = request.form['num_tel']

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE patients
                SET nom = %s, prenom = %s, email = %s, date_naissance = %s, CNIE = %s, num_tel = %s
                WHERE id = %s
            """, (nom, prenom, email, date_naissance, CNIE, num_tel, patient_id))
            mysql.connection.commit()
            cur.close()

            flash('Les informations du Patient ont éte modifié avec succès', 'success')
            return redirect(url_for('show_patients'))

        except Exception as e:
            flash(f'An error occurred: {e}', 'error')
            return redirect(url_for('show_patients'))

    else:
        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM patients WHERE id = %s", (patient_id,))
            patient = cur.fetchone()
            cur.close()

            if patient:
                return render_template('edit_patient.html', patient=patient)
            else:
                flash('Patient non trouvé', 'error')
                return redirect(url_for('show_patients'))

        except Exception as e:
            flash(f'Une erreur s\'est produite: {e}', 'error')
            return redirect(url_for('show_patients'))
        

@app.route('/admin/delete_patient/<int:patient_id>', methods=['POST'])
def delete_patient(patient_id):
    try:
        cur = mysql.connection.cursor()

        cur.execute("DELETE FROM appointments WHERE patient_id = %s", (patient_id,))
        
        cur.execute("DELETE FROM patients WHERE id = %s", (patient_id,))
        
        mysql.connection.commit()
        cur.close()

        flash('Le Patient et ses Rendez-Vous ont été supprimés avec succès', 'success')
        return redirect(url_for('show_patients'))

    except Exception as e:
        flash(f'Une erreur s\'est produite: {e}', 'error')
        return redirect(url_for('show_patients'))


def check_overlapping_appointment(date_appointment, heure_appointment, duree):
    try:
        cur = mysql.connection.cursor()

        cur.execute("""
            SELECT * FROM appointments
            WHERE date_appointment = %s
            AND status = 'accepted'
            AND (
                (heure_appointment <= %s AND ADDTIME(heure_appointment, SEC_TO_TIME(%s * 60)) > %s) OR
                (heure_appointment >= %s AND heure_appointment < ADDTIME(%s, SEC_TO_TIME(%s * 60)))
            )
        """, (date_appointment, heure_appointment, duree, heure_appointment, heure_appointment, heure_appointment, duree))

        existing_appointment = cur.fetchone()
        cur.close()

        return existing_appointment is not None

    except Exception as e:
        app.logger.error(f"Erreur lors de la vérification des rendez-vous qui se chevauchent: {e}")
        return True  


@app.route('/user/appointments')
def user_appointments():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM appointments WHERE patient_id = %s", (patient_id,))
        appointments = cur.fetchall()
        cur.close()
        return render_template('user_appointments.html', appointments=appointments)
    else:
        return redirect(url_for('login'))  


@app.route('/user/request_appointment', methods=['GET', 'POST'])
def request_appointment():
    if 'patient_id' in session:
        if request.method == 'POST':
            date_appointment = request.form['date_appointment']
            heure_appointment = request.form['heure_appointment']
            duree = request.form['durée']
            patient_id = session['patient_id']

            if check_overlapping_appointment(date_appointment, heure_appointment, duree):
                flash('Cette heure de rendez-vous est déjà réservée. Veuillez choisir une heure différente.', 'error')
                return redirect(url_for('request_appointment'))
            
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO appointments (date_appointment, heure_appointment, durée, patient_id, status) VALUES (%s, %s, %s, %s, 'pending')", 
                        (date_appointment, heure_appointment, duree, patient_id))
            mysql.connection.commit()
            cur.close()
            
            flash('Rendez-vous pris avec succès', 'success')
            return redirect(url_for('user_dashboard'))
        
        return render_template('request_appointment.html')
    else:
        return redirect(url_for('login'))
 
    

@app.route('/admin/pending_appointments')
def pending_appointments():
    if 'admin_logged_in' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM appointments WHERE status = 'pending'")
        appointments = cur.fetchall()
        cur.close()
        return render_template('pending_appointments.html', appointments=appointments)
    else:
        return redirect(url_for('login'))  


@app.route('/admin/process_appointment/<int:appointment_id>/<action>', methods=['POST'])
def process_appointment(appointment_id, action):
    if 'admin_logged_in' in session:
        if action in ['accept', 'refuse']:
            status = 'accepted' if action == 'accept' else 'refused'
            cur = mysql.connection.cursor()
            cur.execute("UPDATE appointments SET status = %s WHERE id = %s", (status, appointment_id))
            mysql.connection.commit()
            cur.close()

            flash(f'Rendez-vous {status} avec succès', 'success')
            return redirect(url_for('pending_appointments'))

        return 'Invalid action'
    else:
        return redirect(url_for('login'))


@app.route('/admin/dashboard')
def admin_dashboard():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT nom, prenom FROM admins WHERE id = %s", (session['admin_id'],))
        admin = cur.fetchone()
        cur.close()

        if admin:
            admin_name = f"{admin['prenom']} {admin['nom']}"
            return render_template('admin_dashboard.html', admin_name=admin_name)
        else:
            return 'Admin non trouvé', 404  
    except Exception as e:
        return str(e)  

@app.route('/user/dashboard')
def user_dashboard():
    if 'patient_id' in session:
        patient_id = session['patient_id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT nom FROM patients WHERE id = %s", (patient_id,))
        patient = cur.fetchone()
        cur.close()
        if patient:
            patient_name = patient['nom']
            return render_template('user_dashboard.html', patient_name=patient_name)
        else:
            return redirect(url_for('login'))  
    else:
        return redirect(url_for('login'))  

if __name__ == '__main__':
    app.run(debug=True)
