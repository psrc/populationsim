import pandas as pd
import random

def random_person(df):
    """ Return random value for length of a dataframe."""
    
    return random.randrange(0, len(df), 1)

# Update data based on summary-level info
# Get matching info
df_summary = pd.read_csv(r'C:\Users\Brice\populationsim\psrc\output\summary_block_group_id.csv')

df_person = pd.read_csv(r'C:\Users\Brice\populationsim\psrc\output\synthetic_persons.csv')
df_hh = pd.read_csv(r'C:\Users\Brice\populationsim\psrc\output\synthetic_households.csv')

# Merge the household records to person records
df = df_person.merge(df_hh[['household_id','NP']], on='household_id', how='left')

# Add a person ID record
df['person_id'] = xrange(1, len(df)+1)

# Store result as df_adjusted
df_adjusted = df.copy()

# Keep track of cloned records for now
df_adjusted['clone'] = 0

# Loop through each block group that needs to be adjusted

df_summary.index = df_summary.id
counter = 1
for bg_id in df_summary.id:
    print counter
    diff = df_summary.loc[bg_id]['num_persons_diff']
    counter += 1
    
    # Get a list of all households within this block group, sorted by size
    hh_list = df_hh[df_hh['block_group_id'] == bg_id].sort_values('NP', ascending=False)['household_id'].values
    
    if diff < 0:
        # Add cloned households to meet control
        
        # Select a person to clone from this block group       
        # Clone pool - list of potential records to clone
        # Select clones from overall group
        df_clone_pool = df.loc[df['block_group_id'] == bg_id]
        
        # List of randomly selected rows from the clone_pool
        clone_rows = [random_person(df_clone_pool) for i in xrange(abs(diff))]
        
        # Clone df
        clone_df = df_clone_pool.iloc[clone_rows]
        
        # change the HHID for each of the clone records and append to the new dataframe
        clone_df['household_id'] = hh_list[0:len(clone_df)]
        clone_df['clone'] = 1
        
        # Append records to df_adjusted
        df_adjusted = df_adjusted.append(clone_df)
            
    if diff > 0:
        # Remove persons to meet control
        
        # One person will be removed from each households for however many people are over the control total
        # Households are sorted from largest to smallest - select them in that order
        hh_to_shrink = hh_list[0:abs(diff)]

        # For each household, randomly remove a single person from the household
        # First select all people within the list of households that need to be shrunk by 1 person
        person_removal_pool = df[df['household_id'].isin(hh_to_shrink)]

        # Add a random col, group by person and take smallest value
        person_removal_pool['random_val'] = [random_person(person_removal_pool) for i in xrange(len(person_removal_pool))]

        removed_persons = person_removal_pool.groupby('household_id').min()['person_id']

        # Remove the rows for these people from df_adjusted
        df_adjusted = df_adjusted[-df_adjusted['person_id'].isin(removed_persons)]

# Recalculate household size based on the new records
df_hh_adjusted = df_adjusted.groupby('household_id').count()[['hh_id']].reset_index()
df_hh_adjusted.rename(columns={'hh_id':'NP_adjusted'}, inplace=True)
df_hh_adjusted = df_hh_adjusted.merge(df_hh, on='household_id', how='left')

# Calculate summaries by block group
df_summary_adj = df_adjusted.groupby('block_group_id').count()[['hh_id']].reset_index()
df_summary_adj.rename(columns={'hh_id':'persons_adjusted'}, inplace=True)

df_hhsize_summary = df_hh.groupby(['block_group_id','NP']).count().reset_index()
df_hhsize_summary['NP_group'] = df_hhsize_summary['NP'].copy()
df_hhsize_summary.loc[df_hhsize_summary['NP'] >= 7, 'NP_group'] = 7
df_hhsize_summary = df_hhsize_summary.pivot_table(index='block_group_id', columns='NP_group', values='household_id', aggfunc='sum')
df_hhsize_summary = df_hhsize_summary.reset_index()

# Join this to the original summary
df = df_hhsize_summary.merge(df_summary, left_on='block_group_id', right_on='id')

# also add the adjusted number of persons
# Join with the df_summary file
df = df_summary_adj.merge(df, on='block_group_id')

# Person age summary
df_adjusted['age_group'] = 'None'
df_adjusted.loc[df_adjusted['AGEP'] <= 19, 'age_group'] = 'age_19_under'
df_adjusted.loc[(df_adjusted['AGEP'] > 19) & (df_adjusted['AGEP'] <= 35), 'age_group'] = 'age_20_35'
df_adjusted.loc[(df_adjusted['AGEP'] > 35) & (df_adjusted['AGEP'] <= 60), 'age_group'] = 'age_35_60'
df_adjusted.loc[(df_adjusted['AGEP'] > 60), 'age_group'] = 'age_above_60'

df_age_summary = df_adjusted.groupby(['block_group_id','age_group']).count().reset_index()
df_age_summary = df_age_summary.pivot_table(index='block_group_id', 
                                                  columns='age_group', 
                                                  values='household_id', aggfunc='sum')
df = df_age_summary.merge(df, on='block_group_id')

df.to_csv(r'c:/users/brice/populationsim/summary_adjusted.csv',index=False)