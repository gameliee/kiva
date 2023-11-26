"""script to run `54_lender_country_biLouvian_active.ipynb` with multiple time setup"""
import os
import numpy as np
import papermill as pm

# %%
SCRIPT_PATH = "./54_lender_country_biLouvian_active.ipynb"
DEVICES = "1,2"
ORDER = 1

# %%
begin_year = np.arange(2019, 2024)
end_year = begin_year + 1

for b, e in zip(begin_year, end_year):
    FROM = f"{b}-01-01"
    TO = f"{e}-01-01"
    output_folder = "checkpoints"
    script_filename = os.path.splitext(os.path.basename(SCRIPT_PATH))[0]
    output_filename = f"{script_filename}_from{FROM}_to{TO}_order{ORDER}.ipynb"
    output = os.path.join(output_folder, output_filename)
    print("\n\n\n\n\n---------------------------------------------------------------------")
    print("Running running", output)
    pm.execute_notebook(
        SCRIPT_PATH,
        output,
        parameters={"DEVICES": DEVICES, "FROM": FROM, "TO": TO, "ORDER": 1},
    )

print("DONE")
