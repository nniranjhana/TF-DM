import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import tensorflow as tf

from tensorflow.keras import datasets, layers, models
import numpy as np
import time, sys, random, copy

from src import tfi

(train_images, train_labels), (test_images, test_labels) = datasets.cifar10.load_data()
train_images, test_images = train_images / 255.0, test_images / 255.0

model = models.Sequential()
model.add(layers.Conv2D(32, (3, 3), activation='relu', input_shape=(32, 32, 3)))
model.add(layers.MaxPooling2D((2, 2)))
model.add(layers.Conv2D(64, (3, 3), activation='relu'))
model.add(layers.MaxPooling2D((2, 2)))
model.add(layers.Conv2D(64, (3, 3), activation='relu'))

model.add(layers.Flatten())
model.add(layers.Dense(64, activation='relu'))
model.add(layers.Dense(10))

model.compile(optimizer='adam',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])
'''
# Save the untrained weights for future training with modified dataset
model.save_weights('h5/cnnc-untrained.h5')

model.fit(train_images, train_labels, batch_size=100, epochs=5,
                   validation_data=(test_images, test_labels))

test_loss, test_acc = model.evaluate(test_images,  test_labels, verbose=2)
print("Accuracy with the original dataset:", test_acc)

model.save_weights('h5/cnnc-trained.h5')
'''
conf = sys.argv[1]
filePath = sys.argv[2]
filePath = os.path.join(filePath, "res.csv")

f = open(filePath, "w")
numFaults = int(sys.argv[3])
numInjections = int(sys.argv[4])
offset = 20
num = test_images.shape[0]

totsdc = 0.
start = time.time()
for i in range(numFaults):
    train_labels1 = copy.deepcopy(train_labels);train_images1=copy.deepcopy(train_images)
    model.load_weights('h5/cnnc-trained.h5')
    ind = []
    init = random.sample(range(num), numInjections+offset)
    for i in init:
        test_loss, test_acc = model.evaluate(test_images[i:i+1], test_labels[i:i+1], verbose=0)
        if(test_acc == 1.):
            ind.append(i)
    ind = ind[:numInjections]
    model.load_weights('h5/cnnc-untrained.h5')
    train_images_,train_labels_ = tfi.inject(x_test=train_images1,y_test=train_labels1, confFile=conf)
    
    model.fit(train_images_, train_labels_, batch_size=100, epochs=10,
                    validation_data=(test_images, test_labels), verbose=0)
    sdc = 0.
    for i in ind:
        test_loss, test_acc = model.evaluate(test_images[i:i+1],  test_labels[i:i+1], verbose=0)
        if(test_acc == 0.):
            sdc = sdc + 1.
    f.write(str(sdc/numInjections))
    f.write("\n")
    totsdc = totsdc + sdc
f.write("\n")
f.write(str(totsdc/(numFaults*numInjections)))
f.write("\n")
f.write("Time for %d injections: %f seconds" % (numFaults*numInjections, time.time() - start))
f.close()
