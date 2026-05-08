from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash
)

from flask_sqlalchemy import SQLAlchemy

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

app = Flask(__name__)

app.secret_key = 'promptpilotsecretkey'

# Database Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///promptpilot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =========================
# Database Models
# =========================

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(db.String(300), nullable=False)


class Prompt(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    prompt_text = db.Column(db.Text, nullable=False)

    status = db.Column(
        db.String(50),
        default='Pending'
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    feedback = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(db.Integer)


# =========================
# Helper Function
# =========================

def user_logged_in():

    return 'user_id' in session


# =========================
# Home Page
# =========================

@app.route('/')
def home():

    return render_template('home.html')


# =========================
# Register
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email or not password:

            flash(
                'Please fill all fields',
                'warning'
            )

            return redirect('/register')

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash(
                'Email already registered',
                'danger'
            )

            return redirect('/register')

        encrypted_password = generate_password_hash(
            password
        )

        user = User(
            name=name,
            email=email,
            password=encrypted_password
        )

        db.session.add(user)
        db.session.commit()

        flash(
            'Registration successful. Please login.',
            'success'
        )

        return redirect('/login')

    return render_template('register.html')


# =========================
# Login
# =========================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id
            session['user_name'] = user.name

            flash(
                'Login successful',
                'success'
            )

            return redirect('/dashboard')

        flash(
            'Invalid email or password',
            'danger'
        )

        return redirect('/login')

    return render_template('login.html')


# =========================
# Dashboard
# =========================

@app.route('/dashboard')
def dashboard():

    if not user_logged_in():

        return redirect('/login')

    total_prompts = Prompt.query.filter_by(
        user_id=session['user_id']
    ).count()

    pending_prompts = Prompt.query.filter_by(
        user_id=session['user_id'],
        status='Pending'
    ).count()

    reviewed_prompts = Prompt.query.filter_by(
        user_id=session['user_id'],
        status='Reviewed'
    ).count()

    return render_template(
        'dashboard.html',
        total_prompts=total_prompts,
        pending_prompts=pending_prompts,
        reviewed_prompts=reviewed_prompts
    )


# =========================
# Submit Prompt
# =========================

@app.route('/submit-prompt', methods=['GET', 'POST'])
def submit_prompt():

    if not user_logged_in():

        return redirect('/login')

    if request.method == 'POST':

        title = request.form.get('title')
        prompt_text = request.form.get('prompt_text')

        if not title or not prompt_text:

            flash(
                'All fields are required',
                'warning'
            )

            return redirect('/submit-prompt')

        if len(prompt_text) < 20:

            flash(
                'Prompt should contain at least 20 characters',
                'warning'
            )

            return redirect('/submit-prompt')

        prompt = Prompt(
            title=title,
            prompt_text=prompt_text,
            user_id=session['user_id']
        )

        db.session.add(prompt)
        db.session.commit()

        flash(
            'Prompt submitted successfully',
            'success'
        )

        return redirect('/my-prompts')

    return render_template('submit_prompt.html')


# =========================
# My Prompts
# =========================

@app.route('/my-prompts')
def my_prompts():

    if not user_logged_in():

        return redirect('/login')

    search = request.args.get('search')
    status = request.args.get('status')

    prompts = Prompt.query.filter_by(
        user_id=session['user_id']
    )

    if search:

        prompts = prompts.filter(
            Prompt.title.contains(search)
        )

    if status:

        prompts = prompts.filter_by(
            status=status
        )

    prompts = prompts.order_by(
        Prompt.created_at.desc()
    ).all()

    return render_template(
        'my_prompts.html',
        prompts=prompts
    )


# =========================
# Review Prompt
# =========================

@app.route('/review/<int:id>')
def review_prompt(id):

    if not user_logged_in():

        return redirect('/login')

    prompt = Prompt.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first()

    if not prompt:

        flash(
            'Prompt not found',
            'danger'
        )

        return redirect('/my-prompts')

    prompt.status = 'Reviewed'
    prompt.score = 8
    prompt.feedback = 'Good prompt structure and clarity'

    db.session.commit()

    flash(
        'Prompt reviewed successfully',
        'success'
    )

    return redirect('/my-prompts')


# =========================
# Edit Prompt
# =========================

@app.route('/edit-prompt/<int:id>', methods=['GET', 'POST'])
def edit_prompt(id):

    if not user_logged_in():

        return redirect('/login')

    prompt = Prompt.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first()

    if not prompt:

        flash(
            'Prompt not found',
            'danger'
        )

        return redirect('/my-prompts')

    if request.method == 'POST':

        title = request.form.get('title')
        prompt_text = request.form.get('prompt_text')

        if not title or not prompt_text:

            flash(
                'All fields are required',
                'warning'
            )

            return redirect(f'/edit-prompt/{id}')

        prompt.title = title
        prompt.prompt_text = prompt_text

        db.session.commit()

        flash(
            'Prompt updated successfully',
            'success'
        )

        return redirect('/my-prompts')

    return render_template(
        'edit_prompt.html',
        prompt=prompt
    )


# =========================
# Delete Prompt
# =========================

@app.route('/delete-prompt/<int:id>')
def delete_prompt(id):

    if not user_logged_in():

        return redirect('/login')

    prompt = Prompt.query.filter_by(
        id=id,
        user_id=session['user_id']
    ).first()

    if not prompt:

        flash(
            'Prompt not found',
            'danger'
        )

        return redirect('/my-prompts')

    db.session.delete(prompt)
    db.session.commit()

    flash(
        'Prompt deleted successfully',
        'success'
    )

    return redirect('/my-prompts')


# =========================
# Logout
# =========================

@app.route('/logout')
def logout():

    session.clear()

    flash(
        'Logged out successfully',
        'success'
    )

    return redirect('/login')


# =========================
# 404 Page
# =========================

@app.errorhandler(404)
def page_not_found(error):

    return render_template('404.html'), 404


# =========================
# Run App
# =========================

with app.app_context():

    db.create_all()


if __name__ == '__main__':

    app.run(debug=True)