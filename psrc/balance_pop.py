import os
import pandas as pd
import numpy as np
import random

# Output Directory for Adjusted PUMS records
# Input directory of original population sim results (synthetic_persons.csv, synthetic_households.csv, summaries, etc.)
input_dir = r'C:\Users\bnichols\Documents\populationsim\psrc\output'

# Out directory to store adjusted results (results prepended with "adjusted"; will not overwrite)
output_dir = r'C:\Users\bnichols\Documents\populationsim\psrc\output'

# Original PUMS records 
seed_hh = pd.read_csv(r'R:\e2projects_two\SyntheticPopulation_2018\populationsim_inputs\data\seed_households.csv')
seed_persons = pd.read_csv(r'R:\e2projects_two\SyntheticPopulation_2018\populationsim_inputs\data\seed_persons.csv')

def random_person(df):
    """ Return random value for length of a dataframe."""
    
    return random.randrange(0, len(df), 1)

def create_summary(df_adjusted, _df_hh, df_summary):
    """ Calculate summaries by block group. """

    # Summarize household level results
    hh_group_dict = {
        # Income
        'income_lt15_adjusted': _df_hh['HINCP'] <= 15000,
        'income_gt15-lt30_adjusted': (_df_hh['HINCP'] > 15000) & (_df_hh['HINCP'] <=30000),
        'income_gt30-lt60_adjusted': (_df_hh['HINCP'] > 30000) & (_df_hh['HINCP'] <=60000),
        'income_gt60-lt100_adjusted': (_df_hh['HINCP'] > 60000) & (_df_hh['HINCP'] <=100000),
        'income_gt100_adjusted': _df_hh['HINCP'] > 100000,

        # Vehicles
        'cars_none_adjusted': _df_hh['VEH'] == 0,
        'cars_one_adjusted': _df_hh['VEH'] == 1,
        'cars_two_or_more_adjusted': _df_hh['VEH'] >= 2,

        # HH Size
        # NP_adjusted is the recomputed field for the adjusted hh fields
        'hh_size_1_adjusted': _df_hh['NP_adjusted'] == 1,
        'hh_size_2_adjusted': _df_hh['NP_adjusted'] == 2,
        'hh_size_3_adjusted': _df_hh['NP_adjusted'] == 3,
        'hh_size_4_adjusted': _df_hh['NP_adjusted'] == 4,
        'hh_size_5_adjusted': _df_hh['NP_adjusted'] == 5,
        'hh_size_6_adjusted': _df_hh['NP_adjusted'] == 6,
        'hh_size_7_plus_adjusted': _df_hh['NP_adjusted'] >= 7,

        # Workers 
        # worker_count is the recomputed field for the adjusted hh and person fields
        'workers_0_adjusted': _df_hh['worker_count'] == 0,
        'workers_1_adjusted': _df_hh['worker_count'] == 1,
        'workers_2_adjusted': _df_hh['worker_count'] == 2,
        'workers_3_plus_adjusted': _df_hh['worker_count'] >= 3,

        # Family
        'is_family_adjusted': (_df_hh['HHT'] > 0) & (_df_hh['HHT'] <= 3),
        'not_family_adjusted': _df_hh['HHT'] > 3,
       
        }

    for col_name, _filter in hh_group_dict.items():
        print(col_name)
        # Add flag for households that meet filter criteria
        _df_hh[col_name] = 0
        _df_hh.loc[_filter, col_name] = 1

    # Aggregate household totals by block group across categories, and total persons (NP_adjusted)
    _df = _df_hh.groupby('block_group_id').sum()[list(hh_group_dict.keys())+['NP_adjusted']].reset_index()
    df = df_summary.merge(_df, on='block_group_id')

    # Summary of person records
    person_group_dict = {
        # Age
        'age_19_and_under_adjusted': df_adjusted['AGEP'] <= 19,
        'age_20_to_35_adjusted': (df_adjusted['AGEP'] > 19) & (df_adjusted['AGEP'] <= 35),
        'age_35_to_60_adjusted': (df_adjusted['AGEP'] > 35) & (df_adjusted['AGEP'] <= 60),
        'age_above_60_adjusted': (df_adjusted['AGEP'] > 60),

        # Worker
        'is_worker_adjusted': df_adjusted['is_worker'] == 1,

        # School status
        'school_yes_adjusted': df_adjusted['SCH'].isin([2,3]),
        'school_no_adjusted': (df_adjusted.SCH != 2) & (df_adjusted.SCH != 3),

        # Sex
        'male_adjusted': df_adjusted['SEX'] == 1,
        'female_adjusted': df_adjusted['SEX'] != 1,
        }

    for col_name, _filter in person_group_dict.items():
        # Add flag for households that meet filter criteria
        df_adjusted[col_name] = 0
        df_adjusted.loc[_filter, col_name] = 1

    # Aggregate household totals by block group across categories
    _df = df_adjusted.groupby('block_group_id').sum()[list(person_group_dict.keys())].reset_index()
    df = df.merge(_df, on='block_group_id')

    # Add total household count and rename columns
    _df = df_hh_adjusted.groupby('block_group_id').count()[['household_id']].reset_index()
    df = df.merge(_df, on='block_group_id')
    df.rename(columns={'NP_adjusted': 'num_persons_adjusted', 'household_id': 'num_hh_adjusted'}, inplace=True)

    return df

############################################################
# Clone/Remove Synthetic Persons to Match Control Totals
############################################################

# Use block group level summaries to calculate number of clones to add or remove
df_summary = pd.read_csv(os.path.join(input_dir,'summary_block_group_id.csv'))
df_summary['block_group_id'] = df_summary.id

# Load original synthetic person and hh records to revise
df_person = pd.read_csv(os.path.join(input_dir,'synthetic_persons.csv'))
df_hh = pd.read_csv(os.path.join(input_dir,'synthetic_households.csv'))
# Merge the household records to person records
df = df_person.merge(df_hh[['household_id','NP']], on='household_id', how='left')

# Add a local person ID record to reference when cloning
df['person_id'] = range(1, len(df)+1)

# Store result as df_adjusted
df_adjusted = df.copy()

# Initialize status of whether row has been cloned
df_adjusted['clone'] = 0

# Loop through each block group and add or removed cloned records to reach total population control total
df_summary.index = df_summary.id
counter = 1

# Store added and removed records for analysis
removed_persons_df = pd.DataFrame()
clone_df_tot = pd.DataFrame()

for bg_id in df_summary.id:
    print(counter)
    counter += 1
    
    # Use the difference between control and populationsim output as number of rows to add or remove
    diff = int(df_summary.loc[bg_id]['num_persons_diff'])
    
    # Get a subset of households within the block group that can be modified
    # Only households of a size above a given threshold will be considered
    # These households are also sorted from largest to smallest, meaning the largest will be altered first
    threshold_hhsize = 7
    hh_to_modify = df_hh[(df_hh['block_group_id'] == bg_id) & (df_hh['NP'] >= threshold_hhsize)].sort_values('NP', ascending=False)['household_id'].values
    
    # If there are no households that meet the criteria (i.e., no household large enough to modify) skip to next block group
    if len(hh_to_modify) == 0:
        print ('skipping: '+str(bg_id))
        continue


    if diff < 0:
        ########################################################################################################################
        # Initial synthesized population is lower than control, add cloned records to reach control
        ########################################################################################################################

        # Create a list of households that should have records added
        # Only households above the threshold receive new clone records
        # Households are added to this list starting with the largest households
        # Households are added to the list as many times as necessary to match control totals
        # For instance, if there are 10 households with more than 7 people in each, but a difference of 
        # 25 between the control total and initial result, each 7+ household will recieve 2 new synthetic records
        # and the 5 largest 7+ size households will receive an additional record. The new household
        # size of these households will then range from 9 to 10. 
        hh_add_clone_list = []
        while len(hh_add_clone_list) < abs(diff):
            len_to_add = abs(diff)-len(hh_add_clone_list)
            if len_to_add > len(hh_to_modify):
                hh_add_clone_list += list(hh_to_modify)
            else:
                hh_add_clone_list += list(hh_to_modify[0:len_to_add])
        
        # Generate a clone pool (list of potential records to copy from this block group)
        # Only clone non-workers from the current block group to avoid altering worker distributions
        df_clone_pool = df.loc[(df['block_group_id'] == bg_id) & (df['is_worker'] == 0)]
        if len(df_clone_pool) <= 0:    # skip this block group if no records are available to clone from
            print ('~skipping: '+str(bg_id))
            continue

        # Randomly select rows from the clone pool
        # These nonworker records are added randomly to the large households
        clone_rows = [random_person(df_clone_pool) for i in range(abs(diff))]        
        clone_df = df_clone_pool.iloc[clone_rows]
      
        # Add a clone to all households with 7+ people by renaming the household_id of clone records and adding to original data
        clone_df['household_id'] = hh_add_clone_list[0:len(clone_df)]
        clone_df['clone'] = 1
        
        # Append the cloned records to the initial synthetic population file
        df_adjusted = df_adjusted.append(clone_df)

        # Keep track of cloned records for review
        clone_df_tot = clone_df_tot.append(clone_df)

    if diff >0:
        ########################################
        # Remove persons to meet control totals
        ########################################

        # Records are removed from largest households only if their final size doesn't drop below a threshold (e.g., 7)
        # Removing people from households without this can result in changes across household size distributions
        # and result in much worse fits for even medium-size households in certain block groups.
        # Note that this limits results from always meeting control targets if no sufficiently large households are available for modification.

        # Generate a list of sufficiently large households from this block group that can be modified
        df_removal_hh = df_hh[(df_hh['block_group_id'] == bg_id) & (df_hh['NP'] > threshold_hhsize)]

        # Calculate the number of persons that can be removed from a household before hitting the minimum threshold
        df_removal_hh['repeat_times'] = df_removal_hh['NP']-threshold_hhsize

        # Skip to next block group if no sufficiently large households are available for modification
        if len(df_removal_hh) <= 0:
            continue

        # Build a list of households that will have a person removed, beginning with the largest household
        # As for adding cloned records, this process begins with the largest houeshold and iteratively removes
        # one person until either the control total is matched or no one can be removed from a household without dropping below a threshold. 
        # For instance, if 20 people need to be removed and 10 households each have 9 people, the first pass will randomly remove
        # a non-worker from each household; a second pass will then remove another person. 
        # If there were 10 households that only had 8 people each, the process would stop after the first iteration when 
        # each household had only 7 remaining members, leaving the control total unmet but household size distribution intact.  
        
        hh_to_shrink = []
        for i in range(len(df_removal_hh)):
            row = df_removal_hh.iloc[i]
            if row.repeat_times > 1:
                _list = []
                for j in range(int(row.repeat_times)):
                    _list.append(int(row.household_id))
                hh_to_shrink += _list
            else:
                hh_to_shrink.append(int(row.household_id))

        # For each household, randomly remove a single (non-worker) person from the household
        person_removal_pool = df[(df['household_id'].isin(hh_to_shrink)) & (df['is_worker'] == 0)]

        # Add a random col to sort values then remove record(s) with lowest value(s)
        person_removal_pool['random_val'] = [random_person(person_removal_pool) for i in range(len(person_removal_pool))]

        _df = person_removal_pool.merge(df_removal_hh, on='household_id', how='left')
        
        # Remove number of people from each household from 'repeat times' field
        removed_persons = []
        for hh in np.unique(hh_to_shrink):
            print(hh)
            _hh_df = _df[_df['household_id'] == hh]
            if len(_hh_df) != 0:    # Some households may not have enough nonworkers to remove; skip 
                repeat_val = _hh_df['repeat_times'].min()
                removed_persons += (list(_hh_df.sort_values('random_val').iloc[0:repeat_val]['person_id'].values))

        # Remove the rows for these people from df_adjusted
        df_adjusted = df_adjusted[-df_adjusted['person_id'].isin(removed_persons)]

# Export removed and cloned records for analysis
removed_persons_df.to_csv(os.path.join(output_dir,'removed_persons.csv'), index=False)
clone_df_tot.to_csv(os.path.join(output_dir,'cloned_persons.csv'), index=False)

# Reset the per_num value among households with new cloned records
# FIXME: find a faster way to compute this with lambda functions, or a groupby?
modified_hh_id_list = df_adjusted[df_adjusted['clone'] == 1]['household_id'].unique()
for hh in modified_hh_id_list:
    hhsize = len(df_adjusted[df_adjusted['household_id'] == hh])
    df_adjusted.loc[df_adjusted['household_id'] == hh, 'new_per_num'] = range(1,hhsize+1)
    df_adjusted['NP'] = hhsize

############################################################
# Build a new synthetic household file from the person file
############################################################
# Recalculate new household size and number of workers
# These numbers should be the same if changes are kept to a threshold within the largest household bin and only non-worked cloned/removed.

# Household size
df_hh_adjusted = df_adjusted.groupby('household_id').count()[['hh_id']].reset_index()
df_hh_adjusted.rename(columns={'hh_id':'NP_adjusted'}, inplace=True)
df_hh_adjusted = df_hh_adjusted.merge(df_hh, on='household_id', how='left')

# Number of workers
_df = df_adjusted.groupby('household_id').sum()[['is_worker']].reset_index()
_df.rename(columns={'is_worker': 'worker_count'}, inplace=True)
# drop old columns of worker count from df_hh_adjusted
df_hh_adjusted.drop('worker_count', axis=1, inplace=True)
df_hh_adjusted = df_hh_adjusted.merge(_df, on='household_id', how='left')

# Write results to file
df_adjusted.to_csv(os.path.join(output_dir,'adjusted_synthetic_persons.csv'), index=False)
df_hh_adjusted.to_csv(os.path.join(output_dir,'adjusted_synthetic_households.csv'), index=False)

# Generate summary of the adjusted synthetic household and population file
df = create_summary(df_adjusted, df_hh_adjusted, df_summary)
df.to_csv(os.path.join(output_dir,'summary_adjusted.csv'),index=False)

#############################################
# Update PUMS records with modified records
#############################################
# Cloned records will be considered new PUMS samples; 
# Households that had households added or removed will be added as new HH PUMS samples 

# Add unique person ID field based on household number and person number (SPORDER)
seed_persons['seed_person_id'] = (seed_persons['hhnum'].astype('str')+seed_persons['SPORDER'].astype('str')).astype('int')

# Get list of cloned persons to be added as new PUMS records
cloned_df = df_adjusted[df_adjusted['clone'] == 1]

# Select all persons from households that have been modified
df = df_adjusted[df_adjusted['household_id'].isin(cloned_df['household_id'].values)]
# For each group of persons in a household, assign a new hhid (prepended with 9999 to indicate the record is created)

hhid_value = seed_persons['hhnum'].max()+1
for hhid in df['household_id'].unique():
    print(hhid)
    _filter = df['household_id'] == hhid
    df.loc[_filter,'new_PUMS_hhid'] = int('9999'+str(hhid_value))

    # Update the NP field, using length of records for each household
    df.loc[_filter,'new_NP'] = int(len(df[_filter]))

    # Reset the per_num field as well
    df.loc[_filter,'new_pernum'] = range(1,int(len(df[_filter])+1))

    hhid_value += 1

# Join with PUMS records to copy the existing rows and up create new rows with the new ID
new_seed_persons = df[['hh_id','per_num','new_NP','new_PUMS_hhid','new_pernum','household_id']].merge(seed_persons, 
                                                                                         left_on=['hh_id','per_num'], 
                                                                                         right_on=['hhnum','SPORDER'], 
                                                                                         how='left')

# Update fields with new values
new_seed_persons['NP'] = new_seed_persons['new_NP'].astype('int')
new_seed_persons['hhnum'] = new_seed_persons['new_PUMS_hhid'].astype('int')
new_seed_persons['SPORDER'] = new_seed_persons['new_pernum'].astype('int')
new_seed_persons['adjusted'] = 1
seed_persons['adjusted'] = 0

## Update household file and write to disk
# Copy household info based on the old hhnum
df_hh = seed_hh[seed_hh['hhnum'].isin(new_seed_persons['hh_id'].unique())]
hh_np_df = new_seed_persons.groupby('hh_id').first()[['NP']].reset_index()
hh_np_df.drop('NP', axis=1, inplace=True)
hh_adjusted = df_hh.merge(hh_np_df, left_on='hhnum', right_on='hh_id', how='left')

# Add the new household ID (replace hhnum from new_seed_persons, using hh_id as the join column; hh_id is the original PUMS id)
hh_adjusted = hh_adjusted.drop('hhnum', axis=1)
hh_adjusted = hh_adjusted.merge(new_seed_persons[['hh_id','hhnum']], on='hh_id', how='left')

# Append to original PUMS HH records and write to file
hh_adjusted = seed_hh.append(hh_adjusted)
hh_adjusted[seed_hh.columns].to_csv(os.path.join(output_dir,'adjusted_seed_households.csv'), index=False)

# Append person records to existing PUMS records and write to file
new_seed_persons = new_seed_persons[seed_persons.columns]
new_seed_persons = seed_persons.append(new_seed_persons)
new_seed_persons.to_csv(os.path.join(output_dir,'adjusted_seed_persons.csv'), index=True)