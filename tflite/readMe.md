# Attempting to create TFLite Models

We already have a bunch of models trained up on Darknet ("darknet/weights"). 

Tried 3 different approaches (none worked so far) to create TFLite file:

1. Convert Darknet -> TensorFlow -> TFLite
    
    * According to [AlexeyAB Branch](https://github.com/AlexeyAB/darknet#yolo-v3-in-other-frameworks), use either [tensorflow-yolo-v3](https://github.com/mystic123/tensorflow-yolo-v3) or [DW2TF](https://github.com/jinyu121/DW2TF)'s repos to conver to TensorFlow.
    * tensorflow-yolo-v3:
        - can either make a "saved_model" folder with checkpoint/ckpt files (convert_weights.py), or create a frozen_model.pb file (convert_weights_pb.py)
        - with the saved model, you have to freeze it to get the frozen model using freeze_graph.py (online). However, freezing it wasn't work because something about the input tensors?
        - with the frozen model, I get the error "RuntimeError: MetaGraphDef associated with tags {'serve'} could not be found in SavedModel."
    * DWT2F:
        - creates a folder with checkpoint/.ckpt files AND a frozen_model.pb file
        - with the frozen_model.pb file, when you try to convert it to tflite, it says that it needs to be frozen. something must be wrong with the conversion?

2. Creating a TensorFlow model

    * I tried following [this tutorial](https://towardsdatascience.com/custom-object-detection-using-tensorflow-from-scratch-e61da2e10087)
        - For image annotations, use [Pascal VOC annotation format](https://gist.github.com/Prasad9/30900b0ef1375cc7385f4d85135fdb44)
        - I had to edit the create\_tf\_record.py script, so use my modified version
            - If you have a lot of image files, it will create multiple train and val records. When you train, instead of passing in a single .record file, you can try using the TensorFlow Dataset option to pass in multiple files. (I didn't have time to try this)
        - As of mid 2019, TF was updated to 2.0, and train.py was put in the legacy folder. Unfortunately, this means a whole chain of dependencies was broken, like how you need to downgrade TF, CUDA, and cudNN for train.py to work. Also unfortunately, there are no tutorials on the new way of training (model_main.py). 
        - After prepping all the data and everything, I just couldn't seem to get it to train. I was fiddling around with versions for tf/cuda/cudNN, but I just got a lot of errors, different for each version combination.
    * Tensorflow is not currently compatible with Python3.7+. Please use Python3.6 or below.

3. Creating a PyTorch model

    * This tutorial for creating a [detectron2 model](https://gilberttanner.com/blog/detectron-2-object-detection-with-pytorch).
        - here's some [pre-existing models](https://modelzoo.co/model/detectron-models-for-object-detection)


Other files:

    * All the #\_liteconvert.py files are different ways to convert tensorflow to tflite that I found online. Mostly based on the python API, some for tf1, some for tf2.



