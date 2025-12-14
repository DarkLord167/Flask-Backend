from app import db
from app.models import User, Post
import click
import json


@click.command('populate-db')
@click.argument('table')
@click.argument('json_file')
def populate_db(table, json_file):
    with open(json_file) as f:
        data = json.load(f)
        
        if table == 'user':
            for entry in data:
                user = User(username=entry['username'], email=entry['email'])
                user.set_password_hash('')
                db.session.add(user)
        elif table == 'post':
            for entry in data:
                post = Post(body=entry['body'], user_id=entry['id'])
                db.session.add(post)
        else:
            return print('Table name is incorrect!')
        
        db.session.commit()
        print('Finishid populating database')

