import tensorflow as tf

#graph_def_file = "/path/to/Downloads/mobilenet_v1_1.0_224/frozen_graph.pb"
graph_def_file = "tensorflow-yolo-v3/frozen_darknet_yolov3_model.pb"
input_arrays = ["input"]
output_arrays = ["MobilenetV1/Predictions/Softmax"]

converter = tf.lite.TFLiteConverter.from_frozen_graph(
  graph_def_file, input_arrays, output_arrays)
tflite_model = converter.convert()
open("converted_model.tflite", "wb").write(tflite_model)
