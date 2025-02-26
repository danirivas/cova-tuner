#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import base64
import json
from typing import Optional

import cv2
import numpy as np
import pandas as pd
from flask import Flask, Response
from flask_restful import Api, Resource, reqparse

from cova.dnn.infer import Model, ModelTF

app = Flask(__name__)
api = Api(app)

loaded_models: dict[str, Model] = {}
model_in_use = ""


class Infer(Resource):
    def get(self):
        data = pd.DataFrame([], columns=["test"])
        data = data.to_dict()
        return {"data": data}, 200

    def post(self):
        print("received post request")
        parser = reqparse.RequestParser()

        parser.add_argument("img", required=True)
        parser.add_argument("model", required=True)
        # parser.add_argument('iou_threshold', required=False)

        args = parser.parse_args()

        if args.model != "" and args.model not in loaded_models.keys():
            return {"message": "Invalid model."}, 401

        img = base64.b64decode(args.img)
        nparr = np.frombuffer(img, np.uint8)
        img = cv2.imdecode(nparr, flags=1)

        if args.model != "":
            detector = loaded_models[args.model]
        else:
            detector = loaded_models[model_in_use]

        results = detector.run([img])
        return Response(
            response=json.dumps(
                {
                    "data": results,
                }
            ),
            status=200,
            mimetype="application/json",
        )


api.add_resource(Infer, "/infer")


def start_server(
    model: str,
    model_id: str = "default",
    label_map: Optional[str] = None,
    port: int = 6000,
):
    global loaded_models
    global model_in_use
    global app
    global api

    detector = ModelTF(model, label_map)
    loaded_models[model_id] = detector
    model_in_use = model_id

    app.run(port=port)


if __name__ == "__main__":
    # use argparse
    args = argparse.ArgumentParser()
    args.add_argument("--model", type=str, required=True, help="Path to model.")
    args.add_argument("--model_id", type=str, required=True)
    args.add_argument("--label_map", type=str, default=None)
    args.add_argument("--port", type=int, default=6000)
    params = args.parse_args()

    start_server(
        model=params.model,
        model_id=params.model_id,
        label_map=params.label_map,
        port=params.port,
    )
