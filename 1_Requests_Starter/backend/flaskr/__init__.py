import os
import sys
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy  # , or_
from flask_cors import CORS
import random

from models import setup_db, Book, db

BOOKS_PER_SHELF = 8


def paginate_books(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * BOOKS_PER_SHELF
    end = start + BOOKS_PER_SHELF

    books = [book.format() for book in selection]
    current_books = books[start:end]

    return current_books


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/books')
    def show_books():
        selection = Book.query.order_by(Book.id).all()
        current_books = paginate_books(request, selection)

        if len(current_books) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'books': current_books,
            'total_books': len(selection)
        })

    @app.route('/books/<int:book_id>/rating', methods=['PATCH'])
    def update_rating(book_id):
        book = Book.query.get(book_id)

        try:
            book.rating = request.get_json()['rating']
            book.update()

        except:
            db.session.rollback()
            print(sys.exc_info())

        finally:
            db.session.close()
            return jsonify({'success': True})

    @app.route('/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        try:
            book = Book.query.filter(Book.id == book_id).one_or_none()

            if book is None:
                abort(404)

            book.delete()
            selection = Book.query.order_by(Book.id).all()
            current_books = paginate_books(request, selection)

            return jsonify({
                'success': True,
                'deleted': book_id,
                'books': current_books,
                'total_books': len(Book.query.all())
            })

        except:
            abort(422)

    @app.route('/books/create', methods=['POST'])
    def create_book():
        body = request.get_json()
        title = body.get('title', None)
        author = body.get('author', None)
        rating = body.get('rating', None)
        try:
            new_book = Book(
                title=title,
                author=author,
                rating=rating
            )
            new_book.insert()

            selection = Book.query.order_by(Book.id).all()
            current_books = paginate_books(request, selection)

        except:
            db.session.rollback()

        finally:
            db.session.close()

            return jsonify({
                'success': True,
                'created': new_book.id,
                'books': current_books,
                'total_books': len(Book.query.all())
            })

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'bad request'
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Not found'
        })

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable'
        })

    return app
