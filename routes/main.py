import os
import json
from flask import Blueprint, render_template, redirect, url_for, current_app, send_file, abort

main_bp = Blueprint('main', __name__)

VIEW_TYPE = 'epub'


DEMO_ITEM = {
    'media_id': 1,
    'type': 'articles',        
    'title': 'Sample Article Title',
    'filter': 'MUN',
    'publication_date': '2026-10-17',
    'author_id': 1,
    'author_name': 'Test Author',
}


DATA_FILES = {
    'pdf': 'uploads/sample/document.pdf',
    'mixed': 'uploads/sample/content.json',
    'epub': 'uploads/sample/article.epub'
}


@main_bp.route('/')
def index():
    return redirect(url_for('main.viewer'))


@main_bp.route('/epub/<path:filename>')
def serve_epub(filename):
    """Serve EPUB files with correct MIME type and headers for epub.js."""
    safe_path = os.path.join(current_app.static_folder, 'uploads', filename)
    if not os.path.isfile(safe_path):
        abort(404)
    return send_file(
        safe_path,
        mimetype='application/epub+zip',
        as_attachment=False,
        download_name=os.path.basename(safe_path),
    )


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

    elif VIEW_TYPE in ('pdf', 'zine'):
        item['file_url'] = url_for('static', filename=data_file)

    elif VIEW_TYPE == 'epub':
        epub_relative = data_file.replace('uploads/', '', 1)
        item['file_url'] = url_for('main.serve_epub', filename=epub_relative)

    elif VIEW_TYPE == 'mixed':
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                item['content_blocks'] = json.load(f)
        else:
            item['content_blocks'] = [
                {'type': 'text', 'content': f'[File not found: place content.json at static/{data_file}]'}
            ]

    return render_template('viewer.html', item=item)
