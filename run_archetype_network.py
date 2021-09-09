####################################

import pandas as pd
from build_decorate_network import write_network_file, tsne_layout, plot_network
import pathlib as pl
           
pd.set_option('display.expand_frame_repr', False) # expand display of data columns if screen is wide



def trim_network (ndf, ldf, byCol = 'ClusterCentrality', thresh= 0, plotName = "network_trimmed_tsne.pdf"):
    ## remove nodes that are in small clusters
    toKeep = ((ndf['Creative_Style'] != 'Misc. Small Clusters') & (ndf[byCol] >= thresh))
    ndf_trimmed = ndf[toKeep]
    
    ## get list of node id's that were removed
    nodes_removed = ndf[~toKeep]['id'].unique().tolist()
    
    ## remove links that those nodes are in
    source_remove = ldf['Source'].apply(lambda x: x in nodes_removed)
    target_remove = ldf['Target'].apply(lambda x: x in nodes_removed)
    link_remove = source_remove | target_remove # True if remove the link
    
    ldf_trimmed = ldf[~link_remove]
    
    ## remove nodes that are now isolated with no links
    nodes_w_links = set(ldf_trimmed['Source'].unique().tolist() + ldf_trimmed['Target'].unique().tolist())
    keep_nodes = ndf_trimmed['id'].apply(lambda x: x in nodes_w_links)
    ndf_trimmed = ndf_trimmed[keep_nodes].reset_index(drop=True)
    
    ## add tsne layout and plot
    ndf_trimmed = tsne_layout(ndf_trimmed, ldf_trimmed)
    node_sizes = ndf_trimmed.loc[:,'ClusterCentrality']*10
    node_sizes_array = node_sizes.values # convert clustercentrality to array for sizing
    plot_network(ndf_trimmed, ldf_trimmed, plotName, x='x_tsne', y='y_tsne', node_size=node_sizes_array)
    
    return ndf_trimmed, ldf_trimmed

if __name__ == '__main__':
    
    # ####### paths
    wd = pl.Path.cwd()
    datapath = wd/"data"
    resultspath = wd/"results"
    figpath = wd/"figures"
    
    
    # parameters
    linksPer = 10
    tags = 'tags'
    blacklist = ['Emotionally Stable', 'Tortured Artist']  # ["Early Bird", "Night Owl", "Tortured Artist"]
    version = "2020_11_25"
    
    # filename params
    run_params = "minus" + str(blacklist) + "_" + str(linksPer) + "links_" + version #tag blasklisted, linksPer Node, date  
    
    # filenames
    creative_styles_network = resultspath/("CreativeStyle_Network_" + run_params + ".xlsx")
    creative_styles_network_trimmed =  resultspath/("CreativeStyle_Network_Trimmed_" + str(linksPer) +"links_" + version + ".xlsx")
    network_plot_name = str(figpath/"creative_styles_network_trimmed_tsne.pdf")
    
    
    print('read files')
    ndf = pd.read_excel(creative_styles_network, sheet_name='nodes', engine='openpyxl')
    ldf = pd.read_excel(creative_styles_network, sheet_name='links', engine='openpyxl')
    
    
    ndf_trimmed, ldf_trimmed = trim_network (ndf, ldf, byCol = 'ClusterCentrality', thresh= 0, plotName = network_plot_name)
    
    ## write trimmed network
    #ndf_trimmed.drop(['Cluster'], axis=1, inplace=True)
    write_network_file(ndf_trimmed, ldf_trimmed, creative_styles_network_trimmed)