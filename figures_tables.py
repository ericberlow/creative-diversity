####################################

#from collections import Counter, OrderedDict
import pandas as pd
import numpy as np
import math
from prepare_data import buildTagHistDf
#import pathlib as pl
import altair as alt
import params
from build_decorate_network import write_network_file
import build_archetypeNetwork_player as build_arch
import build_habitNetwork_player as build_hab

pd.set_option('display.expand_frame_repr', False) # expand display of data columns if screen is wide


## colors 
# also see vega color schemes here https://vega.github.io/vega/docs/schemes/ 
cluster_colors = params.cluster_colors 
cluster_colors_30 = params.cluster_colors_30 



def summarize_cluster_distribution(df, creativeSpecies = 'Creative_Species', removeSmall=False):
    ### creative style distrubtion (full network)
    #df_cluster_distr = df.groupby([creativeSpecies, 'Cluster_ID'])['Cluster_Fraction'].agg('count').reset_index()
    df_cluster_distr = df.groupby([creativeSpecies, 'Cluster'])['Cluster_Fraction'].agg('count').reset_index()
    df_cluster_distr.columns = ['Creative_Species', 'Cluster', 'Count']
    df_cluster_distr['Percent'] = 100 * ((df_cluster_distr['Count']/df_cluster_distr['Count'].sum()).round(4))
    df_cluster_distr = df_cluster_distr.sort_values(['Percent'], ascending=False).reset_index(drop=True)
    df_cluster_distr['Cluster'] = df_cluster_distr['Cluster'].apply(lambda x: "Small Clusters" if x == 'Cluster_8' else x) # renamme cluster 8
    
    if removeSmall:
        # option to plot without  small clusters group
        df_cluster_distr = df_cluster_distr[df_cluster_distr['Creative_Species'] != "Misc. Small Clusters"] # remove small clusters
    return df_cluster_distr


def generate_habits_distribution(df):
    # df = full network
    # generate global creative habit distribution
    df_habits =  buildTagHistDf(df, 'Creative_Habits')
    df_habits.sort_values('percent', ascending=False, inplace=True)
    return df_habits
    



############################################################
# CLEAN FINAL DATA FOR FIGURES >
# RENAME HABITS, RENAME ORDINAL COLS, CLEAN DISCIPLINES AND GENDER
#############################################################

def add_broad_tags(x, mappingDict):
    '''
    x is a pipe-separated string of discipline tags
    mappingDict is dictionary mapping specific tags to broad tags
    If the tag is not in the dictionary, don't keep it
    Clean dupes
    Returns a new pipe-separated string of renamed habits
    '''
    newTagList = []
    tagList = x.split("|") if x else []
    for tag in tagList:
        if tag in mappingDict:
            newTagList.append(mappingDict[tag])
    newTagList = list(set(newTagList)) # get unique tags, 
    broadTags = "|".join(newTagList) # join list back into string of tags
    return broadTags


def rename_habits(x, habitDict = params.habit_renameDict, delim="|"):
    '''
    x is a pipe-separated string habits
    Rename habit tags from a renaming dictionary 
    If the habit is not in the dictionary, keep the old one
    Returns a new pipe-separated string of renamed habits
    '''
    newhabitlist = []
    habitlist = x.split(delim) if x else []
    for habit in habitlist:
        if habit in habitDict:
            newhabitlist.append(habitDict[habit])
        else:
            newhabitlist.append(habit)
    newhabits = delim.join(newhabitlist)
    return newhabits

def clean_creative_style_networks(ndf, ldf, outname):
    # clean/rename habit dimensions and habit tags
    ndf.reset_index(drop=True)
    ndf.rename(columns = params.ordCol_renameDict, inplace=True)
    ndf['Creative_Habits'] = ndf['Creative_Habits'].apply(lambda x: rename_habits(x))
    ndf['label'] = ndf['id']
    
    # rename habits in cluster labels
    ndf.rename(columns={'Creative_Style': 'Creative_Species', 'Cluster_ID': 'Cluster'}, inplace=True)
    ndf['Creative_Species'] = ndf['Creative_Species'].apply(lambda x: rename_habits(x, delim=", "))
    ndf['Cluster'] = ndf['Cluster'].str.replace("Cluster_", "Creative Species ")
    ndf['Creative Species'] = ndf['Cluster'].map(params.creative_species_dict)
    
    #### add broad discipline tags (Art, Science, Business)
    df_discMap = pd.read_csv(params.discipline_map) # map disciplines to science, art, business
    discDict = dict(zip(df_discMap['Discipline'],df_discMap['mapTo'])) #dictionary mapping discipline to art, sci, biz
    ndf['Discipline'].fillna('', inplace=True)
    ndf['Discipline'] = ndf['Discipline'].apply(lambda x: add_broad_tags(x, discDict))
    
    #### add Gender category mappings 
    df_genderMap = pd.read_csv(params.gender_map) # map non-binary gender responses to one
    genderDict = dict(zip(df_genderMap['Gender'],df_genderMap['mapTo'])) #dictionary mapping gender to categories
    ndf['Gender'].fillna('', inplace=True)
    ndf['Gender'] = ndf['Gender'].apply(lambda x: add_broad_tags(x, genderDict))  
    
    # fill missing ordinal with neutral value (3):
    ndf[params.habit_dimension_cols] = ndf[params.habit_dimension_cols].astype('Int64')
    # clean final columns
    ndf.drop(['Creative Advice'], axis=1, inplace=True)
    ndf.rename(columns=params.final_Network_renameDict, inplace=True) 
    
    ### write cleaned file to 'submitted' folder
    write_network_file(ndf, ldf, outname)
    return ndf
    

def clean_habits_network(ndf, ldf, outname):
    # rename habits and habvit dimensions 
    ndf['Habit'] = ndf_habits['Habit'].apply(lambda x: rename_habits(x))
    ndf['Label'] = ndf['Habit']
    
    # clean final columns
    ndf.drop(['Cluster_frac'], axis=1, inplace=True)
    ndf.rename(columns=params.final_HabitNetwork_renameDict, inplace=True) 
     
    ### write cleaned file to 'submitted' folder
    write_network_file(ndf, ldf, outname)
    return ndf
    

 
##############################################################
#Figure 1 - Creative Habit and Creative Style Distributions
##############################################################

def make_figure_1(df, removeSmall=False):
    # df - full network
    
    ### first get global creative habit distribution
    df_habits =  generate_habits_distribution(df) # [[Note - this is now computed here from full network df so it does not include blacklisted habits]]
    
    # plot global tag distribution for each cluster 
      # plot parameters
    pct_sort = alt.EncodingSortField(field='Percent', order='descending')
    fix_pct_scale = alt.Scale(domain=[0, 100])
    tag_sort_all = alt.EncodingSortField(field='percent', order='descending')
    
    plot_tags_global = alt.Chart(df_habits).mark_bar().encode(
                            x= alt.X("percent:Q", scale=fix_pct_scale, title="Percent"),
                            y= alt.Y("Creative_Habits:N", sort=tag_sort_all, title=""),
                            color= alt.Color("percent:Q", legend=None, scale=alt.Scale(scheme='redyellowblue', domain=[10, 50])),
                            tooltip=['Creative_Habits', 'percent'],
                        ).properties(
                            width=225,
                            height=400,
                            title = "a) Creative Habits (% of People)"
                        ).interactive()
    
    # plot bar chart of cluster sizes 
    # summarize clusters
    df_cluster_distr = summarize_cluster_distribution(df, removeSmall=removeSmall)
    # get list of unique clusters to create color pallette 
    cluster_list = df_cluster_distr.Cluster.tolist()
    cluster_palette = alt.Scale(domain=cluster_list,
                      range=cluster_colors)
    
    plot_cluster_sizes = alt.Chart(df_cluster_distr).mark_bar().encode(
                            x= alt.X("Percent:Q"), #scale=fix_pct_scale),
                            y= alt.Y("Cluster:N", sort=pct_sort, title=""), # use cluster id as label
                            #color= alt.Color("Cluster:N", scale=alt.Scale(scheme='set2', domain=cluster_list), legend=None),
                            color= alt.Color("Cluster:N", scale = cluster_palette, legend=None),
                            tooltip=['Creative_Species', 'Percent'],
                        ).properties(
                            width=225,
                            height=400,
                            title = "b) 'Creative Species' (% of People)"
                        ).interactive()
    
    ## layout and print charts                        
    fig_1_charts = (plot_tags_global | plot_cluster_sizes)       
    fig_1_charts.save("figures/figure_1.html")
    #fig_1_charts.save("figures/figure_1.png")


##############################################################
#Figure 4 - Disciplines by Cluster
##############################################################
# plot bar chart of discipline z-scores by cluster

def make_figure_4(df, df_disc):
    #df = full network results
    #df_disc = sampled zscores of disciplines by cluster
    
    # summarize clusters to create color pallete
    df_cluster_distr = summarize_cluster_distribution(df, creativeSpecies = 'Creative_Species', removeSmall=False)
    # get list of unique clusters to create color pallette 
    cluster_list = df_cluster_distr.Cluster.tolist()
    cluster_palette = alt.Scale(domain=cluster_list,
                      range=cluster_colors)

    # sort axis by cluster ID 
    cluster_sort = alt.EncodingSortField(field='Cluster', order='ascending')
    # set axis ranges
    z_scale = alt.Scale(domain=[-12, 12])
    pct_diff_scale = alt.Scale(domain=[-50, 50])
    #diff_scale = alt.Scale(domain=[-15, 15])
    
    # plot z_scores of obs discipline frac 
    plot_zscores = alt.Chart(df_disc).mark_bar().encode(
                            x= alt.X("zScore:Q", scale=z_scale),
                            y= alt.Y("Cluster:N", sort=cluster_sort, title=""), # use cluster id as label
                            #color= alt.Color("Cluster:N", scale=alt.Scale(scheme='set2', domain=cluster_list), legend=None),
                            color= alt.Color("Cluster:N", scale = cluster_palette, legend=None),
                            tooltip=['Cluster', 'Creative_Species', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore'],
                            column = alt.Row('Discipline:N', title=None)
                        ).properties(
                            width=275,
                            height=300,
                            #title = "Creative Styles by Discipline"
                        ).interactive()
     
    
    # plot percent diff of observed discipline frac vs random samples      
    plot_pct_diffs = alt.Chart(df_disc).mark_bar().encode(
                            x= alt.X("Percent Difference:Q", scale=pct_diff_scale),
                            y= alt.Y("Cluster:N", sort=cluster_sort, title=""), # use cluster id as label
                            #color= alt.Color("Cluster:N", scale=alt.Scale(scheme='set2', domain=cluster_list), legend=None),
                            color= alt.Color("Cluster:N", scale = cluster_palette, legend=None),
                            tooltip=['Cluster', 'Creative_Species', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore'],
                            column = alt.Row('Discipline:N', title=None)
                        ).properties(
                            width=275,
                            height=300,
                            #title = "Creative Styles by Discipline"
                        ).interactive()

    '''                            
    # absolute diff of observed discipline frac vs random samples                        
    plot_diffs = alt.Chart(df_disc).mark_bar().encode(
                            x= alt.X("Difference (%):Q", scale=diff_scale),
                            y= alt.Y("Cluster_ID:N", sort=cluster_sort, title=""), # use cluster id as label
                            #color= alt.Color("Cluster:N", scale=alt.Scale(scheme='set2', domain=cluster_list), legend=None),
                            color= alt.Color("Cluster_ID:N", scale = params.cluster_palette, legend=None),
                            tooltip=['Cluster_ID', 'Creative_Style', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore'],
                            column = alt.Row('Discipline:N', title=None)
                        ).properties(
                            width=275,
                            height=300,
                            #title = "Creative Styles by Discipline"
                        ).interactive()  
    '''
    
    # write chart to file
    plot_pct_diffs.save("figures/figure_4a_permuted.html")
    plot_zscores.save("figures/figure_4b._permuted.html")
    
    discipline_chart = plot_pct_diffs & plot_zscores
    discipline_chart.save("figures/figure_4_permuted.html")
                            
    
##############################################################
#Figure 5 - Gender by Cluster
##############################################################
# plot bar chart of discipline z-scores by cluster

def make_figure_5(df, df_gender):
    #df = full network results
    #df_gender = sampled zscores of disciplines by gender
    
    # summarize clusters to create color pallete
    df_cluster_distr = summarize_cluster_distribution(df, creativeSpecies = 'Creative_Species', removeSmall=False)
    # get list of unique clusters to create color pallette 
    cluster_list = df_cluster_distr.Cluster.tolist()
    cluster_palette = alt.Scale(domain=cluster_list,
                      range=cluster_colors)

    # sort axis by cluster ID 
    cluster_sort = alt.EncodingSortField(field='Cluster', order='ascending')
    # set axis ranges
    z_scale = alt.Scale(domain=[-12, 12])
    pct_diff_scale = alt.Scale(domain=[-100, 100])
    #diff_scale = alt.Scale(domain=[-15, 15])
    
    # plot z_scores of obs discipline frac 
    plot_zscores = alt.Chart(df_gender).mark_bar().encode(
                            x= alt.X("zScore:Q", scale=z_scale),
                            y= alt.Y("Cluster:N", sort=cluster_sort, title=""), # use cluster id as label
                            #color= alt.Color("Cluster:N", scale=alt.Scale(scheme='set2', domain=cluster_list), legend=None),
                            color= alt.Color("Cluster:N", scale = cluster_palette, legend=None),
                            tooltip=['Cluster', 'Creative_Species', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore'],
                            column = alt.Row('Gender:N', title=None)
                        ).properties(
                            width=275,
                            height=300,
                            #title = "Creative Styles by Discipline"
                        ).interactive()
     
    
    # plot percent diff of observed discipline frac vs random samples      
    plot_pct_diffs = alt.Chart(df_gender).mark_bar().encode(
                            x= alt.X("Percent Difference:Q", scale=pct_diff_scale),
                            y= alt.Y("Cluster:N", sort=cluster_sort, title=""), # use cluster id as label
                            #color= alt.Color("Cluster:N", scale=alt.Scale(scheme='set2', domain=cluster_list), legend=None),
                            color= alt.Color("Cluster:N", scale = cluster_palette, legend=None),
                            tooltip=['Cluster', 'Creative_Species', 'Percent', 'Difference (%)', 'Percent Difference', 'zScore'],
                            column = alt.Row('Gender:N', title=None)
                        ).properties(
                            width=275,
                            height=300,
                            #title = "Creative Styles by Discipline"
                        ).interactive()

     
    # write chart to file
    plot_pct_diffs.save("figures/figure_5a_permuted.html")
    plot_zscores.save("figures/figure_5b._permuted.html")
    
    discipline_chart = plot_pct_diffs & plot_zscores
    discipline_chart.save("figures/figure_5_permuted.html")
                           


##############################################################
# Table 2 - Cluster top habit summary (also Figure xx)
##############################################################

def plot_top_habits_by_Cluster(df_topTags_byCluster):
    # plot parameters
    tag_sort = alt.EncodingSortField(field='Weight', order='descending')
    clus_sort = alt.EncodingSortField(field='Cluster_Frac', order='descending')
    #rel_freq_scale = alt.Scale(domain=[0, 2.75])
    freq_scale = alt.Scale(domain=[0, 100])
    
    # plot top tags for each cluster - in columns, 
    # sort tags by tag weight, bar height is frequency and color is relative frequency
    # each cluster separate plot in 1 row and multiple columns
    
    plot_topTags_byCluster = alt.Chart(df_topTags_byCluster).mark_bar().encode(
                            y = alt.Y("Creative_Habits:N", sort=tag_sort, title=None), # 
                            x = alt.X("Frequency:Q", scale=freq_scale, title="Frequency"),
                            color = alt.Color('Relative_Frequency:Q', title="Relative Frequency"), #legend =None),
                            tooltip = ['Creative_Species', 'Creative_Habits', 'Frequency', 'Global_Frequency', 'Relative_Frequency'],
                            column = alt.Row('Cluster:N', sort=clus_sort, title=None)
                        ).properties(
                            width=100,
                            height=200,
                            title = "Most Common and OverRepresented Creative Habits"
                        ).resolve_axis(
                            #x='independent',
                            y='independent',
                        ).resolve_scale(
                            y='independent', # allows separate sorting for each facet
                        ).interactive()
    
    # write chart to file
    plot_topTags_byCluster.save("figures/figure_x_topTags_byCluster.html")

def summarize_top_habits_by_cluster(df, thresh_abs, thresh_rel, outfile):
    # get tag distributions for each Creative Style in one dataframe 
    # compute absolute and relative frequency for each tag
    # geneate plot of top tags by cluster
    #thresh_abs = absolute frequency threshold to keep
    #thresh_rel = relative frequency threshold to keep
    #df_habits = global tag distribution all tags
    #Returns: concatenated dataframe of clusters and tag frequencies for each
    
    df_styles = df[df['Creative_Species'] != "Misc. Small Clusters"] # remove misc clusters if they are present
    df_styles = df_styles.reset_index(drop=True) 
    style_list = df_styles['Creative_Species'].unique().tolist()
    style_id_dict = dict(zip(df_styles.Creative_Species, df_styles.Cluster)) # dictionary of cluster name to ordered cluster id
    # create dictionary of global freq for each habit tag
    df_habits = generate_habits_distribution(df)
    global_freq_dict = dict(zip(df_habits.Creative_Habits, df_habits.percent)) # dictionary of global frequency for each tag

    df_list = []
    for style in style_list:
        df_style = df_styles[df_styles['Creative_Species'] == style]
        df_style = df_style.reset_index(drop=True)
        tagdf = buildTagHistDf(df_style, 'Creative_Habits', blacklist=params.blacklist)
        tagdf['Creative_Species'] = style
        tagdf['Global_Frequency'] = tagdf['Creative_Habits'].map(global_freq_dict) # add global frequency 
        #tagdf['normalized_frequency'] = (tagdf.percent - tagdf.global_pct)/(tagdf.percent + tagdf.global_pct)
        tagdf['Relative_Frequency'] = np.round((tagdf.percent/tagdf.Global_Frequency),2)
        tagdf['Weight'] = np.round((tagdf['percent']*np.sqrt(tagdf['Relative_Frequency'])),2)
        tagdf['Cluster'] = tagdf['Creative_Species'].map(style_id_dict)
        tagdf.rename(columns = {'percent': 'Frequency'}, inplace=True)
        df_list.append(tagdf)
      
    df_styles_tagdist = pd.concat(df_list) # concatenate into one dataframe
    # add cluster size
    size_dict = dict(zip(df.Creative_Species,df.Cluster_Fraction))
    df_styles_tagdist['Cluster_Frac'] = df_styles_tagdist['Creative_Species'].map(size_dict)
    df_styles_tagdist['Cluster_Frac'] = df_styles_tagdist['Cluster_Frac'].apply(lambda x: 100 * np.round(x,4))
    # sort by cluster size and tag weight (absolute * relative frequency)
    df_styles_tagdist = df_styles_tagdist.sort_values(['Cluster_Frac', 'Weight'], ascending=[False, False]).reset_index(drop=True)

    # get# most common and over-represnted tag per cluster
    mostCommon = ((df_styles_tagdist['Frequency'] >=thresh_abs) | (df_styles_tagdist['Relative_Frequency'] >=thresh_rel))
    df_topTags_byClus = df_styles_tagdist[mostCommon]  
    df_topTags_byClus = df_topTags_byClus[['Creative_Species','Cluster', 'Creative_Habits', 'Weight', 'Frequency', 'Relative_Frequency', 'Global_Frequency','Cluster_Frac']]
    
    #mostRare =  ((df_styles_tagdist['percent'] <= 10) & (df_styles_tagdist['relative_frequency'] <=0.25))
    #df_bottomTags_byClus = df_styles_tagdist[mostRare]
    #df_styles_tag_sum = pd.concat([df_topTags_byClus, df_bottomTags_byClus]) # concatenate into one dataframe

    # summarize # clusters per top tag - and identify ones that are un-represented
    df_topTags_sum = df_topTags_byClus.groupby('Creative_Habits')['Cluster'].agg('count').reset_index()
    df_topTags_sum.columns = ['Creative_Habits', 'Cluster_Count']
    df_allHabits = df_habits[['Creative_Habits']]
    df_topTags_sum = df_topTags_sum.merge(df_allHabits, on='Creative_Habits', how='outer')
    df_topTags_sum['Cluster_Count'].fillna(0, inplace=True)
    df_topTags_sum.sort_values(['Cluster_Count'], ascending=False, inplace=True)
    df_topTags_sum.reset_index(drop=True, inplace=True)
    frac_tags_in_topTags = np.round(100*(sum(df_topTags_sum['Cluster_Count']>0)/len(df_topTags_sum)),2)
    tags_w_no_cluster = sum(df_topTags_sum['Cluster_Count']==0)
    print("\n%s percent of all tags are in the top tags of at least one cluster" %(str(frac_tags_in_topTags)))
    print("%d tags with no cluster \n" %tags_w_no_cluster)
    print(df_topTags_sum)
    
    # summarize # top tags for each cluster 
    df_cluster_sum = df_topTags_byClus.groupby('Creative_Species')['Cluster'].agg('count').reset_index()
    df_cluster_sum.columns = ['Creative_Species', 'Top_Tags_Count']
    avg_topTags_per_cluster = np.round((df_cluster_sum['Top_Tags_Count'].mean()),2)
    print("\n %s top habits per style \n" %str(avg_topTags_per_cluster))
    print(df_cluster_sum)
    
    # write summary file for table
    df_topTags_byClus.to_excel(outfile, index=False)
    
    # plot top tags by cluster
    plot_top_habits_by_Cluster(df_topTags_byClus)




##############################################################
# Supplement Figure 1a - Creative Style Stability
##############################################################

def make_si_fig_1a(df_clus):
    # df_clus = cluster sensitivity analysis summary
    
    # add cluster id as alt label
    df_clus = df_clus.reset_index() # resampled network results - all 30 clusters
    df_clus['Cluster_ID'] = df_clus['index'].apply(lambda x: 'Cluster_'+str(x+1))
    df_clus.drop(['index'], axis=1, inplace=True)
    
    
    # add error bar range
    df_clus['errorBar_max'] = df_clus['Avg_Similarity'] + df_clus['Std_Similarity']
    df_clus['errorBar_min'] = df_clus['Avg_Similarity'] - df_clus['Std_Similarity']
    

    # specify order of y-axis by making ordered list
    #clus_list = ['']+ df_clus['Cluster'].unique().tolist() +[''] # list of clusters sorted largest to smallest for y axis
    #clus_list_2 = ['', '']+ df_clus['Cluster_ID'].unique().tolist() +['', ''] # list of cluster id's sorted largest to smallest for y axis
    
    #clusterID_sort = alt.EncodingSortField(field='Cluster_ID', order='ascending')
    clusetrFrac_sort = alt.EncodingSortField(field='Cluster_frac', order='descending')
    sim_scale = alt.Scale(domain=[0, 1])
    clusterID_list = df_clus.Cluster_ID.tolist()
    cluster_palette = alt.Scale(domain=clusterID_list,
                      range=cluster_colors_30)
    
    # plot cluster stability with error bars
        # the base chart
    points = alt.Chart(df_clus).mark_circle().encode(
        x = alt.X("Avg_Similarity:Q", scale=sim_scale, title="Average Similarity to 100 Sampled Networks"), 
        y = alt.Y("Cluster_ID:N",
                  sort=clusetrFrac_sort,
                  title = "Creative Species Cluster",
                  #axis=alt.Axis(values=clus_list_2, tickCount=40), 
                  ),
        size = alt.Size("Cluster_frac", legend=None, scale=alt.Scale(range=[5, 400])),
        color= alt.Color("Cluster_ID:N", scale = cluster_palette, legend=None),
        tooltip = ['Cluster', 'Avg_Similarity', 'Cluster_frac'],
        #filled = True  
        ).interactive()
    
       # generate the error bars
    errorbars = alt.Chart(df_clus).mark_errorbar().encode(
        y = alt.Y("Cluster_ID:N", 
                  sort=clusetrFrac_sort, 
                  #axis=alt.Axis(values=clus_list_2, tickCount=40), 
                  ),
        x = alt.X("errorBar_min:Q", scale=sim_scale, title=''), 
        x2 ="errorBar_max:Q",
        color= alt.Color("Cluster_ID:N", scale = cluster_palette, legend=None),
        )
    
    plot_sampled_cluster_stability = (points + errorbars).configure_axisY(
                                        labels = True,
                                        tickExtra = True,
                                     ).properties(
                                         width=500,
                                         height=300
                                    ).interactive()
                                                                        
       
    plot_sampled_cluster_stability.save("figures/SI_figure_1a.html")



##############################################################
# Supplement Figure 1b - Stability to Link density - compare netowrks
##############################################################

def make_si_fig_1b(df_compare, df_clus):
    # df_clus = resampled network results for cluster sensitivity analysis
    # df_compare = comparison of networks with different link density
    
    ####################################################
    ### prepare data for scatterplot with error bars ###
    
    # add cluster id and map to cluster name
    df_clus = df_clus.reset_index() # resampled network results - all 30 clusters
    df_clus['Cluster_ID'] = df_clus['index'].apply(lambda x: 'Cluster_'+str(x+1))
    df_clus.drop(['index'], axis=1, inplace=True)
   
    style_id_dict = dict(zip(df_clus.Cluster, df_clus.Cluster_ID)) # dictionary of cluster name to ordered cluser id
    df_compare['ref_clus_id'] = df_compare['ref_clus'].map(style_id_dict)
    df_compare['target_clus_id'] = df_compare['max_clus'].map(style_id_dict)
    df_compare.drop(['sim_mn', 'sim_sd', 'percentile_max_sim'], axis=1, inplace=True)
    
    # add linksPer lable to each network
    linksperDict = {0:6, 1:7, 2:8, 3:9, 4:10, 5:11, 6:12}
    df_compare['ref_linksPer'] = df_compare['idx_1'].map(linksperDict)
    df_compare['target_linksPer'] = df_compare['idx_2'].map(linksperDict)
    
    # remove self-self
    self_self = df_compare['idx_1'] == df_compare['idx_2']
    df_compare = df_compare[~self_self].reset_index(drop=True)
    
    # keep 10 linksPer network and compare to rest
    df_10links_from = df_compare[df_compare['ref_linksPer']==10]
    df_10links_to = df_compare[df_compare['target_linksPer']==10]
    # reverse source and target for 10_links_to
    df_10links_to.columns = ['idx_2',
                             'idx_1',
                             'max_clus',
                             'max_frac',
                             'max_sim',
                             'ref_clus',
                             'ref_frac',
                             'target_clus_id',
                             'ref_clus_id',
                             'target_linksPer',
                             'ref_linksPer'] # reverse names of source and target
    
    df_10links = pd.concat([df_10links_from,df_10links_to ], axis=0)
    
    # remove where cluster frac <0.01
    #small_clusters = (df_10links['ref_frac'] < 0.01) |  (df_10links['max_frac'] < 0.01)
    #df_10links_lg = df_10links[~small_clusters].reset_index(drop=True)
    
    # trim to only best cluster matches'
    group = ['ref_linksPer', 'target_linksPer', 'ref_clus', 'ref_clus_id', 'ref_frac']
       # all clusters
    df_10links_maxSim = df_10links.groupby(group)['max_sim'].agg('max').reset_index()
    df_10links_maxSim = df_10links_maxSim.sort_values(['ref_frac'], ascending=False).reset_index()
    df_10links_means = df_10links_maxSim.groupby(['ref_clus_id', 'ref_frac']).agg({'max_sim':['mean','std', 'count']}).reset_index()
    df_10links_means.columns = ['ref_clus_id', 'ref_frac', 'avg_max_sim', 'std', 'n']
    df_10links_means['std_err'] = df_10links_means.apply(lambda x: x['std'] / math.sqrt(x['n']), axis=1)
    
     # add error bar range
    df_10links_means['errorBar_max'] = df_10links_means['avg_max_sim'] + df_10links_means['std']
    df_10links_means['errorBar_min'] = df_10links_means['avg_max_sim'] - df_10links_means['std']
    

    ####################################
    ### build scatterplot with error bars
    ####################################
    
    ## scatterplot parameters
    refFrac_sort = alt.EncodingSortField(field='ref_frac', order='descending')
    refID_list = df_10links_maxSim.ref_clus_id.tolist()
    cluster_palette = alt.Scale(domain=refID_list, range=cluster_colors_30)
    sim_scale = alt.Scale(domain=[0, 1])
    data = df_10links_means
    
    # plot cluster stability with error bars
        # the base chart
    points = alt.Chart(data).mark_circle().encode(
        x = alt.X("avg_max_sim:Q", scale=sim_scale, title="Avg. Similarity to Networks with Different Link Densities"), 
        y = alt.Y("ref_clus_id:N",
                  sort=refFrac_sort,
                  title = "Creative Species Cluster",
                  ),
        size = alt.Size("ref_frac", legend=None, scale=alt.Scale(range=[5, 400])),
        color= alt.Color("ref_clus_id:N", scale = cluster_palette, legend=None),
        tooltip = ['ref_clus_id', 'avg_max_sim', 'ref_frac'],
        #filled = True  
        ).interactive()
    
       # generate the error bars
    errorbars = alt.Chart(data).mark_errorbar().encode(
        y = alt.Y("ref_clus_id:N", 
                  sort=refFrac_sort, 
                  ),
        x = alt.X("errorBar_min:Q", scale=sim_scale, title=''), 
        x2 ="errorBar_max:Q",
        color= alt.Color("ref_clus_id:N", scale = cluster_palette, legend=None),
        )
    
    plot_linksPer_stability = (points + errorbars).configure_axisY(
                                        labels = True,
                                        tickExtra = True,
                                     ).properties(
                                         width=500,
                                         height=300
                                    ).interactive()
                                                                        
       
    plot_linksPer_stability.save("figures/SI_figure_1b.html")




#################################################################################
if __name__ == '__main__':
    
        
    print('read files')
    ndf = pd.read_excel(params.creative_styles_network , sheet_name='nodes', engine='openpyxl') # nodes from full network
    ldf = pd.read_excel(params.creative_styles_network , sheet_name='links', engine='openpyxl') # links from full network

    ndf_arch = pd.read_excel(params.archetype_network, sheet_name='nodes', engine='openpyxl') # top archetype nodes
    ldf_arch = pd.read_excel(params.archetype_network, sheet_name='links', engine='openpyxl') # top archetype nodes
    
    df_disc_sampled = pd.read_csv(params.disciplines_by_cluster_sampled) # sampled frac disciplines by  cluster
    df_disc_permuted = pd.read_csv(params.disciplines_by_cluster_permuted) # permuted frac disciplines by cluster
    
    df_gender_permuted = pd.read_csv(params.gender_by_cluster_permuted) # permuted frac gender by cluster

    df_clus = pd.read_csv(params.cluster_stats) # resampled network results - all 30 clusters
    df_compare = pd.read_csv(params.network_comparision) # network comparison analysis results
    
    ndf_habits = pd.read_excel(params.habits_network, sheet_name='nodes', engine='openpyxl') # nodes from habits network
    ldf_habits = pd.read_excel(params.habits_network, sheet_name='links', engine='openpyxl') # nodes from habits network
    
    

    # CLEAN and WRITE final networks (e.g. final habit names, habit dimension names, disciplines, gender)
    ndf = clean_creative_style_networks(ndf, ldf, params.final_creative_styles_network)
    ndf_arch = clean_creative_style_networks(ndf_arch, ldf_arch, params.final_archetype_network) 
    ndf_habits = clean_habits_network(ndf_habits, ldf_habits, params.final_habits_network)
    for df in [df_disc_permuted, df_gender_permuted]:
        df.rename(columns = {"Cluster_ID": "Cluster", 'Creative_Style': 'Creative_Species'}, inplace=True)
        df['Cluster'] = df['Cluster'].str.replace("Cluster_", "Creative Species ")
        df['Creative Species'] = df['Cluster'].map(params.creative_species_dict)
    
    #Figure 1 - Creative Habit and Creative Style Distributions
    #make_figure_1(ndf, removeSmall=False)
    

    #Figure 2 - Creative Styles Archetype network (openmappr svg download >> powerpoint)   
    ndf_arch.rename(columns={'Creative_Species': 'Top Species Habits',
                             'Creative_Habits': 'Creative Habits'}, inplace=True)
    ndf_arch = ndf_arch[params.final_arch_cols] # trim and reorder columns for display
    build_arch.build_run_player(ndf_arch,ldf_arch, 
                    params.arch_hide_add,  # list custom attributes to hide from filters
                    params.arch_hideProfile_add, # list custom attributes to hide from right profile
                    params.arch_hideSearch_add, # list custom attribs to hide from search
                    params.arch_liststring_add, # string attribs to force as liststring
                    params.arch_tags_add,  # custom string attribs to render as tag-cloud
                    params.arch_wide_tags_add, # custom string attribs to render as wide tag-cloud
                    params.arch_text_str_add,   # custom string attribs to render as long text in profile
                    params.arch_email_str_add, # custom string attribs to render as email link  in profile
                    params.arch_playerpath, # directory to hold player data
                    params.arch_s3_bucket, # s3_bucket name
                    launch_local=False, 
                    upload_s3=True)

    '''    
    #Figure 3 - Creative Habits network - (openmapr svg download >> powerpoint) 
    build_hab.build_run_player(ndf_habits,ldf_habits, 
                    params.habit_hide_add,  # list custom attributes to hide from filters
                    params.habit_hideProfile_add, # list custom attributes to hide from right profile
                    params.habit_hideSearch_add, # list custom attribs to hide from search
                    params.habit_liststring_add, # string attribs to force as liststring
                    params.habit_tags_add,  # custom string attribs to render as tag-cloud
                    params.habit_wide_tags_add, # custom string attribs to render as wide tag-cloud
                    params.habit_text_str_add,   # custom string attribs to render as long text in profile
                    params.habit_email_str_add, # custom string attribs to render as email link  in profile
                    params.habit_playerpath, # directory to hold player data
                    params.habit_s3_bucket, #s3_bucket name
                    launch_local=False, 
                    upload_s3=True)



    #Figure 4 - Disciplines by Cluster (4a = % difference, 4b = zscore)
    make_figure_4(ndf, df_disc_permuted)


    #Figure 5 - Gender by Cluster (4a = % difference, 4b = zscore)
    make_figure_5(ndf, df_gender_permuted)

    # Table 1 - Survey summary (manually created in Excel)
    # see "Table_1_CreativeStyle-Survey-Phase3-Public.xlsx" 
    
    # Table 2 -Cluster top habit summary (also Figure for internal use)
    summarize_top_habits_by_cluster(ndf, 60, 1.5, params.style_tag_summary_table) # full network

    #summarize_top_habits_by_cluster(df_arch, 75, 2)  # archetype network
    # formatted version = "Table_2_CreativeStyles_TopTags.xlsx"
    
    
    #SI Figure 1a - Creative Style Stability
    make_si_fig_1a(df_clus)
    
    #SI Figure 1b - Stability to Link density - compare netowrks
    make_si_fig_1b(df_compare, df_clus)

    '''
    
##############################################################
