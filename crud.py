import os
import time
import uuid

def getExamplePodcasts(cursor):
	res = cursor.execute('SELECT * FROM example_podcasts INNER JOIN podcasts ON example_podcasts.podcast_id = podcasts.podcast_id')
	return res.fetchall()

def getPodcastById(cursor, podcast_id):
	res = cursor.execute('SELECT * FROM podcasts WHERE podcast_id = ?', (podcast_id,))
	return res.fetchone()

def getPodcastsByUserId(cursor, user_id):
	res = cursor.execute('SELECT * FROM podcasts INNER JOIN user_podcasts ON podcasts.podcast_id = user_podcasts.podcast_id WHERE user_podcasts.user_id = ?', (user_id,))
	return res.fetchall()

def getSubtopicsByPodcastId(cursor, podcast_id):
	res = cursor.execute('SELECT * FROM podcast_subtopics WHERE podcast_id=? ORDER BY subtopic_number', (podcast_id,))
	return res.fetchall()

def deletePodcastForUser(cursor, podcast_id, user_id):
	cursor.execute('DELETE FROM user_podcasts WHERE podcast_id=? AND user_id=?', (podcast_id, user_id))

def deletePodcast(cursor, podcast_id):
	cursor.execute('DELETE FROM podcasts WHERE podcast_id=?', (podcast_id,))

def userHasPodcast(cursor, user_id, podcast_id):
	res = cursor.execute('SELECT * FROM user_podcasts WHERE user_id = ? AND podcast_id = ?', (user_id, podcast_id))
	res = res.fetchone()
	return res is not None

def isExamplePodcast(cursor, podcast_id):
	res = cursor.execute('SELECT * FROM example_podcasts WHERE podcast_id = ?', (podcast_id,))
	res = res.fetchone()
	return res is not None

def getUserByUsername(cursor, username):
	res = cursor.execute('SELECT * FROM users WHERE username=?', (username,))
	return res.fetchone()

def getUserByEmail(cursor, email):
	res = cursor.execute('SELECT * FROM users WHERE email=?', (email,))
	return res.fetchone()

def sessionExists(cursor, session_id):
	res = cursor.execute('SELECT * FROM sessions WHERE session_id=?', (session_id,))
	session = res.fetchone()
	return session is not None

def deleteSessionByUserId(cursor, user_id):
	cursor.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))

def setUserSession(cursor, user_id, session_id):
	cursor.execute('INSERT INTO sessions (session_id, user_id, created) VALUES (?, ?, ?)', (session_id, user_id, int(time.time())))

def userExistsById(cursor, user_id):
	res = cursor.execute('SELECT * FROM users WHERE user_id=?', (user_id,))
	user = res.fetchone()
	return user is not None

def userExistsByVerificationCode(cursor, confirmation_code):
	res = cursor.execute('SELECT * FROM users WHERE confirmation_code=?', (confirmation_code,))
	user = res.fetchone()
	return user is not None

def createUser(cursor, email, username, passhash, first_name, last_name):
	is_new_user_id = False
	while not is_new_user_id:
		user_id = os.urandom(8).hex()
		if not userExistsById(cursor, user_id):
			is_new_user_id = True

	is_new_confirmation_code = False
	while not is_new_confirmation_code:
		confirmation_code = os.urandom(8).hex()
		if not userExistsByVerificationCode(cursor, confirmation_code):
			is_new_confirmation_code = True

	cursor.execute('INSERT INTO users (user_id, email, username, passhash, confirmation_code, first_name, last_name) VALUES (?, ?, ?, ?, ?, ?, ?)', (user_id, email, username, passhash, confirmation_code, first_name, last_name))

def confirmUser(cursor, confirmation_code):
	cursor.execute('UPDATE users SET verified=TRUE WHERE confirmation_code=?', (confirmation_code,))
	return cursor.execute('SELECT * FROM users WHERE confirmation_code=?', (confirmation_code,)).fetchone()

def giveTokensByUserId(cursor, id, qty):
	cursor.execute('UPDATE users SET tokens=tokens+? WHERE user_id=?', (qty, id))

def createTransaction(cursor, user_id, response):
	cursor.execute('INSERT INTO transactions (user_id,stamp,body) values (?,CURRENT_TIMESTAMP,?)', (user_id, response))

def getSiteSettings(cursor):
	return {row['key']: row['value'] for row in cursor.execute("SELECT * FROM site_settings").fetchall()}

def setSiteSetting(cursor, key, value):
	cursor.execute('UPDATE site_settings SET value=? WHERE key=?', (value, key))

def setSiteSettings(cursor, key_values):
	for key, value in key_values.items():
		setSiteSetting(cursor, key, value)

def getSiteHeaderLinks(cursor):
	return {row['text']: row['link'] for row in cursor.execute("SELECT * FROM site_header_links").fetchall()}

def getPosts(cursor):
	return cursor.execute("SELECT * FROM posts").fetchall()

def getPostById(cursor, id):
	return cursor.execute("SELECT * FROM posts WHERE post_id=?", (id,)).fetchone()

def createPost(cursor, title, author, timestamp, content, summary):
	cursor.execute('INSERT INTO posts (post_id, title, author, timestamp, content, summary) VALUES (?, ?, ?, ?, ?, ?)', (str(uuid.uuid4()), title, author, timestamp, content, summary))

def createPostNow(cursor, title, author, content, summary):
	createPost(cursor, title, author, int(time.time()), content, summary)

def updatePostById(cursor, id, title, author, timestamp, content, summary):
	cursor.execute('UPDATE posts SET title=?, author=?, timestamp=?, content=?, summary=? WHERE post_id=?', (title, author, timestamp, content, summary, id))

def updatePostByIdNow(cursor, id, title, author, content, summary):
	updatePostById(cursor, id, title, author, int(time.time()), content, summary)

def deletePostById(cursor, id):
	cursor.execute('DELETE FROM posts WHERE post_id=?', (id,))