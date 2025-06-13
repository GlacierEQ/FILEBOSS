# Hierarchical Sorting Legal Documents using NLP
 
### by Christian Grech


## Introduction

One of the challenges Legal Tech companies encounter involves reconstructing hierarchical structures within regulatory documents after parsing. Establishing clear parent-child relationships between paragraphs is crucial for organizing data in a manner that benefits our customers and enables various machine learning applications.

For this task, I create a system capable of organizing a provided list of paragraphs into a hierarchy by defining parent-child relationships between them. I have included an example dataset (*data.json*) containing paragraphs from a generic legal document, arranged in the correct hierarchy based on reading order. Feel free to utilize this dataset as input for your machine learning model or any alternative approach you prefer.

It's important to note that the hierarchy may consist of multiple levels, meaning a paragraph could serve as both a parent and a child simultaneously. Ultimately, I have used the best performing classifier to organize the paragraphs in *test.json* into a hierarchy and generate an HTML file with visible indentations.

## Dataset description

- *data.json* consists of 785 paragraphs in reading order. id is a unique identifier of the paragraph. *parent_id* holds the reference to the parent paragraph. if *parent_id* is null the paragraph has no parent. *html* is the html representation of the paragraph.

- *test.json* consists of 48 paragraphs in reading order from a legal document similar to the one the paragraphs in data.json were taken from. id is a unique identifier of the paragraph. *html* is the html representation of the paragraph. *parent_id* has been purposefully hidden and should be predicted by the best performing model.

## Solution

1. Data imported from the two json files.
2. Feature extraction: html tags are extracted to try to identify html tags for paragraphs and headers.
3. Data is vectorized and split into training and validation sets.
3. Several classifiers are trained with and their performance is evaluated with the validation dataset.
5. In the end the XGBoost Classifier is used on the test dataset to create the *test_data.json* file with indents.


## Evaluation

The XGBoost model performs with an Accuracy of 0.96  and a Balanced Accuracy of 0.85.

## Improvements

- Finetuning feature extraction and model parameters.
- Predicting relative relationship rather than the numerical level.
