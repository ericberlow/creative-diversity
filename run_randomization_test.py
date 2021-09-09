#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  3 07:13:45 2018

@author: ericlberlow
"""

import pandas as pd
import numpy as np
from scipy import stats
#from prepare_data import buildTagHistDf
import params


pd.set_option('display.expand_frame_repr', False) # expand display of data columns if screen is wide



### summary stats by group #####
def sumstats (cluster, boolean_attrs, num_attrs=['Age']):
    # summarize frac attr true for each cluster
    # boolean _attr is list of boolean columns to get frac True. 
    # num attr is list of numeric columns to get mean
    print ("summarizing by cluster")
    d = {} # dictionary to hold results
    d['cluster_size'] = len(cluster) # cluster size
    d['n_responses_discipline'] = (cluster['Broad Discipline'] != '').sum() # responses with art, science, or biz
    d['n_responses_gender'] = cluster['Gender'].apply(lambda x: x != '').sum()
    
    for attr in boolean_attrs:
        # get fraction each of Arts, Business, Science in each cluster taking account of no responses
        responses = cluster[attr].apply(lambda x: x is not None).sum() # no response
        tagged = cluster[attr].sum() #sum all people where attr = True
        d['frac_'+attr] = tagged/responses # fraction responses with attr True
        d['n_responses_'+attr] = responses # number responses with attr True
    for attr in num_attrs:
        d['avg_'+ attr] = cluster[attr].mean() # average age
    
    df = pd.DataFrame(d, index=[0]) # need to pass index to dataframe - dummy index which will get dropped after
    return df # returns dataframe of summary stats by cluster

def compute_zscore(obs, smpl_mean, smpl_std):
    # compute zscore of observed value vs mean and std of sampled distribution
    zscore = (obs-smpl_mean)/smpl_std
    return zscore

#### compare observed frac to distruction of random samples  #####
def get_sampled_zscore (group, df, attr_list, niter=10):
    '''
    "what is the likelihood the observed frac artists, scientists, etc in a cluster could have been observed by chance?"" 
    get sampled z-score and percentile for observed frac in each group
    for each group, sample a random set of people of the same size
    for each sample, compute the fraction that are [Artists]; repeat n times and compute the mean and std
    compute zscore and percentile of the observed frac compared to mean and std of random samples of same size
    group = cluster 
    attr = name of boolean column 
    returns a group which is added to the dataframe as new columns
    '''
    print("Getting z-scores for group %s" % group)
    for attr in attr_list:
        sample_frac_list = []
        obs_frac = group['frac_'+attr].values[0] # observed fraction Artists, Scientists, etc.
        #obs_avg_age = group['avg_Age'].values[0] # observed avergage group age
        is_null = df[attr].isnull()
        n_vals = group['n_responses_' + attr].values[0]
        for i in range (0, niter):
            if n_vals > 0:
                df_trim = df[~is_null]   # remove null records for random sampling 
                smpl_df = df_trim.sample(n_vals) # get random sample from group same size as n responses in group
                frac_attr = smpl_df[attr].sum()/n_vals  # fraction art, science, etc. in the random sample
                sample_frac_list.append(frac_attr) # compile list of frac True for all samples
                if i % 100 == 0:
                    print("%.2f %s in sample %d"%(frac_attr, attr, i))
            else:
                frac_attr = None # assign no data for frac total cites 
                sample_frac_list.append(frac_attr) # compile list of frac total cites for all samples
    
        sample_fracs = pd.Series(sample_frac_list).sort_values()  #convert list of sample fracs to series
        group['pctl_'+attr] = stats.percentileofscore(sample_fracs, obs_frac, kind='weak') #get percentile of the obs value
        mean_smpl_frac = sample_fracs.mean() # compute mean frac attr across the samples
        std_smpl_frac = sample_fracs.std() # compute std frac attr for across samples
        group['z_'+attr] = np.round((compute_zscore(obs_frac, mean_smpl_frac, std_smpl_frac)),2) # compute zscore of observed group frac       
        group['diff_'+attr] = 100* np.round((obs_frac - mean_smpl_frac), 4) # difference between obseved and mean of random samples
        group['relDiff_'+attr] = (100* np.round((obs_frac/mean_smpl_frac), 4) -100) # percent difference in observed vs mean of random samples
        group['pct_' + attr] = 100* np.round(group['frac_'+attr], 4)
    return group  #returns a dataframe with new computed cols added to original ones

def add_discipline_category(df, maplist, tagcol='discipline_List'):
    # for each discipline tag, add category if any tag in the list is in the category mmappings
    cat_results = df[tagcol].apply(lambda x: [tag in maplist for tag in x if len(x) >0]) # list of True, False, [empty list if no answer]
    category = cat_results.apply(lambda x: True if sum(x)>0 else None if len(x) == 0 else False) # add True if at least one true, None if no answer
    return category # boolean for mapto category

def join_strings_noMissing (df, cols, delim="|"):
    # cols is list of string columns to concatenate - and ignore missing values
    # returns a series
    df[cols] = df[cols].replace(r'^\s*$', np.nan, regex=True) # replace empty string with nan
    return df[cols].apply(lambda x: delim.join(x.dropna()), axis=1)

#%%  ####################################
resultspath = "results/"
datapath = "data/"
infile = resultspath+"CreativeStyle_Network_minus['Emotionally Stable', 'Tortured Artist']_10links_2020_11_25.xlsx"

infile_archetypes = resultspath+"CreativeStyle_Network_Trimmed_10links_2020_11_25.xlsx"

print('read network file')
#get nodes from network file
df = pd.read_excel(infile, sheet_name='nodes', engine='openpyxl')
df = df[df['Cluster_ID']!= 'Cluster_8'].reset_index(drop=True)
df = df.fillna('')
print ('%d total nodes'%len(df)) # total sample size

'''
## generate discipline tag hist for mapping
disc_tag_df = buildTagHistDf(df, 'Discipline', mincnt=0)
disc_tag_df.to_csv("disctiplines_test.csv")
'''

#### add Art, Science, Business dummy attributes
df_discMap = pd.read_csv(params.discipline_map) # map disciplines to science, art, business
#for each disipline category, get a list of synonyms
df_byDisc = df_discMap.groupby("mapTo")['Discipline'].apply(list)

artList = df_byDisc['Arts-Design']
sciList = df_byDisc['Science-Engineering']
bizList = df_byDisc['Business-Entrepreneurship']

df['discipline_List']= df['Discipline'].str.split('|').apply(lambda x: [s.strip() for s in x if x[0] != '']) #empty lst if no response

df['Art'] = add_discipline_category(df, artList)
df['Business'] = add_discipline_category(df, bizList)
df['Science'] = add_discipline_category(df, sciList)
for discipline in ['Art', 'Business', 'Science']:
    df[discipline+"_tag"] = df[discipline].apply(lambda x: discipline if x else None)
df['Broad Discipline'] = join_strings_noMissing (df, ['Art_tag', 'Business_tag', 'Science_tag' ], delim="|")
df['Broad Discipline'] = df['Broad Discipline'].str.replace('Art', 'Arts-Design')\
                                                .str.replace('Business', 'Business-Design')\
                                                .str.replace('Science', 'Science-Engineering')
df.drop(['Art_tag', 'Business_tag', 'Science_tag'], axis=1, inplace=True)
# remove cases where all Art, Biz and Scienc are False
for disc in ['Art', 'Business', 'Science']:
    df[disc] = df.apply(lambda x: x[disc] if (x['Broad Discipline'] != '') else None, axis=1)


#### add Gender category mappings 
df_genderMap = pd.read_csv(datapath+"gender_mapping.csv") # map non-binary gender responses to one
df_byGender = df_genderMap.groupby("mapTo")['Gender'].apply(list)
nonbinary_list = df_byGender['Non-Binary/Non-Conforming']

df['Male'] = df['Gender'].apply(lambda x: x=='Male' if x != '' else None) # None if no response
df['Female'] = df['Gender'].apply(lambda x: x=='Female' if x != '' else None)
df['Non_Conforming'] = df['Gender'].apply(lambda x: x in nonbinary_list if x != '' else None)


### now summarize fracs by cluster and calculate sampled z-score.
## be sure to exclude all rows where there was no response for discipline or gender or age.

# summarize fraction of each category by  cluster
boolean_attribs = ['Male', 'Female', 'Art', 'Science', 'Business' ] #, 'Non_Conforming']
#boolean_attribs = ['Male', 'Female'] #, 'Non_Conforming']
numeric_attribs = []
#df['Age'] = pd.to_numeric(df['Age'], errors='coerce') # convert to numeric type
df_byClus = df.groupby(['Cluster_ID', 'Creative_Style']).apply(lambda x: sumstats(x, boolean_attribs, numeric_attribs)).reset_index().drop('level_2', axis=1)

# get sampled z_scores and percentiles of pbserved fraction artists, scientists, etc in each cluster

df_byClus = df_byClus.groupby(['Cluster_ID','Creative_Style']).apply(lambda x: get_sampled_zscore(x, df, boolean_attribs, niter=1000)) 

# convert to tidy dataframe for plotting

def melt_sampled_summaries (df, metric, melt_cols, melt_ids):
    # melt discipline columns for each metric one by one
    # metric =  the summary metric (e.g. z_score)
    # melt_cols = renaming of columns to melt so they become values of the new 'Discpline' columns
    # melt_ids = columns that are not melted.   
    df = df[['Cluster_ID','Creative_Style', metric+'_Art', metric+'_Science', metric+'_Business']] # subset cols with metric of interest
    df.columns = melt_cols # rename to new values in column
    df_melt = df.melt(id_vars=melt_ids, var_name='Discipline', value_name=metric)
    return df_melt
    
melt_ids = ['Cluster_ID','Creative_Style']
melt_cols = ['Cluster_ID','Creative_Style', 'Arts-Design', 'Science-Engineering', 'Business-Entrepreneur']
metrics = ['pct','diff', 'relDiff','z']

# for each metric make a list of separate dataframes melted by discipline
df_melt_list = []
for metric in metrics:
    df_melt = melt_sampled_summaries(df_byClus, metric, melt_cols, melt_ids)
    df_melt_list.append(df_melt)

# horizontally concatenate all the dataframes and remove the duplicat 'melt_id' columns
df_melt_all = pd.concat(df_melt_list, axis=1)
df_melt_all = df_melt_all.loc[:,~df_melt_all.columns.duplicated()] # remove duplicate columns from concatenation

df_melt_all.columns = ['Cluster_ID', 'Creative_Style', 'Discipline', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore']
df_melt_all.to_csv(resultspath+"Disciplines_byCluster_zScores_FullNetwork.csv")

print(df_melt_all)
'''
   # zcsores
df_byClus_Disc_z =  df_byClus[['Cluster_ID','Creative_Style', 'z_frac_Art', 'z_frac_Science', 'z_frac_Business']]
df_byClus_Disc_z.columns = ['Cluster_ID','Creative_Style', 'Arts-Design', 'Science-Engineering', 'Business-Entrepreneur'] # rename to new values in column
df_Disc_z_melt = df_byClus_Disc_z.melt(id_vars=melt_ids, var_name='Discipline', value_name="zScore")

   # percentile
df_byClus_Disc_pctl =  df_byClus[['Cluster_ID', 'Creative_Style','pctl_frac_Art', 'pctl_frac_Science', 'pctl_frac_Business']]
df_byClus_Disc_pctl.columns = ['Cluster_ID', 'Creative_Style', 'Arts-Design', 'Science-Engineering', 'Business-Entrepreneur'] # rename to new values in column
df_Disc_pctl_melt = df_byClus_Disc_pctl.melt(id_vars=melt_ids, var_name='Discipline', value_name="Percentile")

   # fracs
df_byClus_Disc_frac =  df_byClus[['Cluster_ID', 'Creative_Style','frac_Art', 'frac_Science', 'frac_Business']]
df_byClus_Disc_frac.columns = ['Cluster_ID','Creative_Style', 'Arts-Design', 'Science-Engineering', 'Business-Entrepreneur'] # rename to new values in column
df_Disc_frac_melt = df_byClus_Disc_frac.melt(id_vars=melt_ids, var_name='Discipline', value_name="Fraction")

   # combine
merge_on_cols = ['Cluster_ID','Creative_Style', 'Discipline']
df_Disc_melt = df_Disc_frac_melt.merge(df_Disc_pctl_melt, on=merge_on_cols).merge(df_Disc_z_melt, on=merge_on_cols)
df_Disc_melt[['Fraction', 'zScore']] = np.round(df_Disc_melt[['Fraction', 'zScore']], 2) 



'''

