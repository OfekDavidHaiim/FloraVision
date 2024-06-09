import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

model = tf.keras.models.load_model(f"G:\My Drive\Models\ofek.tf")
IMG_SIZE = (224, 224)

class_names = ['INaturalList', 'healthy', 'not healthy']

def predict(filename):
  img1 = Image.open(filename)
  img1 = img1.resize(IMG_SIZE)
  img1 = np.array(img1)
  img1 = np.expand_dims(img1,axis=0)
  pred1 = model.predict(img1)
  pred1 = tf.nn.softmax(pred1)
  pred1 = tf.argmax(pred1,axis=1).numpy()
  return class_names[pred1[0]]

def predictall(filelist):
  images = []
  for file1 in filelist:
    img1 = Image.open(file1)
    img1 = img1.resize(IMG_SIZE)
    img1 = np.array(img1)
    images.append(img1)
  images = np.array(images)
  pred1 = model.predict(images)
  pred1 = tf.nn.softmax(pred1)
  pred1 = tf.argmax(pred1,axis=1).numpy()
  pred1 = [class_names[x] for x in pred1]
  return pred1


filename = f"G:\\My Drive\\healthy leaf 3.JPG"
p = predict(filename)
print(p)

#file1 = f"G:\My Drive\data\InaturalList\\00a086b438faf55ccef4e2ec828312e1.JPG"
#file3 = f"G:\My Drive\\data\\NotHealthy\\000ec6ea-9063-4c33-8abe-d58ca8a88878___PSU_CG 2169.JPG"
#file2 = f"G:\My Drive\\data\\healthy\\000bf685-b305-408b-91f4-37030f8e62db___GH_HL Leaf 308.1.JPG"
#filelist = [file1,file2,file3]

#p2 = predictall(filelist)
#print(p2)


