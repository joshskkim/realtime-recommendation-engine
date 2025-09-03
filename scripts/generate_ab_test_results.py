# File: scripts/generate_ab_test_results.py
"""Generate A/B test results visualization"""

import matplotlib.pyplot as plt
import numpy as np

# Sample A/B test data
groups = ['Control', 'Variant A', 'Variant B']
conversion_rates = [5.2, 7.1, 6.8]
confidence_intervals = [(4.8, 5.6), (6.5, 7.7), (6.2, 7.4)]
sample_sizes = [5000, 5000, 5000]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('A/B Test Results - Recommendation Algorithm Comparison', fontsize=14, fontweight='bold')

# Conversion rates with confidence intervals
x_pos = np.arange(len(groups))
errors = [(ci[1] - ci[0])/2 for ci in confidence_intervals]
colors = ['#3498db', '#2ecc71', '#e74c3c']

bars = ax1.bar(x_pos, conversion_rates, yerr=errors, capsize=10, color=colors, alpha=0.8)
ax1.set_xlabel('Variant')
ax1.set_ylabel('Conversion Rate (%)')
ax1.set_title('Conversion Rates with 95% CI')
ax1.set_xticks(x_pos)
ax1.set_xticklabels(groups)

# Add value labels on bars
for bar, rate in zip(bars, conversion_rates):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height,
             f'{rate}%', ha='center', va='bottom', fontweight='bold')

# Statistical significance
ax1.axhline(y=conversion_rates[0], color='gray', linestyle='--', alpha=0.5)
ax1.text(0.5, conversion_rates[0] + 0.1, 'Baseline', fontsize=10, alpha=0.7)

# Cumulative conversions over time
days = np.arange(1, 31)
control_cumulative = np.cumsum(np.random.Generator(170, 0.052, 30))
variant_a_cumulative = np.cumsum(np.random.Generator(170, 0.071, 30))
variant_b_cumulative = np.cumsum(np.random.Generator(170, 0.068, 30))

ax2.plot(days, control_cumulative, label='Control', color=colors[0], linewidth=2)
ax2.plot(days, variant_a_cumulative, label='Variant A', color=colors[1], linewidth=2)
ax2.plot(days, variant_b_cumulative, label='Variant B', color=colors[2], linewidth=2)
ax2.set_xlabel('Days')
ax2.set_ylabel('Cumulative Conversions')
ax2.set_title('Cumulative Conversions Over Time')
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('docs/images/ab-testing-results.png', dpi=150, bbox_inches='tight')
print("A/B testing results saved to docs/images/ab-testing-results.png")