

import sys
sys.path.append("../../../GitHub/Tag2Network/tag2network")

import pandas as pd
import pathlib as pl
from collections import Counter, OrderedDict
import numpy as np
from Network.BuildNetwork import buildTagNetwork
from build_decorate_network import write_network_file, tsne_layout, plot_network
#from ast import literal_eval 




def build_habit_network(df, tagAttr,  write=True, nwname=None, plotname="Habit_Network.pdf", 
                                idf=False, linksPer=6, blacklist=[]):   
    '''
    build network of creative habits linked by similar people,  merge small clusters
    merge small clusters and shorten cluster labels
    plot network and write network file
    all files are named with the parameters for the run for comparison
    'tagAttr' = name of column with tags as list of tags
    'nwname' = name of newtork output file
    'plotname' = name of network viz plot
    NOTE : tagAttr for build netowork must be a list of tags, not pipe-delimited string
    '''
    print("Building Creative Habit Network")
    # remove blacklisted people tags if any
    df[tagAttr] = df[tagAttr].apply(lambda x: [tag for tag in x if tag not in blacklist])
    # build network without plotting or writing files
    ndf, edf = buildTagNetwork(df, tagAttr=tagAttr, 
                    plotfile=None, doLayout=False, outname=None,
                    idf=idf, linksPer=linksPer, minTags=3)
    
    # create cluster names from most central habits (rather than people id's)  
    ndf['Cluster_size'] = ndf.groupby(['Cluster'])['Cluster'].transform('count') # add counts
    ndf['Cluster_frac'] = ndf['Cluster_size']/len(ndf)
    # merge small clusters
    ndf['Cluster_Trimmed'] = ndf.apply(lambda x: x.Cluster  if x.Cluster_frac >.01 else "Small Clusters", axis=1) # merge small clusters
    

    # add new sequential cluster id from largest to smallest
    clus_df = pd.DataFrame(ndf['Cluster_Trimmed'].value_counts()).reset_index().reset_index() # add col of index 0-7
    clus_df.columns = ['index', 'Cluster_Trimmed', 'count']
    clus_df['Cluster_ID'] = clus_df['index'].apply(lambda x: 'Cluster_'+str(x+1))
    clus_id_dict = dict(zip(clus_df.Cluster_Trimmed, clus_df.Cluster_ID)) # dictionary of habit theme to ordered cluser id
    ndf['Cluster_ID'] = ndf['Cluster_Trimmed'].map(clus_id_dict)
    
    # add cluster labels as most Central habits
    ndf_sorted = ndf.sort_values(['Cluster_ID', 'ClusterCentrality'], ascending=[True, False])
    df_mostCentral = ndf_sorted.groupby('Cluster_ID').head(3).reset_index() # get top 3 most central habits of each group
    df_mostCentral_habits = df_mostCentral.groupby('Cluster_ID')['Habit'].apply(", ".join).reset_index() # join into string
    clus_label_dict = dict(zip(df_mostCentral_habits.Cluster_ID,df_mostCentral_habits.Habit))
    ndf['Central_Habits'] = ndf['Cluster_ID'].map(clus_label_dict)
    
    ndf['Label'] = ndf['Habit']
     
    ## add tsne layout coordinates
    ndf = tsne_layout(ndf, edf)

    # clean columns
    dropcols = ['InterclusterFraction', 'ClusterDiversity', 'Cluster', 'cluster_name', 'top_tags'] 
    ndf.drop(dropcols, axis=1, inplace=True)
    
    colOrder = ['id', 'Habit','Central_Habits', 'Frequency', 'Percent','Cluster_size', 'Cluster_frac', 
                'Degree','ClusterCentrality', 'ClusterBridging',  'Cluster_ID', 'Label', 'x_tsne', 'y_tsne']
    ndf = ndf[colOrder]
    
    print("\nCluster Names")
    print(ndf['Central_Habits'].value_counts())
    print("\n")

    
    if write:
        #### plot network and write to file
        node_sizes = ndf.loc[:,'ClusterCentrality']*10
        node_sizes_array = node_sizes.values # convert clustercentrality to array for sizing
        plot_network(ndf, edf, plotname, x='x_tsne', y='y_tsne', colorBy='Central_Habits', node_size=node_sizes_array)

        # write network files
        write_network_file(ndf, edf, nwname)

    return ndf, edf    
    
def buildTagHistDf (df, col, blacklist=[], mincnt=0):
    '''
    # generate dictionary of tags and tag counts for a column, exclude rows with no data
    # trim each dataset to tags with greter than mincnt l
    '''
    total = len(df)
    tagDict = {}
    df[col].fillna('', inplace=True)
    tagLists = df[col].str.split('|').apply(lambda x: [ss.strip(' ') for ss in x]) # strip empty spaces for each item in each list
    tagLists = tagLists.apply(lambda x: [t for t in x if t not in blacklist])
    tagHist = OrderedDict(Counter([t for tags in tagLists for t in tags if t != '']).most_common())
    tagDict[col] = list(tagHist.keys())
    tagDict['count'] = list(tagHist.values())
    tagdf = pd.DataFrame(tagDict)
    tagdf['percent'] = tagdf['count'].apply(lambda x: np.round((100*(x/total)),2))
    tagdf = tagdf[tagdf['count']>mincnt]  # remove clusters 10 or less
    return tagdf

def people2tags(df, peopleCol = 'id', tagsCol = 'tags', delim="|", blacklist=[]):
    '''
    Convert dataframe of people ids with tags into unique tags with list of people
    peopleCol = origina node id
    tagsCol = pipe-separated string of tags
    blacklist = tags to remove from final list
    '''
    df = df[[peopleCol, tagsCol]].reset_index(drop=True) # trim columns
    # create histogram of tag frequencies (for tag metadata)
    df_habit_distr = buildTagHistDf (df, tagsCol, blacklist=blacklist)
    df_habit_distr.columns= ["Habit", 'Frequency', 'Percent']

    # convert from tag string to list, remove white spaces
    df[tagsCol]= df[tagsCol].str.split(delim).apply(lambda x: [t.strip() for t in x]) #
    df_explode_tags = df.explode(tagsCol) # explode the tags list into rows
    df_explode_tags.columns=['People', 'Habit'] # rename cols
    
    # aggreagete by habit and make people id's new tag list
    df_habits = df_explode_tags.groupby('Habit')['People'].apply(list) 
    df_habits = df_habits.reset_index()
    
    # remove blacklist habits
    df_habits = df_habits[~df_habits['Habit'].isin(blacklist)]
    # add tag frequencies as node metadata
    df_habits = df_habits.merge(df_habit_distr, on='Habit', how='left')

    return df_habits

    


################################################################

if __name__ == '__main__':
    # paths
    wd = pl.Path.cwd()
    datapath = wd/"data"
    resultspath = wd/"results"
    figpath = wd/"figures"
    
 
    ### parameters for building network
    idf = False
    linksPer = 6
    tags = 'tags'
    tagattr = tags+"_list" # buildNetwork needs tags as a list
    blacklist = ['Emotionally Stable', 'Tortured Artist'] 
    
    # file names
    infile = datapath/"CreativeStyle_Responses_Tagged_Cleaned.xlsx"
   
    version = "2020_11_25"
    run_params = str(linksPer) + "links_" + version 
 
    habit_nw = resultspath/("Habits_Network_"  + run_params + ".xlsx")
    plot_name = figpath/("Habits_Network_" + run_params + ".pdf")
    
    
    print ('reading file')
    df = pd.read_excel(infile, engine='openpyxl')
    
    # convert to unique habits with people as tag list
    df_habits = people2tags(df, peopleCol='id', tagsCol=tags, blacklist=blacklist)
    
    ndf,ldf = build_habit_network(df_habits, 'People',  write=True, 
                                nwname=habit_nw, plotname=plot_name, 
                                idf=False, linksPer=linksPer, blacklist=[])


    
    
    


