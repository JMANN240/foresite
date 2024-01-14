from flask import make_response, redirect, request, url_for, flash
from functools import wraps
import re
import sqlite3
from PIL import Image, ImageDraw, ImageFont

def dict_factory(cursor, row):
	d = {}
	for i, col in enumerate(cursor.description):
		d[col[0]] = row[i]
	return d

def get_db():
	con = sqlite3.connect('database.db')
	con.row_factory = dict_factory
	return con

def uncached_redirect(location, code=303):
	res = make_response(redirect(location, code=code))
	res.cache_control.max_age = 0
	return res

def getUserSession():
	session_id = request.cookies.get('session_id')
	if session_id is None:
		return None
	con = get_db()
	cur = con.cursor()
	res = cur.execute('SELECT * FROM users INNER JOIN sessions ON users.user_id = sessions.user_id WHERE sessions.session_id = ?', (session_id,))
	user_session = res.fetchone()
	return user_session

def requires_authority(authority):
	def requires_authority_inner(f):
		@wraps(f)
		def inner(*args, **kwargs):
			user_session = getUserSession()
			if user_session is None:
				return uncached_redirect(url_for('login'))
			if user_session['authority'] < authority:
				flash('You do not have permission to access that page.')
				return uncached_redirect(url_for('index'))
			setattr(request, 'user_session', user_session)
			return f(*args, **kwargs)
		return inner
	return requires_authority_inner

requires_login = requires_authority(0)

def requires_db(f):
	@wraps(f)
	def inner(*args, **kwargs):
		con = get_db()
		setattr(request, 'db', con)
		return f(*args, **kwargs)
	return inner

'''
# Markdown
### A cool new way to format text
[/static/markdown.png]
Here is a cool new thing. You can even make buttons!
(filled!|/filled) (-outlined!|/outlined-)
So start using markdown today!
'''

class MarkdownLineMatcher:
	def __init__(self, pattern, replacement_function):
		self.pattern = re.compile(pattern)
		self.replacement_function = replacement_function

def title_line_replacement(match):
	return f"<h1 class='huge'>{match.group(1)}</h1>"

def h1_line_replacement(match):
	return f"<h1>{match.group(1)}</h1>"

def h2_line_replacement(match):
	return f"<h2>{match.group(1)}</h2>"

def image_line_replacement(match):
	return f"<div class='center'><img src='{match.group(1)}'></div>"

def button_line_replacement(match):
	button_re = re.compile('\((.+?)\|(.+?)\)')
	html = '<div>'
	for button_match in button_re.findall(match.group(0)):
		html += f"<a class='btn' href='{button_match[1]}'>{button_match[0]}</a>"
	html += '</div>'
	return html

def hr_line_replacement(match):
	return f"<hr>"

def p_line_replacement(match):
	return f"<p>{match.group(1)}</p>"

def renderMarkdown(markdown):
	markdown_lines = markdown.split('\n')
	html_lines = []
	for markdown_line in markdown_lines:
		title_line = MarkdownLineMatcher('^# (.+)$', title_line_replacement)
		h1_line = MarkdownLineMatcher('^## (.+)$', h1_line_replacement)
		h2_line = MarkdownLineMatcher('^### (.+)$', h2_line_replacement)
		image_line = MarkdownLineMatcher('^\[(.+)\]$', image_line_replacement)
		button_line = MarkdownLineMatcher('^(?:\(.+?\|.+?\) ?)+$', button_line_replacement)
		hr_line = MarkdownLineMatcher('^---$', hr_line_replacement)
		p_line = MarkdownLineMatcher('^(.+)$', p_line_replacement)

		line_res = (
			title_line,
			h1_line,
			h2_line,
			image_line,
			button_line,
			hr_line,
			p_line
		)

		for line_re in line_res:
			match = line_re.pattern.match(markdown_line)
			if match is not None:
				html_lines.append(line_re.replacement_function(match))
				break
	return '\n'.join(html_lines)

def generateFavicon(letter, fg, bg, size=32, serifs=False):
	image = Image.new("RGBA", (size, size), bg)
	font_family = "EBGaramond-Bold.ttf" if serifs else "Roboto-Bold.ttf"
	font = ImageFont.truetype(font_family, size)
	_, top, _, bottom = font.getbbox(letter)
	height = bottom-top
	draw = ImageDraw.Draw(image)
	draw.text((size/2, (size/2)+(height/2)), letter, font=font, fill=fg, anchor='mb')
	return image