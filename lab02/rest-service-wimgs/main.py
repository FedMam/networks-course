import uuid
import os
import io

from flask import Flask, request, jsonify, send_file
from PIL import Image
from pathlib import Path

SERVER_FILES_DIR = f'{Path(__file__).resolve().parent}/server-files'

app = Flask('lab02')


class Product:
    def __init__(self, id: int, name: str, description: str, image_file: str | None = None):
        self.id = id
        self.name = name
        self.description = description
        self.image_file = image_file
    
    def set_image_file(self, image_file: str | None):
        self.image_file = image_file

    def to_dict(self):
        # TODO: add image
        return {'id': self.id,
                'name': self.name,
                'description': self.description,
                **({} if self.image_file is None else {'icon': self.image_file})}

    def to_json(self):
        return jsonify(self.to_dict())
    
    @staticmethod
    def from_json(json, id: int | None = None):
        return Product(id if id is not None else json['id'], json['name'], json['description'])


products_database: dict[int, Product] = {}
id_counter = -1

error_message_not_json = lambda: {'error': 'request must be JSON'}
error_message_not_found = lambda product_id: {'error': f'product #{product_id} does not exist'}
error_message_bad_id = lambda product_id: {'error': f'\'{product_id}\' is not a number'}
error_message_no_file = lambda: {'error': 'no file'}
error_message_many_files = lambda: {'error': 'too many files'}
error_message_no_image = lambda product_id: {'error': f'no image for product #{product_id}'}


def new_id():
    global id_counter
    id_counter += 1
    return id_counter


@app.post('/product')
def new_product():
    if request.is_json:
        product = Product.from_json(request.get_json(), id=new_id())
        products_database[product.id] = product
        return product.to_dict(), 201
    return error_message_not_json(), 415


@app.get('/product/<product_id>')
def get_product(product_id):
    if not product_id.isdecimal():
        return error_message_bad_id(product_id), 400
    product_id = int(product_id)

    product = products_database.get(product_id)
    if not product:
        return error_message_not_found(product_id), 404
    return product.to_dict(), 200


@app.put('/product/<product_id>')
def update_product(product_id):
    if not product_id.isdecimal():
        return error_message_bad_id(product_id), 400
    product_id = int(product_id)

    if request.is_json:
        product = products_database.get(product_id)
        if not product:
            return error_message_not_found(product_id), 404
        json = request.get_json()
        if 'name' in json:
            product.name = json['name']
        if 'description' in json:
            product.description = json['description']
        return product.to_dict(), 200
    return error_message_not_json(), 415


@app.delete('/product/<product_id>')
def delete_product(product_id):
    if not product_id.isdecimal():
        return error_message_bad_id(product_id), 400
    product_id = int(product_id)

    if product_id not in products_database:
        return error_message_not_found(product_id), 404
    product = products_database[product_id]
    del products_database[product_id]
    return product.to_dict(), 200


@app.get('/products')
def get_all_products():
    return [products_database[id].to_dict() for id in products_database]


@app.post('/product/<product_id>/image')
def set_product_image(product_id):
    if not product_id.isdecimal():
        return error_message_bad_id(product_id), 400
    product_id = int(product_id)

    if product_id not in products_database:
        return error_message_not_found(product_id), 404
    product = products_database[product_id]

    if not request.data:
        return error_message_no_file(), 400
    
    try:
        img = Image.open(io.BytesIO(request.data))
        img_file = f'{uuid.uuid4().hex}.png'
        img.save(f'{SERVER_FILES_DIR}/{img_file}', format='png')
        product.set_image_file(img_file)
    except Exception as E:
        return {'error': f'image parsing failed: {E}'}, 400
    
    return '', 204


@app.get('/product/<product_id>/image')
def get_product_image(product_id):
    if not product_id.isdecimal():
        return error_message_bad_id(product_id), 400
    product_id = int(product_id)

    if product_id not in products_database:
        return error_message_not_found(product_id), 404
    product = products_database[product_id]

    if not product.image_file:
        return error_message_no_image(product_id), 404
    
    img_path = f'{SERVER_FILES_DIR}/{product.image_file}'
    return send_file(img_path, mimetype='image/png'), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)