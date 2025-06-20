from sklearn.metrics import accuracy_score
from gpt_img import predict_gpt4o
# from groq import predict_llava
from clip_img_model import predict_clip
import os
classes = ['Potato', 'Cabbage', 'Beans', 'Tomato', 'Carrot']
valid_extensions = (".jpg", ".jpeg", ".png", ".bmp", ".webp")
print(classes)
y_true, y_pred_clip, y_pred_gpt4o, y_pred_llava = [], [], [], []

for class_name in classes:
    folder = f"veg_sample/{class_name}"
    print('Class: ',class_name)
    for filename in os.listdir(folder):
        if filename.lower().endswith(valid_extensions):
            path = os.path.join(folder, filename)
            y_true.append(class_name)
            clip_prediction = predict_clip(path)
            gpt_prediction = predict_gpt4o(path)
            y_pred_clip.append(clip_prediction)
            y_pred_gpt4o.append(gpt_prediction)
            # y_pred_llava.append(predict_llava(path))
print('Clip ',y_pred_clip)
print('GPT',y_pred_gpt4o)

# Accuracy
print("CLIP Accuracy:", accuracy_score(y_true, y_pred_clip))
print("GPT-4.1 Accuracy:", accuracy_score(y_true, y_pred_gpt4o))
# print("LLaVA (Groq) Accuracy:", accuracy_score(y_true, y_pred_llava))
