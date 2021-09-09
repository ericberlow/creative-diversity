# -*- coding: utf-8 -*-

# import pandas as pd

import pathlib as pl
from prepare_data import clean_HC_data  # , buildTagHistDf
from build_decorate_network import build_creative_style_network
from sensitivity_analysis import compute_sampled_similarity, compare_network_clusters
from plot_figures import plot_histogram, plot_cluster_stats
import pandas as pd
from ast import literal_eval
import params

# ####### paths
wd = pl.Path.cwd()
datapath = wd/"data"
resultspath = wd/"results"
figpath = wd/"figures"

# #######  parameters for building network and sensitivity analysis
all_linksPer =  params.all_linksPer # list of link densities (6-12) to explore - > final choice was 10 links/node
tags = params.tags # pipe-separated tags attr
tagattr = params.tagattr  #  tags converted to list for  buildNetwork needs tags as a list
blacklist = params.blacklist  # removed ["Emotionally Stable", "Tortured Artist"] 
maxtags = params.maxtags # top tags to compare for cluster similarity
weighted = params.weighted  # compare clusters using weighted tag distribution rather than top tags.

# #######  filenames
infile = params.responses_raw_data  # raw survey respones
processed_file = params.responses_cleaned_processed # cleaned file with tags
tags_file = params.tagdistr_file  # tag distribution summary


# ################################################################
# ####### process/clean  raw survey responses into creative habit tags
if processed_file.is_file():  # if already processed load it
    print("reading processed survey data")
    df = pd.read_excel(processed_file, engine='openpyxl')
    df.fillna('', inplace=True)
    df[tagattr] = df[tagattr].apply(literal_eval)  # convert from string to list
else:  # ## otherwise prepare data from raw survey responses
    print("processing raw survey data")
    df = clean_HC_data(infile, processed_file, tags_file)
    df.fillna('', inplace=True)

# ################################################################
# ####### build networks from tags - multiple networks with different link densities
# ####### compare cluster similarities acrtoss different networks and summarize results

for linksPer in all_linksPer:
    # #######  filename params
    version = params.version 
    if blacklist == []:
        run_params = "allTags_" + str(linksPer) + "links_" + version  # tag blasklisted, linksPer Node, date
    else:
        run_params = "minus" + str(blacklist) + "_" + str(linksPer) + "links_" + version

    sim_params = run_params
    if not weighted:
        sim_params += "_" + str(maxtags) + "maxtags"  # add maxtags to suffix for sensitivity analysis

    # parameter-dependent files
    nw_name = resultspath / ("CreativeStyle_Network_" + run_params + ".xlsx")  # network file
    clusters_name = resultspath / ("Top_CreativeStyles_" + run_params + ".csv")  # top clusters summary (small clus)
    nw_plot_name = figpath/("CreativeStyle_Network_" + run_params + ".pdf")
    clus_stats_name = resultspath/("CreativeStyles_ClusterStats_" + sim_params + ".csv")  # sensitivity analysis

    #  ####### build creative style network from tags
    if nw_name.is_file():  # load file if there
        print("reading network file")
        ndf = pd.read_excel(nw_name, engine='openpyxl')
    else:  # otherwise build network and write file
        print("building creative style network")
        ndf, edf = build_creative_style_network(df, tagattr, doLayout=True,
                                                write=True, nwname=nw_name, clusname=clusters_name,
                                                plotname=nw_plot_name, idf=False, linksPer=linksPer, blacklist=blacklist
                                                )

    ########  run sensitivity analysis
    if clus_stats_name.is_file():  # load cluster stability stats if it's there
        print('reading cluster stats file')
        clus_stat_df = pd.read_csv(clus_stats_name)
                         
    else: # otherise run sampled cluster similarities
        print('running sensitivity analysis')
        # df is the processed survey data, nw_name is the reference network file
        clus_stat_df = compute_sampled_similarity(df, nw_name, tagattr, sim_params, 
                         idf=False, linksPer = linksPer, blacklist=blacklist,
                         clus_attr='cluster_name',
                         niter=100, frac=0.5, maxtags=maxtags)
    
    
    ######## plot figures
    
    # plot_histogram(ndf, 'tags', "Creative Habits", sim_params, mincount=0, metric='percent', w=800, h=600 )
    # plot_cluster_stats(clus_stat_df, sim_params)
    # plot_histogram(ndf, 'cluster_name', "Creative Styles", sim_params, mincount=10, metric='percent', w=800, h=600 )

    
