'''
Adapted streaming code from Google, uses the gstreamer "api" in
this folder.
Inference times end up being faster than my own queue detection.
'''
import argparse
import time
import re
import svgwrite
import imp
import os
from edgetpu.detection.engine import DetectionEngine
# a streaming library for google
import gstreamer

# load labels from label file
def load_labels(path):
    p = re.compile(r'\s*(\d+)(.+)')
    with open(path, 'r', encoding='utf-8') as f:
       lines = (p.match(line).groups() for line in f.readlines())
       return {int(num): text.strip() for num, text in lines}

# draws the text onto the box
def shadow_text(dwg, x, y, text, font_size=20):
    dwg.add(dwg.text(text, insert=(x+1, y+1), fill='black', font_size=font_size))
    dwg.add(dwg.text(text, insert=(x, y), fill='white', font_size=font_size))

# draws the boxes onto the svg canvas for viewing
def generate_svg(dwg, objs, labels, text_lines):
    width, height = dwg.attribs['width'], dwg.attribs['height']
    for y, line in enumerate(text_lines):
        shadow_text(dwg, 10, y*20, line)
    if objs:
        print("****************************************")

    # iterate through results
    for obj in objs:
        x0, y0, x1, y1 = obj.bounding_box.flatten().tolist()
        x, y, w, h = x0, y0, x1 - x0, y1 - y0
        x, y, w, h = int(x * width), int(y * height), int(w * width), int(h * height)
        percent = int(100 * obj.score)
        label = '%d%% %s' % (percent, labels[obj.label_id])
        shadow_text(dwg, x, y - 5, label)
        dwg.add(dwg.rect(insert=(x,y), size=(w, h), fill_opacity=0, stroke='red'))
        print("DETECTED: " + str(percent) + "%")
        print("Bounding box: " + str(obj.bounding_box.flatten().tolist()))
    print()

# main function of the program
def main():
    default_model_dir = '../models'
    default_model = 'mobilenet_ssd_v2_coco_quant_postprocess_edgetpu.tflite'
    default_labels = 'coco_labels.txt'
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', help='.tflite model path',
                        default=os.path.join(default_model_dir,default_model))
    parser.add_argument('--labels', help='label file path',
                        default=os.path.join(default_model_dir, default_labels))
    parser.add_argument('--top_k', type=int, default=3,
                        help='number of classes with highest score to display')
    parser.add_argument('--threshold', type=float, default=0.4,
                        help='class score threshold')
    args = parser.parse_args()

    # load the label file
    print("Loading %s with %s labels."%(args.model, args.labels))
    engine = DetectionEngine(args.model)
    labels = load_labels(args.labels)
    
    last_time = time.monotonic()
    def user_callback(image, svg_canvas):
      # get the inference time
      nonlocal last_time
      start_time = time.monotonic()
      # perform the image detection
      objs = engine.detect_with_image(image, threshold=args.threshold,
                                    keep_aspect_ratio=True, relative_coord=True,
                                    top_k=args.top_k)
      end_time = time.monotonic()
      text_lines = [
          'Inference: %.2f ms' %((end_time - start_time) * 1000),
          'FPS: %.2f fps' %(1.0/(end_time - last_time)),
      ]
      print(' '.join(text_lines))
      last_time = end_time
      # generates the image for viewing
      generate_svg(svg_canvas, objs, labels, text_lines)

    result = gstreamer.run_pipeline(user_callback)

if __name__ == '__main__':
    main()
