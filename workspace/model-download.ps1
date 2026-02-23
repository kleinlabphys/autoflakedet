# Download the M2F Graphene Model
ls
mkdir -p ./models/segmentation_models/M2F
wget "https://zenodo.org/records/15765516/files/SEG_M2F_GrapheneH.zip?download=1" -O ./models/segmentation_models/M2F/GrapheneH.zip
Expand-Archive ./models/segmentation_models/M2F/GrapheneH.zip -d ./models/segmentation_models/M2F/GrapheneH

# Download the AMM Graphene Model
mkdir -p ./models/classification_models/AMM
wget "https://zenodo.org/records/15765516/files/CLS_AMM_GrapheneH.zip?download=1" -O ./models/classification_models/AMM/GrapheneH.zip
Expand-Archive ./models/classification_models/AMM/GrapheneH.zip -d ./models/classification_models/AMM/GrapheneH

# Download the GMM Graphene Model
mkdir -p ./models/classification_models/GMM
wget "https://zenodo.org/records/15765516/files/CLS_GMM_GrapheneH.zip?download=1" -O ./models/classification_models/GMM/GrapheneH.zip
Expand-Archive ./models/classification_models/GMM/GrapheneH.zip -d ./models/classification_models/GMM/GrapheneH