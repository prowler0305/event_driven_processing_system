from flask import Blueprint
from order_api.resources.order_resource import OrderResource

orders_bp = Blueprint("orders_bp", __name__)

order_view = OrderResource.as_view("orders")

orders_bp.add_url_rule("/orders", view_func=order_view, methods=["POST"])