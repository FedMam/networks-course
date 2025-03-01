from flask import Flask, request, jsonify

app = Flask('lab02')


class Product:
    def __init__(self, id: int, name: str, description: str):
        self.id = id
        self.name = name
        self.description = description
    
    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'description': self.description}

    def to_json(self):
        return jsonify(self.to_dict())
    
    @staticmethod
    def from_json(json, id: int | None = None):
        return Product(id if id is not None else json['id'], json['name'], json['description'])


products_database: dict[int, Product] = {}
id_counter = -1

error_message_umt = lambda: {'error': 'request must be JSON'}
error_message_not_found = lambda product_id: {'error': f'product #{product_id} does not exist'}
error_message_bad_id = lambda product_id: {'error': f'\'{product_id}\' is not a number'}


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
    return error_message_umt(), 415


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
    return error_message_umt(), 415


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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)