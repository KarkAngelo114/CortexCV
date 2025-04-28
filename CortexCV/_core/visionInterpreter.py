from .._utils import suppressor, ModelType
suppressor.suppress()
import tensorflow as tf
from onnxruntime import *


def cortexOperation(input_shape, models = [], labels = []):

    class_names = []
    individual_class_predictions = []
    outputs = []
    model_accuracies = []

    for label in labels:
        with open(f'{label}', 'r') as data:
            for line in data:
                class_names.append(line.strip())

    for trained_model in models:
        model_interpreter, model_format = ModelType.getModelType(trained_model)

        for class_name_index, className in enumerate(class_names):
            pass
            