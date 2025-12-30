from src.demo import demo_leads
import pandas as pd

leads = demo_leads(20, location='Tehran')
df = pd.DataFrame(leads)
fn = 'test_new_leads.csv'
df.to_csv(fn, index=False)
print(f'Wrote {len(df)} demo leads to {fn}')
