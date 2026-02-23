# autoflakedet
Automated Flake Detection Module

See [workspace](workspace) for example scripts and procedures

## Launching labelme done via powershell

`python -m labelme`

### Usage
- Manually draw polygons on samples with label = 1 for monolayer, label = 2 for bilayer, etc. Or just keep at 1 for simplicity.
- Make sure to save all label me annotation jsons to a common directory prior to COCO formatting

## Formatting annotations to COCO for incorporation in finetuning

- Reference the notebook `polygons2rle-coco.ipynb` to perform the conversion seemlessly
- Dependency errors can be resolved with `pip install numpy pycocotools labelme` (in other words install the missing libraries)