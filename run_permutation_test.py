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

def add_broad_discipline_tags(x, mappingDict):
    '''
    x is a pipe-separated string of specific discipline tags
    mappingDict is dictionary mapping specific tags to broad tags
    If the tag is not in the dictionary, don't keep it
    Clean dupes
    Returns a new pipe-separated string of tags
    '''
    newTagList = []
    tagList = x.split("|") if x else []
    for tag in tagList:
        if tag in mappingDict:
            newTagList.append(mappingDict[tag])
    newTagList = list(set(newTagList)) # get unique tags, 
    broadTags = "|".join(newTagList) # join list back into string of tags
    return broadTags

def sumstats (cluster, boolean_attrs, num_attrs=[]):
    ### summary stats by group #####
    # summarize frac attr true for each cluster
    # boolean _attr is list of boolean columns to get frac True. 
    # num attr is list of numeric columns to get mean
    d = {} # dictionary to hold results
    d['cluster_size'] = len(cluster) # cluster size
    clus_size = len(cluster)
    
    for attr in boolean_attrs:
        # get fraction each of Arts, Business, Science in each cluster (already filtered out no responses)
        tagged = cluster[attr].sum() #sum all people where attr = True
        d['frac_'+attr] = tagged/clus_size # fraction responses with attr True
    for attr in num_attrs:
        d['avg_'+ attr] = cluster[attr].mean() # average age
    
    df = pd.DataFrame(d, index=[0]) # need to pass index to dataframe - dummy index which will get dropped after
    return df # returns dataframe of summary stats by cluster

def permute_label(df, col):
    shuffled = np.random.permutation(df[col].tolist()).tolist()
    return shuffled # shuffled list of same length can be read as df column


def compute_zscore(obs, smpl_mean, smpl_std):
    # compute zscore of observed value vs mean and std of sampled distribution
    zscore = (obs-smpl_mean)/smpl_std
    return zscore

def summarize_permuted_data(df, permuted_cols):
    # get mean and std of permuted runs
    agg_data = {col: ['mean', 'std'] for col in permuted_cols} # mean fracs across runs
    groupVars = ['Cluster_ID'] # group by cluster
    df_permute_sum = df.groupby(groupVars).agg(agg_data) # summarize across permutations
    df_permute_sum.columns = ["_".join(x) for x in df_permute_sum.columns.ravel()] # add mean and std suffix to col names
    df_permute_sum.reset_index()  # reset cluster id and creative style
    return df_permute_sum

#### compare observed frac to distruction of random samples  #####
def get_permuted_summaries_byCluster (df, attr_list, niter=10):
    '''
    "what is the likelihood the observed frac artists, scientists, etc in a cluster could have been observed by chance?"" 
    get permuted z-score and percentile for observed frac in each group
    for each attribute, permute the labels wrt clusters
    for each permutation - compute the fraction in each cluster. 
    repeat n times and compute the mean and std
    compute zscore and percentile of the observed frac compared to mean and std of permuted samples
    
    group = cluster 
    attr = name of boolean column 
    returns a group which is added to the dataframe as new columns
    '''
    print("permuting discipline labels")
    permuted_df_list = [] # list of dataframes one for each permutation
    
    for i in range(0,niter):
        if i %100 == 0: # print row number every 100 rows to show progress
            print("summarizing permuted disciplines by cluster for sample %d"%i)
        permuted_attribs = [] # list to hold attribute names
        for attr in attr_list:
            df[attr+"_rand"] = permute_label(df, attr) # permute labels
            permuted_attribs.append(attr+"_rand") # list of permuted attributes
        # summarize fraction Art, Sci, Biz by cluster
        df_permute_byClus = df.groupby(['Cluster_ID', 'Creative_Style']).apply(lambda x: sumstats(x, permuted_attribs)).reset_index().drop('level_2', axis=1)
        df_permute_byClus['sample'] = i
        permuted_df_list.append(df_permute_byClus) # add permuted summary by cluster to list
    # concatenate list of dataframes into one
    df_allRuns = pd.concat(permuted_df_list)
    permuted_cols = ['frac_'+attr+'_rand' for attr in discipline_attribs]

    # get mean, std permuted data
    df_sumRuns = summarize_permuted_data(df_allRuns, permuted_cols)

    return df_allRuns, df_sumRuns
        

def compare_obs_v_permuted(df_obs, df_rand, category_attribs): 
    # merge permuted and obs datasets - compute metrics to compare obs vs random
    df_obs_v_rand = df_obs.merge(df_rand, on=['Cluster_ID'])
    for col in category_attribs:
        df_obs_v_rand['z_'+col] = compute_zscore(df_obs_v_rand["frac_"+col], df_obs_v_rand["frac_"+col+"_rand_mean"], df_obs_v_rand["frac_"+col+"_rand_std"])
        df_obs_v_rand['diff_'+col] = 100 * np.round(df_obs_v_rand["frac_"+col] - df_obs_v_rand["frac_"+col+"_rand_mean"], 4) # absolute difference
        df_obs_v_rand['pctDiff_'+col] = (100 * (np.round((df_obs_v_rand["frac_"+col]/df_obs_v_rand["frac_"+col+"_rand_mean"]), 4))-100) # percent difference
        df_obs_v_rand['pct_'+col] = 100 * np.round(df_obs_v_rand["frac_"+col], 4) # percent difference
    return df_obs_v_rand             

########################################################################
if __name__ == '__main__':
    

    infile =  params.creative_styles_network  # full creative style network (all respondents)
    
    print('read network file')
    #get nodes from network file
    df = pd.read_excel(infile, sheet_name='nodes', engine='openpyxl')
    df = df[df['Cluster_ID']!= 'Cluster_8'].reset_index(drop=True)
    df = df.fillna('')
    print ('%d total nodes'%len(df)) # total sample size
   
    #### add broad discipline tags (Art, Science, Business)
    df_discMap = pd.read_csv(params.discipline_map) # map disciplines to science, art, business
    discDict = dict(zip(df_discMap['Discipline'],df_discMap['mapTo'])) #dictionary mapping discipline to art, sci, biz
    df['Discipline'].fillna('', inplace=True)
    df['Broad_Discipline'] = df['Discipline'].apply(lambda x: add_broad_discipline_tags(x, discDict))

    #### add Art, Science, Business dummy attributes
    discipline_attribs = ['Arts-Design', 'Science-Engineering', 'Business-Entrepreneurship' ] 
    for disc in discipline_attribs:
        df[disc] = df['Broad_Discipline'].apply(lambda x: disc in x)
        
    ### Delete records where no broad discipline response
    df_disc = df[['id', 'Cluster_ID','Creative_Style', 'Broad_Discipline'] + discipline_attribs]
    df_disc =  df[~(df_disc['Broad_Discipline']=='')]
    df_disc.reset_index(drop=True, inplace=True)
    
    #### Summarize frac Art, Business, Science by Cluster
    print ("summarizing by cluster")
    df_byClus = df_disc.groupby(['Cluster_ID', 'Creative_Style']).apply(lambda x: sumstats(x, discipline_attribs)).reset_index().drop('level_2', axis=1)
    
    #### Permute discipline labels, compute frac by cluster for each run, summarize across runs
    df_permute_all, df_permute_sum = get_permuted_summaries_byCluster (df_disc, discipline_attribs, niter=1000)
    
    #### Compare observed vs permuted fracs
    df_obs_v_rand = compare_obs_v_permuted(df_byClus, df_permute_sum, discipline_attribs)
    #df_obs_v_rand.to_csv('test.csv')
        

    ######## Format for figures ########
    ######## melt disciplines for each metric, then combine horizontally ############
    def melt_sampled_summaries (df, metric, melt_cols, melt_ids):
        # melt discipline columns for each metric one by one
        # metric =  the summary metric (e.g. z_score) which is the prefix of the attribute
        # melt_cols = renaming of columns to melt so they become values of the new 'Discipline' columns
        # melt_ids = columns that are not melted.   
        df = df[['Cluster_ID','Creative_Style','cluster_size', 
                 metric+'_Arts-Design', metric+'_Science-Engineering', metric+'_Business-Entrepreneurship']] # subset cols with metric of interest
        df.columns = melt_cols # rename to new values in column
        df_melt = df.melt(id_vars=melt_ids, var_name='Discipline', value_name=metric)
        return df_melt

    # convert to tidy dataframe for plotting          
    melt_ids = ['Cluster_ID','Creative_Style', 'cluster_size']
    melt_cols = ['Cluster_ID','Creative_Style', 'cluster_size', 'Arts-Design', 'Science-Engineering', 'Business-Entrepreneur']
    metrics = ['pct','diff', 'pctDiff','z']
    
    df_melt_list = [] # to hold list of melted dataframes, one for each metric
    for metric in metrics: # melt separate dataframe for each metric
        df_melt = melt_sampled_summaries(df_obs_v_rand, metric, melt_cols, melt_ids)
        df_melt_list.append(df_melt)
    
    # horizontally concatenate all the dataframes and remove the duplicat 'melt_id' columns
    df_melt_all = pd.concat(df_melt_list, axis=1)
    df_melt_all = df_melt_all.loc[:,~df_melt_all.columns.duplicated()] # remove duplicate columns from concatenation
    
    df_melt_all.columns = ['Cluster_ID', 'Creative_Style', 'cluster_size', 'Discipline', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore']
   # df_melt_all.to_csv(params.disciplines_by_cluster_permuted, index=False)
    
    print(df_melt_all)

