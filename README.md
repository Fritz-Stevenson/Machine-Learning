# Heart Disease Machine Learning Project.

**Problem Definition**
### A project aimed at modelling heart disease based on biometric factors in order to predict its incidence.
 * labels are binary 0(no heart disease) and 1(heart disease)
    
**Data**
Taken from Kaggle.com, this data set is curated by UCI in Cleveland
https://www.kaggle.com/ronitf/heart-disease-uci

*Evaluation:
With only 303 rows, this is a small dataset,but the spread between target labels 0(no heart disease) and 1(heart disease) is fairly even.
Also, with 14 columns there is a lot of depth to analyze our dataset with.

Our benchmark goal will be 95% accuracy  
    
**Features**
* age 
* sex
* chest pain type (4 values)(cp)
    - 0 = typical angina (chest pain related to lack of blood in heart)
    - 1 = Atypical angina (chest pain not related to heart)
    - 2 = non-anginal pain (typical esophageal spasm not related to heart)
    - 4 = Asymptomatic  
* resting blood pressure (trestbps)
    - one of the key risk factors outlined by the CDC)
    - Over 120 is cause for concern
* serum cholestoral in mg/dl (chol)
    - Another key CDC risk factor 
    - Over 200 is high and over 240 is irregular
* fasting blood sugar > 120 mg/dl (fbs)
    - high blood sugar can damage blood vessels and the nerves that control your heart
    - Over 200 is irregular
* resting electrocardiographic results (values 0,1,2) (restecg)
    - can tell where the heart's blood supply is blocked or interrupted by a build-up of fatty substances.
    - Over 100 is irregular
    - 0  = No signs of irregularity
    - 1 = ST-T wave abnormality (signals non-normal heart beat)
    - 2 = definite sign of left-ventricular hypertrophy
* maximum heart rate achieved (thalach)
    - 220 minus age is the threshold
* exercise induced angina
    - heart pain based on exercies
* oldpeak = ST depression induced by exercise relative to rest
* slope =the slope of the peak exercise ST segment
* number of major vessels (0-3) colored by flourosopy (ca)
* thal: 3 = normal; 6 = fixed defect; 7 = reversable defect
