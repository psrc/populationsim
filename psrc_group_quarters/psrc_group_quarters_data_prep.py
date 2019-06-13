import pandas as pd

# Load PUMS records
df_pums_persons = pd.read_csv(r'R:\SyntheticPopulation_2018\group_quarters\input_files\seed_persons_gq.csv')
df_pums_households = pd.read_csv(r'R:\SyntheticPopulation_2018\group_quarters\input_files\seed_households_gq.csv')

# Load block group level group quarters data from OFM
df_ofm_bg = pd.read_csv(r'R:\SyntheticPopulation_2018\group_quarters\input_files\ofm_bg_gq_2018.csv')

# Calculate distributions for each PUMA

# Classify by income
df_pums_persons['income_group'] = "inc_missing"
df_pums_persons.loc[df_pums_persons['PINCP'] < 10000, "income_group"] = 'inc_under_10'
df_pums_persons.loc[(df_pums_persons['PINCP'] <25000) & (df_pums_persons['PINCP'] >= 10000), "income_group"] = 'inc_10_25'
df_pums_persons.loc[(df_pums_persons['PINCP'] <50000) & (df_pums_persons['PINCP'] >= 25000), "income_group"] = 'inc_25_50'
df_pums_persons.loc[df_pums_persons['PINCP'] > 50000, "income_group"] = 'inc_over_50'

# Classify by age
df_pums_persons['age_group'] = "age_missing"
df_pums_persons.loc[df_pums_persons['AGEP'] < 18, "age_group"] = 'age_0_17'
df_pums_persons.loc[(df_pums_persons['AGEP'] <25) & (df_pums_persons['AGEP'] >= 18), "age_group"] = 'age_18_24'
df_pums_persons.loc[(df_pums_persons['AGEP'] <35) & (df_pums_persons['AGEP'] >= 25), "age_group"] = 'age_25_34'
df_pums_persons.loc[(df_pums_persons['AGEP'] <45) & (df_pums_persons['AGEP'] >= 35), "age_group"] = 'age_35_45'
df_pums_persons.loc[(df_pums_persons['AGEP'] <55) & (df_pums_persons['AGEP'] >= 45), "age_group"] = 'age_45_54'
df_pums_persons.loc[(df_pums_persons['AGEP'] <65) & (df_pums_persons['AGEP'] >= 55), "age_group"] = 'age_55_64'
df_pums_persons.loc[(df_pums_persons['AGEP'] <75) & (df_pums_persons['AGEP'] >= 65), "age_group"] = 'age_65_74'
df_pums_persons.loc[df_pums_persons['AGEP'] >= 75, "age_group"] = 'age_over_75'

# Classify by worker type
df_pums_persons['worker_status'] = 'nonworker'
df_pums_persons.loc[df_pums_persons['ESR'].isin([1,2,4,5]), "worker_status"] = 'worker'

# CLassify by gender
df_pums_persons['sex_category'] = 'female'
df_pums_persons.loc[df_pums_persons['SEX'] == 1, 'sex_category'] = 'male'

# CLassify by school status
df_pums_persons['school_category'] = 'nonstudent'
df_pums_persons.loc[df_pums_persons['SCH'].isin([2,3]), 'school_category'] = 'student'

agg_cols = ['age_group','income_group','worker_status','sex_category','school_category']

# Get total pums records by PUMA to calcualte shares across agg categories
df = df_pums_persons.groupby('PUMA').count()
df.rename(columns={'REGION': 'puma_tot_gq_pop'}, inplace=True)

for col in agg_cols:
    _df = df_pums_persons.groupby([col,'PUMA']).count()[['REGION']].reset_index()
    _df.rename(columns={'REGION':col+'_puma_tot'}, inplace=True)
    _df = _df.pivot_table(index='PUMA',columns=col, values=col+'_puma_tot', aggfunc='sum').fillna(0).reset_index()

    df = df.merge(_df, on='PUMA')

df = df.merge(df_ofm_bg[['PUMA','GQ2018','GEOID10','block_group_id']], on='PUMA')

df['GQ2018_hh'] = df['GQ2018'].copy().astype('int')
df['GQ2018_pop'] = df['GQ2018'].copy().astype('int')

# Add the state ID to the block_group_id field
df['block_group_id'] = '53' + df['block_group_id'].astype('str')

df.to_csv(r'R:\SyntheticPopulation_2018\group_quarters\input_files\bg_gq_control_targets.csv', index=False)