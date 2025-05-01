from .._utils import suppressor, ModelType, _ANSI
suppressor.suppress()
import tensorflow as tf
from onnxruntime import *
import cv2

print(f"\n{_ANSI.cyan()}I, CortexCV, is now {_ANSI.yellow()}live{_ANSI.reset()}\n")


def cortexOperation(threshold, frame, input_shape, models=[], labels=[]):
    # ret, frame = vision.read()

    # if not ret:
    #     raise Exception(f"{_ANSI.red()} Unable to process live image feed {_ANSI.reset()}")
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB (optional but good for models)
    class_names = []

    for model_index, trained_model in enumerate(models):
        model_interpreter, model_format = ModelType.getModelType(trained_model)

        # Reset and load class names for this model
        class_names.clear()

        with open(labels[model_index], 'r') as data:
            for line in data:
                class_names.append(line.strip())

        # Preprocess the captured frame (vision)
        img = tf.image.resize(frame, input_shape)
        img = tf.expand_dims(img, axis=0)
        img = tf.cast(img, dtype=tf.float32)

        # Run inference
        if model_format == ".tflite":
            model_interpreter.set_tensor(model_interpreter.get_input_details()[0]['index'], img.numpy())
            model_interpreter.invoke()
            output = model_interpreter.get_tensor(model_interpreter.get_output_details()[0]['index'])[0]
        elif model_format == ".h5":
            output = model_interpreter.predict(img.numpy())[0]
        elif model_format == ".onnx":
            input_name = model_interpreter.get_inputs()[0].name
            output_name = model_interpreter.get_outputs()[0].name
            output = model_interpreter.run([output_name], {input_name: img.numpy()})[0][0]
        else:
            raise ValueError("Unsupported model format.")

        # Interpret output
        output = tf.nn.softmax(output).numpy()  # Make it probabilities
        top_class_index = tf.argmax(output).numpy()
        top_score = output[top_class_index]

        if top_score >= threshold:  # 90% confidence threshold
            predicted_class = class_names[top_class_index]
            return predicted_class, top_score * 100  # return as percentage
        
        

    # If no model meets N% confidence, return something like "Unknown"
    return "Unknown", 0

            