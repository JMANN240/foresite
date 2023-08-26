#!/usr/bin/bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
cat setup.sql | sqlite3 database.db
