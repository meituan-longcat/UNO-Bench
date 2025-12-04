import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from adjustText import adjust_text
from scipy.optimize import curve_fit

data = {
    'ModelName': ['Qwen2.5-Omni-3B', 'MiniCPM-O-2.6', 'Ming-lite-Omni-1.5', 'Baichuan-Omni-1.5', 'Qwen2.5-Omni-7B', 'Qwen3-Omni-30B-A3B-Instruct', 'Gemini-2.0-Flash', 'Gemini-2.5-Flash', 'Gemini-2.5-Pro'],
    'Audio': [0.544, 0.565, 0.583, 0.541, 0.602, 0.794, 0.707, 0.795, 0.884],
    'Visual': [0.4267, 0.4227, 0.4628, 0.4466, 0.5068, 0.6329, 0.6276, 0.6954, 0.7867],
    'Omni': [0.278, 0.286, 0.289, 0.297, 0.326, 0.421, 0.449, 0.543, 0.709]
}

new_model_data = {
    'ModelName': 'LongCat-Flash-Omni', 
    'Audio': 0.802, 
    'Visual': 0.6706, 
    'Omni': 0.4990
}

df = pd.DataFrame(data)
df['Audio_x_Visual'] = df['Audio'] * df['Visual']
x_data_fit = df['Audio_x_Visual'].values
y_data_fit = df['Omni'].values

def compositional_law(x, C, alpha, b):
    return C * (x**alpha) + b

popt, pcov = curve_fit(compositional_law, x_data_fit, y_data_fit)
C_opt, alpha_opt, b_opt = popt
y_predicted = compositional_law(x_data_fit, C_opt, alpha_opt, b_opt)
ss_res = np.sum((y_data_fit - y_predicted)**2)
ss_tot = np.sum((y_data_fit - np.mean(y_data_fit))**2)
r_squared = 1 - (ss_res / ss_tot)


new_model_df = pd.DataFrame([new_model_data])
df_plot = pd.concat([df, new_model_df], ignore_index=True)
df_plot['Audio_x_Visual'] = df_plot['Audio'] * df_plot['Visual']
x_plot_all = df_plot['Audio_x_Visual'].values
y_plot_all = df_plot['Omni'].values

plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(10, 7))

x_smooth = np.linspace(x_plot_all.min(), x_plot_all.max(), 200)
y_smooth = compositional_law(x_smooth, C_opt, alpha_opt, b_opt)

ax.plot(x_smooth, y_smooth, color='mediumseagreen', linestyle='--', linewidth=2, label='Fitted Compositional Law')


ax.scatter(x_data_fit, y_data_fit, color='darkgreen', s=60, label='Observed Models', zorder=5)

new_model_point = df_plot[df_plot['ModelName'] == 'LongCat-Flash-Omni']

ax.scatter(new_model_point['Audio_x_Visual'], new_model_point['Omni'], 
           color='darkgreen', marker='*', s=200, label='LongCat-Flash-Omni', zorder=6)


models_to_hide = ['Qwen2.5-Omni-3B', 'MiniCPM-O-2.6', 'Ming-lite-Omni-1.5', 'Baichuan-Omni-1.5', 'Qwen2.5-Omni-7B']
models_to_hide = []
texts = []
for i, model_name in enumerate(df_plot['ModelName']):
    if model_name not in models_to_hide:
        texts.append(ax.text(x_plot_all[i], y_plot_all[i], model_name, fontsize=14))

adjust_text(texts, 
            arrowprops=dict(arrowstyle='-', color='gray', lw=0.5),
            ax=ax)


ax.set_xlabel('Uni-modal Scores (Audio x Visual)', fontsize=18, labelpad=15)
ax.set_ylabel('Omni-modal Score', fontsize=18, labelpad=15)

formula_text = (f'Fitted Law: $Omni = {C_opt:.2f} \\times (A \\times V)^{{{alpha_opt:.2f}}} + {b_opt:.2f}$'
                f'\n$R^2 = {r_squared:.4f}$')
ax.text(0.05, 0.95, formula_text, transform=ax.transAxes, fontsize=16,
        verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc='aliceblue', alpha=0.8))

ax.tick_params(axis='both', which='major', labelsize=16)

ax.legend(
    loc='lower right',
    fontsize=16,
    frameon=True,
    facecolor='white',
    edgecolor='gray',
    framealpha=1.0,
    fancybox=True
)

if os.path.exists('./eval_results') == False:
    os.makedirs('./eval_results')

plt.tight_layout()

plt.savefig('./eval_results/compositional_law_plot.pdf', dpi=300, bbox_inches='tight')
plt.savefig('./eval_results/compositional_law_plot.png', dpi=300, bbox_inches='tight')

plt.show()
