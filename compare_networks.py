import pathlib as pl
from prepare_data import clean_HC_data  # , buildTagHistDf
from sensitivity_analysis import compare_network_clusters
import pandas as pd
from ast import literal_eval

# ####### paths
wd = pl.Path.cwd()
datapath = wd/"data"
resultspath = wd/"results"
figpath = wd/"figures"

# #######  parameters for building network and sensitivity analysis
all_linksPer = [6, 7, 8, 9, 10, 11, 12]
tags = 'tags'
tagattr = tags + "_list"  # buildNetwork needs tags as a list
blacklist = ["Emotionally Stable", "Tortured Artist"]  # [] #["Early Bird", "Night Owl"]
maxtags = 10  # top tags to compare for cluster similarity
weighted = True

nw_list = []
for linksPer in all_linksPer:
    # #######  filename params
    version = "2020_11_25"
    if blacklist == []:
        run_params = "allTags_" + str(linksPer) + "links_" + version  # tag blasklisted, linksPer Node, date
    else:
        run_params = "minus" + str(blacklist) + "_" + str(linksPer) + "links_" + version

    sim_params = run_params
    if not weighted:
        sim_params += "_" + str(maxtags) + "maxtags"  # add maxtags to suffix for sensitivity analysis

    # parameter-dependent files
    nw_name = resultspath / ("CreativeStyle_Network_" + run_params + ".xlsx")  # network file

    print("reading network file")
    ndf = pd.read_excel(nw_name)
    nw_list.append(ndf)

# %%
results_df = compare_network_clusters(nw_list)

results_df.to_csv(resultspath/"NetworkComparison.csv", index=False)

# %%
# just keep biggest cluster
rdf = results_df[(results_df.ref_frac > 0.01) & (results_df.max_frac > 0.01)]
# group by network pair and compute aggregate stats
pair_df = rdf.groupby(['idx_1', 'idx_2']).agg({'max_sim': 'mean', 
                                               'percentile_max_sim': 'mean', 
                                               'idx_2': 'count', 
                                               'ref_frac': 'sum',
                                               'max_frac': 'sum',
                                               })


'''
mean max sim is consistently high - every big cluster has a closely-matching other cluster
count of idx is the number of big cluster pairs - this number drops as links per increases
ref_frac is the fraction of nodes in the big clusersof network 1 - increases as links per increases
max_frac > 1 because sometimes the same cluster in the second network is the best match to more 
than one cluster in the first nw

'''

'''
In pair_df, mean of max sim should be weighted by cluster size so small clusters have less influence on 
aggregate mean max sim
'''