# Image Processing Validation

This project implements a image reader which can read grocery receipts as well as vegetable images.

## Grocery Bill Reader

For Grocery bills we have used the below OCR models to compare the performance.
Both WER & CER are captured for the models but WER is given more importance.

### OCR models:

- easyOCR + embedding (Pipeline)
- Gpt-4O (Multimodal model)
As there is a restriction on image uploads with free tier, we dint check with other multimodal models.

### Dataset:

In order to monitor the performance, synthetic bills that mimic the actual grocery bills with some image noise is generated. The synthetic bills are further formatted to a nearest handwritten format and divided into three datasets with 100 bills each.

### Performance:

![image](https://github.com/user-attachments/assets/5c1bffb4-7673-4f56-9404-e841670fe943)


### Observation
easyOCR as a standalone solution had high WER as it combined words into a meaningless sequence.
But easyOCR with an embedding to pick only the vegetables & fruits, performed much better but still gpt-4O is a clear winner here. gpt-4O at times captures the non vegetable entries in the bill to a vegetable by performing some word normalization. 

## Vegetable Image Reader

For detecting the vegetablea in the image, we have used the below models to compare the performance.
Accuracy is captured for the models.

### Image reader models:

- Clip model with small patch
- Clip model with large patch
- Gpt-4O (Multimodal model)
As there is a restriction on image uploads with free tier, we dint check with other multimodal models.

### Dataset:

In order to analyze the performance, for each vegetable images are crawled from web and 50+ images were collected for each vegetable. Now vegetables are grouped and split into 100 images per set. 
However images with a big bunch of vegetables like below were not captured as there is no proper labelled data available to validate.

![image](https://github.com/user-attachments/assets/57166ab8-5841-4abb-a703-75b7b066dc35)

### Performance:

![image](https://github.com/user-attachments/assets/aec71f09-4caf-4ca4-995d-46bedc90cab0)

### Observation:
Clip model with larger patch was able to capture most of the vegetables clearly. At times it couldnt classify the more alike objects properly like Beans & Peas.
Gpt-4O clearly identified every vegetable with a much clear description for example - Red potato, Purple Cabbage.

### Execution Snaps
OCR:
![image](https://github.com/user-attachments/assets/3d519575-bab8-452c-b60e-dc76747e61ae)

