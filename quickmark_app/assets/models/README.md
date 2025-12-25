# Placeholder for MobileFaceNet TFLite Model

This folder should contain the `mobilefacenet.tflite` model file.

The app includes a **fallback mode** that works without the model file by using face landmarks for simple identity comparison. For full face recognition, you can download a MobileFaceNet model from:

- https://github.com/nicovang/facevec/tree/main/assets
- https://www.tensorflow.org/hub

The model should be approximately 4MB and output 192-dimension embeddings.
