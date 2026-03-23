from flask import request, current_app, jsonify
from flask.views import MethodView
from ..services.order_service import create_order_event


class OrderResource(MethodView):

    def post(self):
        data = request.get_json()
        result = create_order_event(data=data)
        current_app.logger.info(f"Hello from POST method")

        return jsonify({"status": "ok", **result}), 201