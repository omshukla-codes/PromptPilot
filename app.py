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

app.secret_key = 'promptpilotsecret'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///promptpilot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# User Model
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100))

    email = db.Column(
        db.String(100),
        unique=True
    )

    password = db.Column(db.String(300))


# Prompt Model
class Prompt(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200))

    prompt_text = db.Column(db.Text)

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


# Home Route
@app.route('/')
def home():

    return render_template('home.html')


# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if name == '' or email == '' or password == '':

            flash('All fields are required')

            return redirect('/register')

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            flash('Email already exists')

            return redirect('/register')

        hashed_password = generate_password_hash(password)

        new_user = User(
            name=name,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        flash('Registration successful')

        return redirect('/login')

    return render_template('register.html')


# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session['user_id'] = user.id

            session['user_name'] = user.name

            flash('Login successful')

            return redirect('/dashboard')

        else:

            flash('Invalid email or password')

            return redirect('/login')

    return render_template('login.html')


# Dashboard Route
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:

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


# Submit Prompt Route
@app.route('/submit-prompt', methods=['GET', 'POST'])
def submit_prompt():

    if 'user_id' not in session:

        return redirect('/login')

    if request.method == 'POST':

        title = request.form['title']

        prompt_text = request.form['prompt_text']

        if title == '' or prompt_text == '':

            flash('All fields are required')

            return redirect('/submit-prompt')

        if len(prompt_text) < 20:

            flash('Prompt should be at least 20 characters')

            return redirect('/submit-prompt')

        new_prompt = Prompt(
            title=title,
            prompt_text=prompt_text,
            user_id=session['user_id']
        )

        db.session.add(new_prompt)

        db.session.commit()

        flash('Prompt submitted successfully')

        return redirect('/my-prompts')

    return render_template('submit_prompt.html')


# My Prompts Route
@app.route('/my-prompts')
def my_prompts():

    if 'user_id' not in session:

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


# Review Route
@app.route('/review/<int:id>')
def review_prompt(id):

    if 'user_id' not in session:

        return redirect('/login')

    prompt = Prompt.query.get(id)

    if prompt:

        prompt.status = 'Reviewed'

        prompt.score = 8

        prompt.feedback = (
            'Good clarity and structure'
        )

        db.session.commit()

        flash('Prompt reviewed successfully')

    return redirect('/my-prompts')


# Edit Route
@app.route('/edit-prompt/<int:id>', methods=['GET', 'POST'])
def edit_prompt(id):

    if 'user_id' not in session:

        return redirect('/login')

    prompt = Prompt.query.get(id)

    if request.method == 'POST':

        title = request.form['title']

        prompt_text = request.form['prompt_text']

        if title == '' or prompt_text == '':

            flash('All fields are required')

            return redirect(f'/edit-prompt/{id}')

        prompt.title = title

        prompt.prompt_text = prompt_text

        db.session.commit()

        flash('Prompt updated successfully')

        return redirect('/my-prompts')

    return render_template(
        'edit_prompt.html',
        prompt=prompt
    )


# Delete Route
@app.route('/delete-prompt/<int:id>')
def delete_prompt(id):

    if 'user_id' not in session:

        return redirect('/login')

    prompt = Prompt.query.get(id)

    if prompt:

        db.session.delete(prompt)

        db.session.commit()

        flash('Prompt deleted successfully')

    return redirect('/my-prompts')


# Logout Route
@app.route('/logout')
def logout():

    session.clear()

    flash('Logged out successfully')

    return redirect('/login')


# 404 Error Route
@app.errorhandler(404)
def not_found(e):

    return render_template('404.html'), 404


# Run App
if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(debug=True)