DROP TABLE users;
DROP TABLE sessions;
DROP TABLE site_settings;
DROP TABLE site_header_links;
DROP TABLE site_pages;

CREATE TABLE users (
	user_id TEXT PRIMARY KEY,
	email TEXT UNIQUE NOT NULL,
	username TEXT UNIQUE NOT NULL,
	passhash TEXT NOT NULL,
	first_name TEXT NOT NULL,
	last_name TEXT NOT NULL,
	verified INTEGER NOT NULL DEFAULT FALSE,
	confirmation_code TEXT NOT NULL,
	authority INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE sessions (
	session_id TEXT NOT NULL,
	user_id TEXT NOT NULL,
	created INTEGER NOT NULL,
	PRIMARY KEY (session_id, user_id)
);

CREATE TABLE site_settings (
	key TEXT NOT NULL,
	value TEXT NOT NULL,
	PRIMARY KEY (key)
);

INSERT INTO site_settings (key, value) VALUES ('name', 'ForeSite');
INSERT INTO site_settings (key, value) VALUEs ('primary-color', '#007bff');
INSERT INTO site_settings (key, value) VALUEs ('secondary-color', '#202020');
INSERT INTO site_settings (key, value) VALUEs ('tertiary-color', '#808080');
INSERT INTO site_settings (key, value) VALUEs ('danger-color', '#b82626');

CREATE TABLE site_header_links (
	text TEXT NOT NULL,
	link TEXT NOT NULL,
	position INTEGER NOT NULL,
	PRIMARY KEY (position)
);

INSERT INTO site_header_links (text, link) VALUES ('Home', '/');
INSERT INTO site_header_links (text, link) VALUES ('About', '/about');
INSERT INTO site_header_links (text, link) VALUES ('Gallery', '/gallery');

CREATE TABLE site_pages (
	route TEXT,
	title TEXT,
	content TEXT,
	PRIMARY KEY (route)
);