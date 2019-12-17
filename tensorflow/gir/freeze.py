from tensorflow.python.tools import freeze_graph

freeze_graph.freeze_graph('tensorflowModel.pbtxt', "", False,
                          './tensorflowModel.ckpt', "output/softmax",
                           "save/restore_all", "save/Const:0",
                           'frozentensorflowModel.pb', True, ""
                         )
