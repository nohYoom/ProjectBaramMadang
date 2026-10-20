import os
import json
from flask import Blueprint, render_template, redirect, url_for, current_app

main_bp = Blueprint('main', __name__)

# ============================================================
# CHANGE THIS to switch viewer: 'text', 'pdf', 'mixed', 'book'
VIEW_TYPE = 'text'
# ============================================================

# Dict matches DB schema from diagram
DEMO_ITEM = {
    'media_id': 1,
    'type': 'articles',          # articles, images, zines
    'title': 'Sample Article Title',
    'filter': 'science',
    'publication_date': '2026-10-17',
    'author_id': 1,
    'author_name': 'Test Author',
}

# Which file to load for each view type
DATA_FILES = {
    'text': 'uploads/sample/article.txt',
    'pdf': 'uploads/sample/document.pdf',
    'mixed': 'uploads/sample/content.json',
    'book': 'uploads/sample/document.pdf',
    'epub': 'uploads/sample/book.epub',
}


@main_bp.route('/')
def index():
    return redirect(url_for('main.viewer'))


@main_bp.route('/viewer')
def viewer():
    item = DEMO_ITEM.copy()
    item['view_type'] = VIEW_TYPE
    data_file = DATA_FILES[VIEW_TYPE]
    file_path = os.path.join(current_app.static_folder, data_file)

    if VIEW_TYPE == 'text':
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                item['content'] = f.read()
        else:
            item['content'] = f'[File not found: place a text file at static/{data_file}]'

    elif VIEW_TYPE in ('pdf', 'book', 'epub'):
        item['file_url'] = url_for('static', filename=data_file)

    elif VIEW_TYPE == 'mixed':
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                item['content_blocks'] = json.load(f)
        else:
            item['content_blocks'] = [
                {'type': 'text', 'content': f'[File not found: place content.json at static/{data_file}]'}
            ]

    return render_template('viewer.html', item=item)
