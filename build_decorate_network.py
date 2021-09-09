

import sys
sys.path.append("../../../GitHub/Tag2Network/tag2network/Network")

import pandas as pd
import pathlib as pl
from BuildNetwork import buildTagNetwork, buildNetworkX
import BuildNetwork as bn
from DrawNetwork import draw_network_categorical
from ast import literal_eval 




def plot_network(ndf, edf, plot_name, x='x', y='y', colorBy='Creative_Style', node_size=30):    
    # draw network colored by creative style and save image
    nw = buildNetworkX(edf)
    draw_network_categorical(nw, ndf, node_attr=colorBy, plotfile=plot_name, x=x, y=y, node_size=node_size)
    
def write_network_file(ndf, edf, nw_name):    
    # write cleaned network file to excel with 2 sheets
    writer = pd.ExcelWriter(nw_name)
    ndf.to_excel(writer,'nodes', index=False)
    edf.to_excel(writer,'links', index=False)
    writer.save()

def tsne_layout(ndf, ldf):   
    ## add tsne-layout coordinates and draw
    bn.add_layout(ndf, linksdf=ldf, nw=None)
    ndf.rename(columns={"x": "x_tsne", "y": "y_tsne"}, inplace=True)
    return ndf

def build_creative_style_network(df, tagAttr,  write=False, nwname=None, clusname=None, plotname=None, 
                                idf=False, linksPer=6, blacklist=[], doLayout=False):   
    '''
    build network by creative style tag similarity, merge small clusters
    summarize top creative styles and write file
    plot network and write network file
    all files are named with the parameters for the run for comparison
    'tagAttr' = name of column with tags as list of tags
    'nwname' = name of newtork output file
    'clusname' = name of creative styles summary file
    'plotname' = name of network viz plot
    NOTE : tagAttr for build netowork must be a list of tags, not pipe-delimited string
    '''
    print("Building Creative Style Network minus %s" %str(blacklist))
    # remove blacklisted tags if any
    df[tagAttr] = df[tagAttr].apply(lambda x: [tag for tag in x if tag not in blacklist])
    # build network
    ndf, edf = buildTagNetwork(df, tagAttr=tagAttr, 
                    plotfile=None, doLayout=doLayout, outname=None,
                    idf=idf, linksPer=linksPer, minTags=3)
    
    # decorate nodes with added fields 
    ndf['Cluster_size'] = ndf.groupby(['Cluster'])['Cluster'].transform('count') # add counts
    ndf['Cluster_frac'] = ndf['Cluster_size']/len(ndf)
    ndf['Creative_Style'] = ndf.apply(lambda x: x.cluster_name  if x.Cluster_frac >.01 else "Misc. Small Clusters", axis=1)
    
    # add new sequential cluster id from largest to smallest
    clus_df = pd.DataFrame(ndf['Creative_Style'].value_counts()).reset_index().reset_index() # add col of index 0-7
    clus_df.columns = ['index', 'Creative_Style', 'count']
    clus_df['Cluster_ID'] = clus_df['index'].apply(lambda x: 'Cluster_'+str(x+1))
    clus_id_dict = dict(zip(clus_df.Creative_Style, clus_df.Cluster_ID)) # dictionary of cluster name to ordered cluser id
    ndf['Cluster_ID'] = ndf['Creative_Style'].map(clus_id_dict)
    ndf.drop(['Cluster'], axis=1, inplace=True)  # remove 'Cluster' for mappr upload
    
    ndf['Creative_Habits'] = ndf[tagAttr].apply(lambda x: "|".join(x))

    '''
    #TODO
    #### add Art, Science, Business dummy attributes
    df_discMap = pd.read_csv(datapath+"discipline_mapping_final.csv") # map disciplines to science, art, business
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

    '''
    
    # clean columns
    dropcols = ['Degree', 'InterclusterFraction', 'ClusterDiversity'] 
    ndf.drop(dropcols, axis=1, inplace=True)
    
    ndf.rename(columns={'(Slow vs Fast Paced': 'Slow -- Fast Paced'}, inplace=True)
    
    colOrder = ['id', 'Creative_Habits', 'Creative_Style', 'Gender', 'Discipline', 'Creative Advice',  'Cluster_ID',  
                'Montasker -- Multitasker', 'Specialist -- Generalist', 'Solo Creator -- Collaborator', 'Self-Critical -- Self-Assured', 
                'Distractible -- Focused', 'Inwardly vs Outwardly Inspired', 'Rational -- Intuitive', 'Internally vs Externally Motivated', 
                'NonKinetic -- Kinetic', 'Controlled Chaos -- Organized', 'Slow -- Fast Paced', 'Pragmastist -- Perfectionist', 
                'Risk Averse -- Risk Friendly', 'Make It Happen -- Let It Happen', 'Tenacious -- Reframer', 'Private vs Public Workspace', 
                'Work in Silence vs Noise/Music', 'Urban -- Nature',  'Novetly Seeker -- Creature of Habit', 'Stifled_By vs Stimulated_By Constraints', 
                'n_tags', 'ClusterBridging', 'ClusterCentrality', 'Cluster_frac', 'x', 'y']
    ndf = ndf[colOrder]
    
    if write:
        #### plot network and write to file
        plot_network(ndf, edf, plotname)
        
        # write top clusters summary file
        #### remove small clusters and summarize the rest 
        ndf_trim = ndf[ndf['Cluster_frac']>0]
        print(f"{(len(ndf)-len(ndf_trim))} records removed that were in clusters smaller than {0.1*(len(ndf))}")
        clusdf = ndf_trim.groupby(['Cluster_ID', 'Creative_Style']).size().reset_index() 
        clusdf.columns = ['Cluster_ID', 'Creative_Style', 'Cluster_Size']
        clusdf = clusdf.sort_values('Cluster_Size', ascending=False)
        print(clusdf)        
        clusdf.to_csv(clusname, index=False)
        
        # write network files
        write_network_file(ndf, edf, nwname)

    return ndf, edf    
    
  


################################################################

if __name__ == '__main__':
    # paths
    wd = pl.Path.cwd()
    datapath = wd/"data"
    outpath = wd/"results"
    figpath = wd/"figures"
    
 
    ### parameters for building network
    idf = False
    linksPer = 10
    tags = 'tags'
    tagattr = tags+"_list" # buildNetwork needs tags as a list
    blacklist = ['Emotionally Stable', 'Tortured Artist'] 
    
    # file names
    infile = datapath/"CreativeStyle_Responses_Tagged_Cleaned.xlsx"
   
    version = "2020_11_25"
    if blacklist == []:
        run_params = "allTags_" + str(linksPer) + "links_" + version #tag blasklisted, linksPer Node, date  
    else:
        run_params = "minus" + str(blacklist) + "_" + str(linksPer) + "links_" + version #tag blasklisted, linksPer Node  
    nw_name = outpath/("CreativeStyle_Network_" + run_params + ".xlsx")
    clusters_name = outpath/("Top_CreativeStyles_"  + run_params + ".csv")
    plot_name = figpath/("CreativeStyle_Network_" + run_params + ".pdf")
    
    
    print ('reading file')
    df = pd.read_excel(infile, engine='openpyxl')
    #df = df.head(100) # for testing
    df[tagattr] = df[tagattr].apply(literal_eval)# convert from string to list
    df.fillna('', inplace=True)
    
    
    ndf, edf = build_creative_style_network(df, tagattr,
                                write=True, nwname=nw_name, clusname=clusters_name, plotname=plot_name,
                                idf=idf, linksPer=linksPer, blacklist=blacklist,  
                                doLayout=True)
    
    
    
    
    
    


