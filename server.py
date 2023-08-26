from flask import Flask, render_template, request, send_file, redirect, url_for, flash, Response, abort
import hashlib
import os
from util import *
from crud import *

app = Flask(__name__)
app.secret_key = os.urandom(64)

@app.context_processor
def inject_user_session():
	user_session = getUserSession()
	con = get_db()
	cur = con.cursor()
	site_settings = getSiteSettings(cur)
	site_header_links = getSiteHeaderLinks(cur)
	site_pages = getSitePages(cur)
	return dict(user_session=user_session, site_settings=site_settings, site_header_links=site_header_links, site_pages=site_pages)

@app.errorhandler(404)
def notFound(e):
	return render_template('404.html', title='404 Not Found', path=request.path)

@app.route('/')
def index():
	return uncached_redirect('/home')

@app.route('/<path:path>')
@requires_db
def path(path):
	path = f'/{path}'
	cur = request.db.cursor()
	site_page = getSitePageByRoute(cur, path)
	if site_page is None:
		abort(404)
	return render_template('path.html', main=renderMarkdown(site_page['content']), title=site_page['title'])

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
		con.commit()
		return uncached_redirect(url_for('admin'))

@app.route('/admin/<path:path>', methods=['GET', 'POST'])
@requires_authority(1)
@requires_db
def updatePage(path):
	path = f'/{path}'
	con = request.db
	cur = con.cursor()
	if request.method == 'GET':
		page = getSitePageByRoute(cur, path)
		return render_template('update_page.html', title='Update Page', page=page)

	elif request.method == 'POST':
		updateSitePageByRoute(cur, request.form['route'], request.form['title'], request.form['content'])
		con.commit()
		flash('Update Successful')
		return uncached_redirect(url_for('updatePage', path=path[1:]))

@app.route('/admin/delete/<path:path>')
@requires_authority(1)
@requires_db
def deletePage(path):
	path = f'/{path}'
	con = request.db
	cur = con.cursor()
	cur = request.db.cursor()
	if request.method == 'GET':
		deleteSitePageByRoute(cur, path)
		con.commit()
		return uncached_redirect(url_for('admin'))

@app.route('/admin/create_page', methods=['GET', 'POST'])
@requires_authority(1)
@requires_db
def createPage():
	if request.method == 'GET':
		return render_template('create_page.html', title='Create Page', route=request.args.get('path', ''))

	elif request.method == 'POST':
		con = request.db
		cur = con.cursor()
		createSitePage(cur, request.form['title'], request.form['route'], request.form['content'])
		con.commit()
		return uncached_redirect(url_for('admin'))

if __name__ == '__main__':
	app.run('0.0.0.0', 5000, debug=True)