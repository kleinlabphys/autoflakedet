# autoflakedet
Automated Flake Detection Codebase

Full Documentation has moved [here](https://docs.google.com/document/d/1N5IEGf8QIGqM0PZJyFzPuqLQPUqQueSjiCPBYYscdsk/edit?tab=t.0)

## Launching labelme done via powershell

`python -m labelme`

### Usage
- Manually draw polygons on samples with label = 1 for monolayer, label = 2 for bilayer, etc. Or just keep at 1 for simplicity.
- Make sure to save all label me annotation jsons to a common directory prior to COCO formatting

## Formatting annotations to COCO for incorporation in finetuning

- Reference the notebook `polygons2rle-coco.ipynb` to perform the conversion seemlessly
- Dependency errors can be resolved with `pip install numpy pycocotools labelme` (in other words install the missing libraries)
