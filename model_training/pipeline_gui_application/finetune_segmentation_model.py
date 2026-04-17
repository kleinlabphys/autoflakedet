import argparse

def parse_seg_args(
    config_file="",
    resume=False,
    num_gpus=1,
    num_machines=1,
    machine_rank=0,
    pretraining_augmentations=False,
    train_image_root=None,
    train_annotation_path=None,
    dist_url="auto",
    opts=None,
) -> argparse.Namespacee:

    return argparse.Namespace(
        config_file=config_file,
        resume=resume,
        num_gpus=num_gpus,
        num_machines=num_machines,
        machine_rank=machine_rank,
        pretraining_augmentations=pretraining_augmentations,
        train_image_root=train_image_root,
        train_annotation_path=train_annotation_path,
        dist_url=dist_url,
        opts=opts or [],
    )


import warnings

from detectron2.data.datasets import register_coco_instances
from detectron2.engine import launch

from maskterial.modeling.segmentation_models.M2F.maskformer_model import (
    MaskFormer,  # noqa: F401
)
from maskterial.modeling.segmentation_models.M2F.modeling import *  # noqa: F401, F403
from maskterial.utils.dataset_functions import setup_config
from maskterial.utils.model_trainer import MaskTerial_Trainer

warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", FutureWarning)


def main(args: dict):
    cfg = setup_config(args)
    trainer = MaskTerial_Trainer(
        cfg,
        pretraining_augmentations=args.pretraining_augmentations,
    )
    trainer.resume_or_load(resume=args.resume)
    return trainer.train()


if __name__ == "__main__":
    args = parse_seg_args()

    register_coco_instances(
        "Maskterial_Dataset",
        {},
        args.train_annotation_path,
        args.train_image_root,
    )

    print("Command Line Args:", args)
    launch(
        main,
        num_gpus_per_machine=args.num_gpus,
        num_machines=args.num_machines,
        machine_rank=args.machine_rank,
        dist_url=args.dist_url,
        args=(args,),
    )



# command that worked for training
# python.exe ..\MaskTerial\train_segmentation_model.py  --config .\workspace\maskterial_repo\configs\M2F\base_config.yaml --train-image-root model_training\library_to_train_on --train-annotation-path model_training\intermittent_storage\coco.json

## TODO: Need to figure out how to overwrite yaml entries 
# 1. WEIGHTS
# 2. NUM_CLASSES