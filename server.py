from flask import Flask, render_template, request, send_file, redirect, url_for, flash, Response, abort
import hashlib
import os
from util import *
from crud import *
import time
import write
from config import *
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.urandom(64)

@app.context_processor
def inject_user_session():
	user_session = getUserSession()
	con = get_db()
	cur = con.cursor()
	site_settings = getSiteSettings(cur)
	site_header_links = getSiteHeaderLinks(cur)
	posts = getPosts(cur)
	year = time.strftime('%Y')
	return dict(user_session=user_session, site_settings=site_settings, site_header_links=site_header_links, posts=posts, year=year)

@app.errorhandler(404)
def notFound(e):
	return render_template('404.html', title='404 Not Found')

@app.route('/')
@requires_db
def index():
	cur = request.db.cursor()
	site_settings = getSiteSettings(cur)
	posts = getPosts(cur)
	content = f"# {site_settings['name']}\n\n### A blog about {site_settings['topic']}.\n\n## Recent posts\n\n---\n\n"
	for post in posts:
		content += f"### <a href='/post/{post['post_id']}'>{post['title']}</a> by {post['author']}\n\n{post['summary']}\n\n---\n\n"
	return render_template('post.html', main=renderMarkdown(content), title='Home')

@app.route('/post/<id>')
@requires_db
def post(id):
	cur = request.db.cursor()
	post = getPostById(cur, id)
	if post is None:
		abort(404)
	content = f"# {post['title']}\n\nWritten by {post['author']} on {time.strftime('%x', time.localtime(post['timestamp']))}\n\n---\n\n{post['content']}"
	return render_template('post.html', main=renderMarkdown(content), title=post['title'])

@app.route('/support')
def support():
	return render_template('support.html', title='Support')

@app.route('/terms')
def terms():
	return render_template('terms.html', title='Terms and Conditions')

@app.route('/privacy')
def privacy():
	return render_template('privacy.html', title='Privacy Policy')

@app.route('/account')
@requires_login
@requires_db
def account():
	return render_template('account.html', title="Account")

@app.route('/login', methods=['GET', 'POST'])
@requires_db
def login():
	if request.method == 'GET':
		return render_template('login.html', title='Login')
	
	elif request.method == 'POST':
		cur = request.db.cursor()
		user = getUserByUsername(cur, request.form.get('username'))
		if user is None:
			flash("Username does not exist", 'error')
			return redirect(url_for('login'))

		hasher = hashlib.sha512()
		hasher.update(bytes(request.form.get('password'), 'ascii'))
		passhash = hasher.hexdigest()

		if passhash != user.get('passhash'):
			flash("Incorrect password", 'error')
			return redirect(url_for('login'))
		
		is_new_session_id = False
		while not is_new_session_id:
			session_id = os.urandom(8).hex()
			if not sessionExists(cur, session_id):
				is_new_session_id = True
		
		user_id = user.get('user_id')

		deleteSessionByUserId(cur, user_id)
		setUserSession(cur, user_id, session_id)
		request.db.commit()
		
		res = make_response(redirect(url_for('index')))
		res.set_cookie('session_id', session_id, max_age=60*60*24*365*10)
		return res

@app.route('/register', methods=['GET', 'POST'])
@requires_db
def register():
	if request.method == 'GET':
		return render_template('register.html', title='Register')
	
	elif request.method == 'POST':
		email = request.form.get('email')
		username = request.form.get('username')
		password = request.form.get('password')
		confirmPassword = request.form.get('confirm-password')
		first_name = request.form.get('first-name')
		last_name = request.form.get('last-name')

		if email == "":
			flash("Email address cannot be empty", 'error')
			return redirect(url_for('register'))

		if username == "":
			flash("Username cannot be empty", 'error')
			return redirect(url_for('register'))

		if first_name == "":
			flash("First name cannot be empty", 'error')
			return redirect(url_for('register'))

		if last_name == "":
			flash("Last name cannot be empty", 'error')
			return redirect(url_for('register'))

		if password == "":
			flash("Password cannot be empty", 'error')
			return redirect(url_for('register'))

		if password != confirmPassword:
			flash("Passwords do not match", 'error')
			return redirect(url_for('register'))
		
		cur = request.db.cursor()
		user = getUserByUsername(cur, username)

		if user is not None:
			flash("Username already exists", 'error')
			return redirect(url_for('register'))
		
		user = getUserByEmail(cur, email)
		if user is not None:
			flash("Email address already exists", 'error')
			return redirect(url_for('register'))

		hasher = hashlib.sha512()
		hasher.update(bytes(password, 'ascii'))
		passhash = hasher.hexdigest()
		
		createUser(cur, email, username, passhash, first_name, last_name)
		request.db.commit()

		user = getUserByUsername(cur, username)

		# send_email.default_send(
		# 	f"{first_name} {last_name}",
		# 	email,
		# 	"Confirm Your Email",
		# 	send_email.render_email("confirm_email.html", first_name=first_name, confirmation_code=user['confirmation_code']))

		flash("Please check your inbox for a confirmation email.")

		is_new_session_id = False
		while not is_new_session_id:
			session_id = os.urandom(8).hex()
			if not sessionExists(cur, session_id):
				is_new_session_id = True
		user_id = user.get('user_id')

		setUserSession(cur, user_id, session_id)
		request.db.commit()
		
		res = make_response(redirect(url_for('index')))
		res.set_cookie('session_id', session_id, max_age=60*60*24*365*10)
		return res

@app.route('/email/confirm')
@requires_db
def confirm_email():
	confirmation_code = request.args.get('confirmation_code')

	if confirmation_code is None:
		flash("Confirmation code can not be empty.", 'error')
		return uncached_redirect(url_for('index'))

	cur = request.db.cursor()
	user = confirmUser(cur, confirmation_code)

	if user is None:
		flash("Could not find user for that code.", 'error')
		return uncached_redirect(url_for('index'))

	request.db.commit()

	return uncached_redirect(url_for('account'))

@app.route('/logout')
@requires_login
@requires_db
def logout():
	cur = request.db.cursor()
	deleteSessionByUserId(cur, request.user_session['user_id'])
	request.db.commit()

	res = make_response(redirect(url_for('login')))
	res.set_cookie('session', '', expires=0)
	return res

@app.route('/admin', methods=['GET', 'POST'])
@requires_authority(1)
@requires_db
def admin():
	if request.method == 'GET':
		return render_template('admin.html', title='Admin')

	elif request.method == 'POST':
		con = request.db
		cur = con.cursor()
		setSiteSettings(cur, dict(request.form))
		generateFavicon(request.form['name'][0], request.form['primary-color'], request.form['secondary-color'], serifs=True).save('static/favicon-32.png')
		con.commit()
		return uncached_redirect(url_for('admin'))

@app.route('/admin/post/<id>', methods=['GET', 'POST'])
@requires_authority(1)
@requires_db
def updatePost(id):
	con = request.db
	cur = con.cursor()
	if request.method == 'GET':
		post = getPostById(cur, id)
		return render_template('update_post.html', title='Update Post', post=post)

	elif request.method == 'POST':
		updatePostByIdNow(cur, id, request.form['title'], request.form['author'], request.form['content'], request.form['summary'])
		con.commit()
		flash('Update Successful')
		return uncached_redirect(url_for('admin'))

@app.route('/admin/delete/post/<id>')
@requires_authority(1)
@requires_db
def deletePost(id):
	con = request.db
	cur = con.cursor()
	deletePostById(cur, id)
	con.commit()
	return uncached_redirect(url_for('admin'))

@app.route('/admin/create_post', methods=['GET', 'POST'])
@requires_authority(1)
@requires_db
def createPost():
	if request.method == 'GET':
		return render_template('create_post.html', title='Create Post')

	elif request.method == 'POST':
		con = request.db
		cur = con.cursor()
		createPostNow(cur, request.form['title'], request.form['author'], request.form['content'], request.form['summary'])
		con.commit()
		return uncached_redirect(url_for('admin'))

@app.route('/admin/generate_post')
@requires_authority(1)
@requires_db
def generatePost():
	con = request.db
	cur = con.cursor()
	client = OpenAI(api_key=OPENAI_API_KEY)
	site_settings = getSiteSettings(cur)
	post = write.generatePostTopics(client, site_settings['name'], site_settings['topic'], 1)[0]

	content = ""

	sections = write.generatePostSections(client, site_settings['name'], site_settings['topic'], post['title'], post['summary'])
	for section in sections:
		content += f"## {section['title']}\n\n"
		section_paragraphs = write.generateSectionContent(client, site_settings['name'], site_settings['topic'], post['title'], post['summary'], section['title'], section['summary'])
		for section_paragraph in section_paragraphs:
			content += f"{section_paragraph}\n\n"

	createPostNow(cur, post['title'], 'Theodore Bellamy', content, post['summary'])
	con.commit()
	return uncached_redirect(url_for('admin'))

if __name__ == '__main__':
	app.run('0.0.0.0', 5000, debug=True)