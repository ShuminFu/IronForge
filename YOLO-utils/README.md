# XML to YOLO Conversion Tool
`xm_2YOLO.py`
This  script converts image annotations from XML format to YOLO format. It's designed for the Road Damage Detection (RDD) dataset but can be adapted for other datasets by modifying the class mappings.

## Features

- Recursively searches for all images and corresponding XML files in a specified directory
- Randomly splits the dataset into training (70%) and validation (30%) sets
- Converts bounding box coordinates from XML format to YOLO format
- Generates a directory structure compatible with YOLO training requirements
- Creates a `data.yaml` configuration file
- Displays conversion progress using a progress bar

## Usage

1. Place the script in the root directory containing your dataset.
2. Modify the `class_mapping` and `class_names` in the script if necessary.
3. Run the script
4. The converted YOLO format dataset will be saved in the `./yolo_dataset` directory.
