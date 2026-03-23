
def attention_to(websocket, node_id):

    websocket.send_json({
        "operation": "ATTENTION",
        "node_id": node_id
    })