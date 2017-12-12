import numpy as np
import os
import six.moves.urllib as urllib
import tarfile
import tensorflow as tf
from PIL import Image
from app.object_detection import label_map_util
from app.object_detection import visualization_utils as vis_util


class ImageProcessor():
    """performs object detection on an image
    """

    def __init__(self, path_to_model, path_to_labels):
        self._model_name = 'ssd_mobilenet_v1_coco_2017_11_17'
        # Path to frozen detection graph. This is the actual model that is used for the object detection.
        self._path_to_model = path_to_model
        # strings used to add correct label for each box.
        self._path_to_labels = path_to_labels
        self._num_classes = 90
        self._detection_graph = None
        self._labels = dict()
        self._image = None
        self._boxes = None
        self._classes = None
        self._scores = None
        self._num = None

    def setup(self):
        MODEL_FILE = self._model_name + '.tar.gz'
        DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'
        # self.download_model(DOWNLOAD_BASE, MODEL_FILE)
        self.load_model(self._path_to_model)
        self._labels = self.load_labels(self._path_to_labels)

    def download_model(self, url, filename):
        """download a model file from the url and unzip it
        """
        opener = urllib.request.URLopener()
        opener.retrieve(url + filename, filename)
        tar_file = tarfile.open(filename)
        for file in tar_file.getmembers():
            file_name = os.path.basename(file.name)
            if 'frozen_inference_graph.pb' in file_name:
                tar_file.extract(file, os.getcwd())

    def load_model(self, path):
        """load saved model from protobuf file
        """
        self._detection_graph = tf.Graph()
        with self._detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(path, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')

    def load_labels(self, path):
        """load labels from .pb file, and map to a dict with integers, e.g. 1=aeroplane
        """
        label_map = label_map_util.load_labelmap(path)
        categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=self._num_classes,
                                                                    use_display_name=True)
        category_index = label_map_util.create_category_index(categories)
        return category_index

    def load_image_into_numpy_array(self, path):
        """load image into NxNx3 numpy array
        """
        image = Image.open(path)
        (im_width, im_height) = image.size
        return np.array(image.getdata()).reshape((im_height, im_width, 3)).astype(np.uint8)

    def detect(self, image):
        """detect objects in the image
        """
        with self._detection_graph.as_default():
            with tf.Session(graph=self._detection_graph) as sess:
                # Definite input and output Tensors for detection_graph
                image_tensor = self._detection_graph.get_tensor_by_name('image_tensor:0')
                # Each box represents a part of the image where a particular object was detected.
                detection_boxes = self._detection_graph.get_tensor_by_name('detection_boxes:0')
                # Each score represent how level of confidence for each of the objects.
                # Score is shown on the result image, together with the class label.
                detection_scores = self._detection_graph.get_tensor_by_name('detection_scores:0')
                detection_classes = self._detection_graph.get_tensor_by_name('detection_classes:0')
                num_detections = self._detection_graph.get_tensor_by_name('num_detections:0')
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(image, axis=0)
                # Actual detection.
                (self._boxes, self._scores, self._classes, num) = sess.run(
                    [detection_boxes, detection_scores, detection_classes, num_detections],
                    feed_dict={image_tensor: image_np_expanded})
                return self._boxes, self._scores, self._classes, self._num

    def annotate_image(self, image, boxes, classes, scores):
        """draws boxes around the detected objects and labels them

        :return: annotated image
        """
        annotated_image = image.copy()
        vis_util.visualize_boxes_and_labels_on_image_array(
            annotated_image,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            self._labels,
            use_normalized_coordinates=True,
            line_thickness=8)
        return annotated_image

    @property
    def labels(self):
        return self._labels
