<h1 align="center">
	🦉 OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation
</h1>

🦉 OWL is a cutting-edge framework for multi-agent collaboration that pushes the boundaries of task automation, built on top of the [Camel-AI Framework](https://github.com/camel-ai/camel). 
OWL ranks #1 among open-source frameworks on GAIA benchmark.

Our vision is to revolutionize how AI agents collaborate to solve real-world tasks. By leveraging role-playing mechanisms and dynamic agent interactions, OWL enables more natural, efficient, and robust task automation across diverse domains.

<!-- # Key Features -->

# 🔥 News

- **[2025.03.06]**: We open-source the codebase of 🦉 OWL project.

## 🛠️ Installation

### **Clone the Github repository**

```bash
git clone https://github.com/camel-ai/owl.git
cd owl
```

### **Set up Environment**

Using Conda (recommended):
```bash
conda create -n owl python=3.11
conda activate owl
```

Using venv (alternative):
```bash
python -m venv owl_env
# On Windows
owl_env\Scripts\activate
# On Unix or MacOS
source owl_env/bin/activate
```

### **Install Dependencies**

```bash
python -m pip install -r requirements.txt
```

### **Setup Environment Variables** 

In the `.env.example` file, you will find all the necessary API keys along with the websites where you can register for each service. To use these API services, follow these steps:

1. *Copy and Rename*: Duplicate the `.env.example` file and rename the copy to `.env`.
2. *Fill in Your Keys*: Open the `.env` file and insert your API keys in the corresponding fields. 

## 🚀 Quick Start
   
Run the following minimal example:

```bash
python owl/run.py
```

# 🧪 Experiments

We provided a script to reproduce the results on GAIA. 
You can check the `run_gaia_roleplaying.py` file and run the following command:

```bash
python run_gaia_roleplaying.py
```

# ⏱️ Future Plans

- [ ] Write a technical blog post detailing our exploration and insights in multi-agent collaboration in real-world tasks.
- [ ] Enhance the toolkit ecosystem with more specialized tools for domain-specific tasks.
- [ ] Develop more sophisticated agent interaction patterns and communication protocols

# Architecture



# Cite
