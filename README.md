# Stroke-Modelling
Datasets from kaggle were used for this project: https://www.kaggle.com/fedesoriano/stroke-prediction-dataset
This notebook aims to model the occurence of strokes based on various historical and biometric factors.

    We will first break down and explore the data
    Then we will treat and prepare the data for visualization and modelling
    We will visualize the data to set up for modelling
    And finally we will test and tune our model


Through repeated modelling, Accuracy for the model increased to 95% despite many categorical fields and only 5% prevalence of stroke victims within the dataset. 
This model featured very little correlation between stroke incidence and non-categorical fields of glucose levels and bmi. 

Initial tests of the model found that dropping the bmi column to preserve the size increased accuracy in modelling. In mid term tests, ball tree was marginally more accurate than kd tree and brute force algorithms and was faster than brute force algorithm which came in second. 

![Alt text](https://github.com/Fritz-Stevenson/Stroke-Modelling/blob/main/stroke-analysis-figure.png?raw=true)
