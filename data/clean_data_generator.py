import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Set seed for reproducibility
seed = 42
np.random.seed(seed=seed)
random.seed(a=seed)

# Configuration
n_samples = 100_000  # Adjust this number to generate more rows
noise = False

# Possible values
if noise:
    components = ['Engine', 'Eng', 'MOTOR', 'Motor Diese', "Mot. Diesel",
                            'PTO',
                            'Transmission', 'Transmição', 'Transmissão',
                            'Hydraulic System', 'Sistema Hidráulico', 'Sis. Hidráulico', 'Sis. Hid.'] 

    fleet_models = ['777G','77G', 'CAT 777G', 'CATERPILLAR 777', '777',
                            'PC2000', 'Komatsu - PC2000', 'Kom-2000', '2000',
                            'L1350', 'Letourneu - L1350', 'Let-L1350', 'L135',
                            '785C', 'CAT 785c', 'CATERPILLAR 785', '785']
else:    
    components = ['Engine', 'PTO', 'Transmission', 'Hydraulic System']

    fleet_models = ['777G', '785C', 'PC2000', 'L1350']

overall_interp_labels = ['Normal', 'Monitor', 'Critical']
locations = ['PICO', 'VIGA', 'CPX', 'CKS']

# Equipment number to model mapping (1-to-1)
equipment_numbers = [f"EQT-{random.randint(100, 999)}" for _ in range(30)]
equipment_mapping = {eq: random.choice(fleet_models) for eq in equipment_numbers}
location_mapping = {eq: random.choice(locations) for eq in equipment_numbers}

# ISO code generator
def generate_iso_code():
    return f"{random.randint(10, 25)}/{random.randint(15, 35)}/{random.randint(15, 30)}"

# Generate data
data = []
for i in range(n_samples):
    eq_number = random.choice(list(location_mapping.keys()))
    row = {
        'id': f"{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
        'equipment_type': equipment_mapping[eq_number],
        'location': location_mapping[eq_number],
        'equipment_number': eq_number,
        'component': random.choice(components),
        'sample_date': (datetime.today() - timedelta(days=random.randint(0, 2000))).strftime('%Y-%m-%d'),
        'fluid_changed': random.choice([True, False]),
        'filter_changed': random.choice([True, False]),
        'al': round(np.random.uniform(0, 100), 2),
        'cr': round(np.random.uniform(0, 100), 2),
        'cu': round(np.random.uniform(0, 100), 2),
        'fe': round(np.random.uniform(0, 500), 2),
        'ni': round(np.random.uniform(0, 100), 2),
        'pb': round(np.random.uniform(0, 50), 2),
        'si': round(np.random.uniform(0, 150), 2),
        'sn': round(np.random.uniform(0, 100), 2),
        'iso': generate_iso_code(),
        'viscosity_at_100c': round(np.random.uniform(5, 30), 2),
        'overall_interp': random.choice(overall_interp_labels),
    }
    data.append(row)

# Create DataFrame
df = pd.DataFrame(data)

# Save to CSV if needed
df.to_csv("data/data.csv", index=False)