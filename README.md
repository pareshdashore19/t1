# 🧠 T1 Agent – Multi-Domain Travel Dataset Inference and Evaluation

This repository provides the code and setup instructions for running inference and evaluation of the **T1 Agent** using the **multi-domain travel T1 dataset**.  
For detailed information, refer to the paper here:  
📄 [T1: A Tool-Oriented Conversational Dataset for Multi-Turn Agentic Planning](https://arxiv.org/abs/2505.16986)

---

## ⚙️ Environment Setup

Create and activate a conda environment:

```bash
conda create -n t1 python=3.11 -y
conda activate t1
```

Then, install the dependencies in editable mode:

```bash
pip install -e .
```

After installation, ensure the environment is activated before running inference:

```bash
conda activate t1
```

---

## 📦 Dataset Setup

Download the T1 dataset which is present in the following link:

👉 [https://huggingface.co/datasets/capitalone/T1](https://huggingface.co/datasets/capitalone/T1)

The dataset could be dowloaded by running
```bash
pip install download_dataset.py
```

After downloading, the dataset folder should look like this:

```
dataset/
├── ontology/
│   ├── single-domain/
│   │   ├── t1_attraction_data.csv
│   │   ├── t1_flight_data.csv
│   │   ├── t1_hotel_data.csv
│   │   └── t1_restaurant_data.csv
│   │
│   ├── multi-domain/
│   │   ├── t1_hotel_attraction_data.csv
│   │   ├── t1_hotel_restaurant_data.csv
│   │   └── t1_restaurant_attraction_data.csv
│   │
│   └── miscellaneous/
│       ├── t1_all_airports.csv
│       └── t1_city_neighborhoods.csv
│
├── attraction/
├── flight/
├── flighthotel/
├── flighthotelattraction/
├── flighthotelrestaurant/
├── hotel/
├── hotelattraction/
├── hotelrestaurant/
└── restaurant/
```

---

## 🌍 Environment Variables Setup

Before running inference, export the required environment variables in your terminal (adjust the paths accordingly):

Make sure to **activate the environment first**:

```bash
conda activate t1
```

Then export the dataset paths and API key:

```bash
export OPENAI_API_KEY=your_openai_api_key_here

export ALL_AIRPORTS=path_to/t1_all_airports.csv
export ALL_HOTELS=path_to/t1_hotel_data.csv
export ALL_RESTAURANTS=path_to/t1_restaurant_data.csv
export ALL_ATTRACTIONS=path_to/t1_attraction_data.csv
export HOTEL_ATTRACTIONS=path_to/t1_hotel_attraction_data.csv
export HOTEL_RESTAURANTS=path_to/t1_hotel_restaurant_data.csv
export RESTAURANT_ATTRACTIONS=path_to/t1_restaurant_attraction_data.csv
export ALL_FLIGHTS=path_to/t1_flight_data.csv
export INPUT_DIR=path_to/inference_dataset
export OUTPUT_DIR=path_to/output_directory
```

---

## 🚀 Running Inference

Once the environment variables are set, run the inference script:

```bash
python inference.py
```

This inference uses the **GPT-5-mini** model for reasoning and response generation.
The inference and evaluation results will be saved in the directory you specified in `OUTPUT_DIR`.

---

## 📊 Running Evaluation

After running inference, you can evaluate the model outputs using the automated evaluation pipeline.

### Prerequisites

Make sure all environment variables from the inference setup are still set (dataset paths and API keys).

### Running the Evaluation Pipeline

The evaluation pipeline consists of three stages:

1. **Process Model Output**: Executes ground truth and generated plans to extract tool calls and cache states
2. **Generate Evaluation Metrics**: Computes tool calling metrics, parameter accuracy, and BLEU scores
3. **Compute Aggregate Metrics**: Aggregates results per domain into a final CSV summary

To run the complete evaluation pipeline:

```bash
# Make the script executable (first time only)
chmod +x evaluation/run_evaluation.sh

# Run evaluation on your model output directory
./evaluation/run_evaluation.sh /path/to/your/model/output
```

The script will create the following output structure:
```
processed_output/        # Intermediate processed outputs
eval_output/             # Evaluation files per domain
metrics/                 # Final aggregated metrics CSV
```

### Output

The final metrics will be saved in `metrics/<output>_metrics.csv` with per-domain evaluation results including:
- Code success rate
- Tool calling precision, recall, F1, and accuracy
- Tool parameter metrics
- Cache summary exact match scores
- SacreBLEU scores for information seeking

---

## 🧩 Citation

If you use this repository or dataset in your research, please cite the paper:

```bibtex
@article{dashore2025t1,
  title={T1: A Tool-Oriented Conversational Agent for Multi-Domain Travel Planning},
  author={Amartya Chakraborty, Paresh Dashore, Nadia Bathaee, Anmol Jain, Anirban Das, Shi-Xiong Zhang, Sambit Sahu, Milind Naphade, Genta Indra Winata},
  journal={arXiv preprint arXiv:2505.16986},
  year={2025}
}
```

---

## 📧 Contact

For questions or collaborations, feel free to reach out via GitHub issues or email.
