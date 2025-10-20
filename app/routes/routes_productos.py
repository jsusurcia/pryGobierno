from flask import Blueprint, request, jsonify
from app.controllers.control_productos import ControlProducto

producto_bp = Blueprint('producto_bp', __name__)

@producto_bp.route('/productos/<int:id_producto>', methods=['GET'])
def obtener_producto_ID(id_producto):
    rpta = dict()
    rpta['data'] = []
    
    producto = ControlProducto.buscar_por_ID(id_producto)
    
    if producto is not None:
        rpta['status'] = 'success'
        rpta['message'] = 'Producto encontrado'
        rpta['data'] = producto
    else:
        rpta['status'] = 'error'
        rpta['message'] = 'No se encontró el producto'
        
    return jsonify(rpta)

@producto_bp.route('/productos', methods=['GET'])
def obtener_productos():
    rpta = dict()
    rpta['data'] = []
    
    productos = ControlProducto.buscar_todos()
    
    if productos is not None:
        rpta['status'] = 'success'
        rpta['message'] = 'Productos encontrados'
        rpta['data'] = productos
    else:
        rpta['status'] = 'error'
        rpta['message'] = 'No se encontraron productos'
        
    return jsonify(rpta)

