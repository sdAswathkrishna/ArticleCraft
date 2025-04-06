from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Article
from datetime import datetime
from urllib.parse import quote_plus
from recommendation_module import recommend_articles_nn
from nextword_module import generate_next_words, load_model_and_tokenizer
from generate_article_with_groq import ArticleGenerator
import jsonify

# Initialize Article Generator
generator = ArticleGenerator()
generator.setup_vector_database("final_nlp_data.csv", sample_size=1000)

model, tokenizer = load_model_and_tokenizer()
max_seq_len = 30  # Set this based on training time

password = quote_plus('aswath@22')

app = Flask(__name__)
app.secret_key = 'a8f3e9b27c34a1d7f5e649e0a2d4537bb7f89cc30b3c9e6dfc4d8c71a1475efb'

# --- MySQL DB Config ---
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{password}@localhost/coderelate'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ---------- ROUTES ---------- #

@app.route('/')
def home():
    articles = Article.query.order_by(Article.timestamp.desc()).limit(10).all()
    return render_template('home.html', articles=articles)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw, email=email)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('login'))

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        seed_text = request.form['seed_text']
        predictions = generate_next_words(
            seed_text, 
            next_words=10, 
            model=model, 
            tokenizer=tokenizer, 
            max_seq_len=max_seq_len
        )
        
        # Return the predictions as JSON
        return jsonify({
            'success': True,
            'predictions': predictions
        })
    
    # Handle GET request or return error for POST without seed_text
    return jsonify({
        'success': False,
        'error': 'Please provide seed text'
    })


@app.route('/write', methods=['GET', 'POST'])
def write():
    if 'user_id' not in session:
        flash("Please login to write.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form.get('tags', '')

        new_article = Article(
            title=title,
            content=content,
            tags=tags,
            author_id=session['user_id']
        )
        db.session.add(new_article)
        db.session.commit()

        flash('Article posted successfully.')
        return redirect(url_for('home'))

    return render_template('write.html')


@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if 'user_id' not in session:
        flash("Please login to use AI generation.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']

        # Placeholder: Call your AI text generation pipeline here
        generated_content = generator.generate_article(title, num_similar_articles=3)

        new_article = Article(
            title=title,
            content=generated_content,
            generated=True,
            author_id=session['user_id']
        )
        db.session.add(new_article)
        db.session.commit()

        flash("Article generated and saved.")
        return redirect(url_for('home'))

    return render_template('generate.html')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please login to view your profile.")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    articles = Article.query.filter_by(author_id=user.id).all()
    article_count = len(articles)

    return render_template('profile.html', user=user, articles=articles, count=article_count)


@app.route('/article/<int:article_id>')
def view_article(article_id):
    article = Article.query.get_or_404(article_id)

    # TODO: Add recommendation logic here based on the current article
    recommendations = recommend_articles_nn(article.title)

    return render_template('article.html', article=article, recommendations=recommendations)


# ---------- MAIN ---------- #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
