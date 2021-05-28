# -*- coding: utf-8 -*-
"""Dog_Identification_TF.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1z-90Ngoa7jyOQ1hPs9wkWocu6tg5sdTR

# Dog Breed Identification ML Project

## Problem Identification
A multiclass modelling project using tensorflow and tensorflow.hub aimed at identifying dog breed from an image.

## Data
Training, Test, and evaluation data obtained from a closed Kaggle competition.
https://www.kaggle.com/c/dog-breed-identification/data

There are 10,000+ photos
## Evaluation
Submissions are evaluated on Multi Class Log Loss between the predicted probability and the observed target.

## Features
Unstructured data consisting of photos of dogs.

There are 120 target labels or dog breeds.
"""

# Getting our tools
import pandas as pd
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import os
from datetime import datetime

print('TF Version:',tf.__version__ )
print('TF Hub Version:', hub.__version__)

# Make sure that a GPU has been enabled
print('GPU Available' if tf.config.list_physical_devices('GPU') else 'Not Available')

"""# Data Eploration (EDA)
We need to convert our data into a format tensor flow can process (tensors).

These images need to be converted into numerical format.
"""

label_df = pd.read_csv('/content/drive/MyDrive/Dog_Vision/labels.csv')
label_df.head(5)

label_df['breed'].value_counts(), label_df['breed'].value_counts().mean()

label_df['breed'].value_counts().plot.bar(figsize=(15,15))

"""Though there is a decent range of value counts for each label, the data has a slight right skew, which means our accuracy between labels should be fairly consistent.

Yet many of our labels have value counts below 100, which is the optimal minimum per class.
"""

from IPython.display import Image
bluetick_image = Image('drive/My Drive/Dog_Vision/train/00214f311d5d2247d5dfe4fe24b2303d.jpg')
bluetick_image

"""We need to create a list of images location and their labels so that they can be accessed as images.


"""

label_df['id'] = label_df['id'].apply(lambda x:'drive/My Drive/Dog_Vision/train/' + str(x) +'.jpg')
label_df['id'][0]

label_dummies = pd.get_dummies(label_df['breed'])
label_dummies.head(5)
breed_labels= label_dummies.columns

treated_df = pd.concat([label_df, label_dummies], axis=1)
treated_df = treated_df.drop('breed', axis=1)
treated_df.head(5)

treated_df.dtypes

"""## Treating Data, Creating Data Sets

We first need to ready the data by transforming it into tensors.

Then we need to split the data into training and validation sets.
"""

NUM_IMAGES = 1000 #@param {type:'slider', min:1000, max:12000, step:100}

from sklearn.model_selection import train_test_split
X = treated_df['id']
y = treated_df.drop('id', axis=1)
X_train, X_val, y_train, y_val = train_test_split(X[:NUM_IMAGES],y[:NUM_IMAGES],
                                                  test_size=0.2, random_state=27)
X_train.shape, X_val.shape, y_train.shape, y_val.shape

from matplotlib.pyplot import imread
def convert_image_to_tensor(file):
  file = tf.io.read_file(file) 
  # convert each file path to an image
  image = tf.io.decode_jpeg(file)
  # convert rbg values to float 0-1 to normalize data and make for easier computing
  tensor = tf.image.convert_image_dtype(image, tf.float32)
  # normalize image size for easier algorithm comparison
  tensor = tf.image.resize(tensor, size=[224, 224])
  return tensor

def get_tensor_tuple(X, y):
  # The image file_path needs to be converted into a tensor
  image = convert_image_to_tensor(X)
  # The target label needs to be a tensor too.
  label = y
  #return the image and target label as a tuple pair. 
  return image, label

"""## Batch Creation

We need to create batches of the training data.

This is necessary because the batch could exceed memory that the algorithm can process, ruining our fit.

The format necessary is a list of tuples


"""

BATCH_SIZE = 32
def create_batch(X, y=None, batch_size=BATCH_SIZE, val_data=False, test_data=False):
  # If else clauses to determine workflow for data type.
  if test_data:
    print('Creating test data batch...')
    data =tf.data.Dataset.from_tensor_slices(tf.constant(X))
    data_batch = data.map(convert_image_to_tensor).batch(BATCH_SIZE)
    return data_batch
  elif val_data:
    print('Creating validation data batch...')
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X),tf.constant(y)))
    data_batch = data.map(get_tensor_tuple).batch(BATCH_SIZE)
    return data_batch
  else:
    print('Creating training data batch...')
    data = tf.data.Dataset.from_tensor_slices((tf.constant(X),tf.constant(y)))
    # If it is training data we will shuffle the data
    data = data.shuffle(buffer_size=len(X))
    data_batch = data.map(get_tensor_tuple).batch(BATCH_SIZE)
    return data_batch

val_data = create_batch(X_val,y_val, val_data=True)
val_data.element_spec

"""## Vizualizing Batch Data

We need to visualize our batch data so it can be easier to understand
"""

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import matplotlib.pyplot as plt

def plot_batch(images, labels):
  #Displays 25 images from a batch
  fig = plt.figure(figsize=(10,10),)
  for i in range(25):
    ax = plt.subplot(5,5,i+1)
    plt.imshow(images[i])
    #Matches index of positive label with column name/breed
    plt.title(breed_labels[labels[i].argmax()],size=24)
    plt.axis('off')
    plt.subplots_adjust(left=0,bottom=0,right=3,top=3)

val_images, val_labels = next(val_data.as_numpy_iterator())
plot_batch(val_images, val_labels)

train_data = create_batch(X_train, y_train)
train_data.element_spec

train_images, train_labels = next(train_data.as_numpy_iterator())
plot_batch(train_images, train_labels)

"""# Modelling Data

We are aiming to implement transfer learning.

We need to first outline:

* Input shape (what are the specs of data fed to the model)
* Output shape (what are the specs of data returned from the model)
* Transfer model URL (where are we finding the pre-existing model for transfer learning)
"""

INPUT_SHAPE = [None, 224, 224, 3] # Batch, length, width, and color channel

OUTPUT_SHAPE = len(y.iloc[0])
# model obtained from tf.hub
MODEL_URL = "https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/classification/5"

"""## Create Model Function
We are ready to write a  function that streamlines our model implementation. It will:
* Use Input shape, output shape and model as parameters
* Instruct the model how the layers should be structured in sequential format with keras.
* Compiles the model and describes/tunes its performance.
* Builds the model.
* Returns the model.
"""

def create_model(input_shape=INPUT_SHAPE, output_shape=OUTPUT_SHAPE, model_url=MODEL_URL):
  print('Creating the model using "https://tfhub.dev/google/imagenet/mobilenet_v2_130_224/classification/5"')
  model = tf.keras.Sequential([
    hub.KerasLayer(model_url),
    tf.keras.layers.Dense(OUTPUT_SHAPE,
                          activation='softmax')
  ])
  # Compiles the model 
  model.compile(
                loss=tf.keras.losses.CategoricalCrossentropy(),
                optimizer=tf.keras.optimizers.Adam(),
                metrics=['accuracy'])
  # Builds the model
  model.build(INPUT_SHAPE)  # Batch input shape.
  return model

model = create_model()
summary = model.summary()

"""## Creating callback functions
We need to create callback functions to report how our model is performing as it trains

**TensorBoard**
Logs progress of model training. To implement we will:
* load TensorBoard Notebook
* Link TensorBoard with our `fit()` function.
* Visualize our TensorBoard logs.

**EarlyStopping**
Stops the program if the model is overfit.
"""

# Commented out IPython magic to ensure Python compatibility.
# Load tensorboard
# %load_ext tensorboard

def tensorboard_callback():
  log_dir = os.path.join('drive/My Drive/Dog_Vision/logs/',
                         # Logs will be named the log time
                         datetime.now().strftime('%Y%m%d-%H:%M:%S'))
  callback = tf.keras.callbacks.TensorBoard(log_dir)
  return callback

def earlystopping_callback():

  callback = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=3)
  return callback

NUM_EPOCHS = 100

# check to make sure that the GPU is still available
print('GPU Available'if tf.config.list_physical_devices('GPU') else 'GPU not currently available')

"""## Train Model Function
We are finally able to functionalize the training of our model

This function will incorporate the model creation funciton and the callback functions to fit and train the model in a more streamlined fashion.
"""

def train_model():
  model = create_model()

  tensorboard= tensorboard_callback()

  earlystopping = earlystopping_callback()

  model.fit(x=train_data, 
            validation_data=val_data,
            validation_freq=1,
            epochs=NUM_EPOCHS,
            callbacks=[tensorboard, earlystopping],
            shuffle=True,
            )
  return model

model = train_model()

"""Our model is overfitting the data. It's accuracy is already 100% on the training set, but it's validation accuracy is stagnant at 64%

We need to find a way to prevent overfitting so that our model can continue to learn. We will handle this after we test the model.

First we will visualize the tensorboard logs.
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir drive/My\ Drive/Dog_Vision/logs/

"""## Prediction and Testing of the Model

We have not visualized how the model is working, we need to more fine grained information about predictions and certainty.
"""

predictions = model.predict(val_data, verbose=1)
predictions, predictions.shape

# predictions returns the activation for each label. We can see the final prediction and the label with the following code
print(f'The model is {predictions[0].max()*100}% confident the label is {breed_labels[predictions[0].argmax()]}')

"""## Comparing Predictions with Text and Label.

We need to unbatch our val_data, convert the image tensor to an image, and display the original image and label next to the predicted label and confidence interval.
"""

def unbatch_data_with_preds(batch_data, predictions):
  """
  Compares unbatched image-label pairs with the model's predictions
  """
  real_images = []
  real_labels = []
  for image, label in batch_data.unbatch():
    real_images.append(image)
    real_labels.append(breed_labels[np.array(label).argmax()])
  # Creates a list of prediction strings for each prediction array in the predictions inputted
  float_formatter = "{:0.0f}"
  pred_certainty = [float_formatter.format(prediction.max()*100) for prediction in predictions]
  pred_labels = [breed_labels[prediction.argmax()] for prediction in predictions]
  return [[real_images[i], real_labels[i], pred_certainty[i], pred_labels[i]] for i in range(len(real_images))]

unbatch_data_with_preds(val_data, predictions)

"""## Let's create a visualization of our predictions:


"""

def prediction_vis(unbatched,n=0, ax=None):
  image= [obj[0] for obj in unbatched][n]
  true_label= [obj[1] for obj in unbatched][n]
  certainty = [obj[2] for obj in unbatched][n]
  prediction_label= [obj[3] for obj in unbatched][n]
  fig, ax = plt.subplots()
  if true_label==prediction_label:
    title_color = 'green'
  else:
    title_color = 'red'
  ax.set_title(f'{prediction_label} with certainty {certainty}% real: {true_label}', color=title_color)
  ax = plt.imshow(image)

unbatched1 = unbatch_data_with_preds(val_data, predictions)
prediction_vis(unbatched1, n=15)

# The last unbatch function's outputs aren't exactly what we need for the next visualization. Let's create another.
def simple_unbatch(batch_data, predictions):
  images=[]
  labels=[]
  raw_predictions = [prediction for prediction in predictions]
  for image, label in batch_data.unbatch():
    images.append(image)
    labels.append(label)
  return [[images[i],labels[i], raw_predictions[i]] for i in range(len(images))]

# We need to create a visualization of the top ten predictions of the model and highlight the accurate label if present.

def top_10_preds_visualization(unbatched_data, n=0, ax=None):
  prediction_confidence_values = unbatched_data[n][2]
  top_ten_pred_indexes = prediction_confidence_values.argsort()[-10:][::-1]
  true_answer = breed_labels[np.array(unbatched_data[n][1]).argmax()]
  prediction_values = [prediction_confidence_values[y] for y in top_ten_pred_indexes]
  top_ten_label_text = [breed_labels[x] for x in top_ten_pred_indexes]
  top_10_preds = plt.bar(np.arange(len(top_ten_label_text)),
                        # Creating rounded percent values as height variable
                        prediction_confidence_values[top_ten_pred_indexes],
                        color=['grey'],
                        )
  plt.xticks(np.arange(len(top_ten_label_text)),
             labels=top_ten_label_text,
             rotation='vertical')
  plt.title('Top 10 Predictions for Image')
  if np.isin(true_answer, top_ten_label_text):
    true_index = [i for i in range(len(top_ten_label_text)) if top_ten_label_text[i]==true_answer]
    top_10_preds[true_index[0]].set_color('green')
  plt.show()

unbatched = simple_unbatch(val_data, predictions)
top_10_preds_visualization(unbatched)

def visualize_failures(unbatched, param='Count', low_end=False):
  pred_indexes = [np.argmax(obj[2]) for obj in unbatched]
  pred_conf = [np.max(obj[2]) for obj in unbatched]
  true_indexes = [np.argmax(obj[1]) for obj in unbatched]
  mismatch_indexes = [i for i in range(len(pred_indexes)) if pred_indexes[i]!=true_indexes[i]]
  mismatch_breed_index = [pred_indexes[mismatch] for mismatch in mismatch_indexes]
  mismatch_prediction_confidence = [pred_conf[i] for i in mismatch_indexes]
  mismatch_labels = [breed_labels[mis] for mis in mismatch_breed_index]
  mismatch_df = pd.DataFrame(data=[mismatch_prediction_confidence,mismatch_labels], 
                             index=['confidence', 'mismatch_labels'])
  mismatch_df = mismatch_df.T
  mismatch_df['Count'] = mismatch_df.groupby('mismatch_labels')['confidence'].transform('count')
  mismatch_df['confidence']= mismatch_df['confidence'].astype(float)
  label_groups_df = mismatch_df.groupby('mismatch_labels').mean()
  label_groups_df = label_groups_df.sort_values(param, ascending=low_end)
  label_groups_df[param][:10].plot.bar(figsize=(20,10))
  plt.title(f'Failures Organized by {param}')
  plt.ylabel(f'{param}')

def visualize_success(unbatched, param='Count', low_end=False):
  pred_indexes = [np.argmax(obj[2]) for obj in unbatched]
  true_indexes = [np.argmax(obj[1]) for obj in unbatched]
  pred_conf = [np.max(obj[2]) for obj in unbatched]
  match_indexes = [i for i in range(len(pred_indexes)) if pred_indexes[i]==true_indexes[i]]
  match_breed_index = [pred_indexes[match] for match in match_indexes]
  match_prediction_confidence = [pred_conf[i] for i in match_indexes]
  match_labels = [breed_labels[match] for match in match_breed_index]
  match_df = pd.DataFrame(data=[match_prediction_confidence,match_labels], 
                             index=['confidence', 'match_labels'])
  match_df = match_df.T
  match_df['Count'] = match_df.groupby('match_labels')['confidence'].transform('count')
  match_df['confidence']= match_df['confidence'].astype(float)
  label_groups_df = match_df.groupby('match_labels').mean()
  label_groups_df = label_groups_df.sort_values(param, ascending=low_end)
  label_groups_df[param][:10].plot.bar(figsize=(20,10))
  plt.title(f'Successes Organized by {param}')
  plt.ylabel(f'{param}')

visualize_failures(unbatched, param='confidence', low_end=True)

visualize_success(unbatched)

visualize_success(unbatched, param='confidence', low_end=True)

sample_size = 10 # number of pairs returned
index_pos = 0
for i in range(sample_size):
  prediction_vis(unbatched1, n=i+index_pos)
  plt.show()
  top_10_preds_visualization(unbatched, n=i+index_pos)
  plt.show()

"""# Saving and Reloading a Model
Instead of running the whole collab notebook every time, we can save and reload the model. This also allows us to enable the sharing of this model with others.

italicized text
"""

# Let's create a save model function to make this easier in the future.
def save_model(model, suffix=''):
  model_dir = os.path.join('drive/My Drive/Dog_Vision/models', 
                           datetime.now().strftime('%Y%m%d-%H:%M:%S'))
  model_path = model_dir + suffix + '.h5' 
  print(f'Saving model at {model_path}')
  model.save(model_path)
  return model_path
def load_model(model_path):
  """A function that loads an existing folder in model path"""
  print(f'Loading model from {model_path}')
  model = tf.keras.models.load_model(model_path, 
                                     custom_objects={'KerasLayer':hub.KerasLayer})
  return model

"""We need to check our functions."""

save_model(model, '1000_image_model')

load_model = load_model('drive/My Drive/Dog_Vision/models/20210526-04:16:221000_image_model.h5')

load_model.predict(val_data)

"""We have now saved and loaded the model and checked that it is functioning well.

#Scaling Model (Full Set Implementation)
We are training the model on all the data to improve the accuracy of the model prediction.
"""

# Creating data batches with all the data.
full_data_set = create_batch(X,y)

len(full_data_set)

"""We have created 320 sets of 32."""

# Create full model callbacks
tensorboard_callback_full = tensorboard_callback()
earlystopping_callback_full = tf.keras.callbacks.EarlyStopping(monitor='accuracy',
                                                               patience=5)

full_model = create_model()

full_model.fit(x=full_data_set,
               epochs=NUM_EPOCHS,
               callbacks=[tensorboard_callback_full,
                          earlystopping_callback_full])

save_model(full_model, suffix='full_model')

full_model=load_model('drive/My Drive/Dog_Vision/models/20210526-05:54:09.h5')

"""# Creating Predictions on the Test Set

We need to make predictions based on the test set, and format the outputs according to Kaggle Requirements:

https://www.kaggle.com/c/dog-breed-identification/overview/evaluation
* convert the test images into batches
* Input the test batches into the predict function 
* format the output as a pandas DataFrame for evaluation submission. 
"""

test_images = os.listdir('drive/My Drive/Dog_Vision/test')
test_image_dir = ['drive/My Drive/Dog_Vision/test/'+ dir for dir in test_images]
test_data = create_batch(test_image_dir, test_data=True)
test_preds = full_model.predict(test_data)

np.savetxt('drive/My Drive/Dog_Vision/test_preds.csv',test_preds)

np.loadtxt('drive/My Drive/Dog_Vision/test_preds.csv')

test_pred_df = pd.DataFrame(data=test_preds, columns=breed_labels)
test_pred_df.head()

id_df = pd.DataFrame(data=test_images, columns=['id'])
id_df['id'] = id_df['id'].apply(lambda x: x.split('.')[0])
submission_df = pd.concat([id_df,test_pred_df], axis=1)
submission_df.head()

submission_df.to_csv('dog_vision_prediction_submission.csv', index=False)

len(submission_df)