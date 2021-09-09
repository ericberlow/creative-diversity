#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 10:03:11 2021

@author: ericberlow
"""


import sys
sys.path.append("../../../Github/Tag2Network/tag2network/")  # add Tag2Network directory
sys.path.append("../../../Github/py2mappr/src")  # add Tag2Network directory
sys.path.append("../CommonFunctions") # add auto Tagging directory
import pandas as pd
import reference as ref 
import common_network_functions as net  # build network, layouts, plot network functions
from map_utils import create_map, create_snapshot

import launch_upload_player



def build_run_player(ndf,ldf, launch_local=True, upload_s3=True):
    '''
    Build player from nodes and links dataframes
    First generate openmappr player files - including attribute type render settings
    Then build player - snapshot settings and global settings
    Then launch in browser locally and/or upload to s3 static website
    '''
    
    ndf = ndf[ref.finalNodeAttrs] # clean columns
    
    # Write openMappr files
    net.write_openmappr_files(ndf, ldf, ref.playerpath/"data_in", labelCol='label', 
                    hide_add = ref.hide_add,  # list custom attributes to hide from filters
                    hideProfile_add =ref.hideProfile_add, # list custom attributes to hide from right profile
                    hideSearch_add = ref.hideSearch_add, # list custom attribs to hide from search
                    liststring_add = ref.liststring_add, # string attribs to force as liststring
                    tags_add = ref.tags_add,  # custom string attribs to render as tag-cloud
                    wide_tags_add = ref.wide_tags_add  , # custom string attribs to render as wide tag-cloud
                    text_str_add = ref.text_str_add,   # custom string attribs to render as long text in profile
                    email_str_add = ref.email_str_add # custom string attribs to render as email link  in profile
                    )
    
    # configure the files and folders
    
    inDataPath = ref.playerpath / "data_in"
    nodesFile = inDataPath / "nodes.csv"
    linksFile = inDataPath / "links.csv"
    nodeAttrsFile = inDataPath / "node_attrs.csv"
    outFolder = ref.playerpath / "data_out"
    
    
    # configure the mapping for the read parameters
    # maps are in the form of {"required param name": "name of column in datasheet"}
    # the required param names are fixed and should not be changed.
    node_attr_map = {"OriginalLabel": "label", "OriginalX": "x_tsne", "OriginalY": "y_tsne"}
    link_attr_map = {"source": "Source", "target": "Target", "isDirectional": "isDirectional"}
    
    # create some snapshots
    # snapshot - scatterplot
    
    sn1 = create_snapshot(
        name="Keyword Themes",
        subtitle="People clustered into systems themes",
        summaryImg="https://www.dl.dropboxusercontent.com/s/1jdc4hvp5zw6as9/Screen%20Shot%202021-03-31%20at%206.59.23%20AM.png?dl=0",
        description="<p><span>This is an 'affinity network' of Summit Impacr community members linked if they share similar \
                keywords. \
                If you hover over any person, the links show the other peole with the most overalp in keywords. \
                The tags were assigned by searching through the full text of their LinkedIn prifiles for mentions of terms from a custom \
                keyword dictionary of professional and social impact terms. \
                </span><br/></p><p>The colored clusters are groups of people that tend to co-share similar keyword sets. \
                The clusters, or 'Keyword Themes' are auto-labeled by the three most commonly shared tags in the cluster. \
                Since each person has many keywords describing what they do, they don't always fit neatly in one box. \
                Use the <b>Filters</b> panel to browse and select people by any combination of keywords or other tags. \
                If you <i>Apply</i> that selection, the <b>Filters</b> panel will summarize the tags for the selected group. \
                </p><p>\
                <b>Node Color: </b>Keyword Theme</p><p>\
                <b>Node Size:</b>  Keyword Theme Centralityt: Larger nodes are more representative or archetypal of the cluster</p>",
        layout_params={
            "plotType": "original",  # "scatterplot",
            # "xaxis":  not needed for 'original' network layout
            # "yaxis": not needed for 'original' network layout
            "settings": {
                # node size
                "nodeSizeAttr": "ClusterCentrality",
                "nodeSizeScaleStrategy": "linear",  # "linear" or "log"
                "nodeSizeMin": 4,
                "nodeSizeMax": 20,
                "nodeSizeMultiplier": 0.8,
                "bigOnTop": False,
                # node color and images
                "nodeColorAttr": "Keyword Theme", 
                "nodeColorPaletteOrdinal": [
                    {"col": "#1F4B8E"},
                    {"col": "#DE432F"},
                    {"col": "#7BA1DB"},
                    {"col": "#B4E026"},
                    {"col": "#7E8F49"},
                    {"col": "#2A768F"},
                    {"col": "#DE2F5C"},
                    {"col": "#7BC3DB"},
                ],
                "nodeImageShow": True,
                "nodeImageAttr": "Photo",
                # link rendering
                "drawEdges": True,
                "edgeCurvature": 0,
                "edgeDirectionalRender": "outgoing",  # "outgoing", "incoming", "all"
                "edgeSizeStrat": "fixed",  #  "attr" // "fixed"
                "edgeSizeAttr": "weight",  # size by
                "edgeColorStrat": "gradient",  # source / target / gradient / attr / select
                "edgeColorAttr": "OriginalColor",
                "edgeSizeMultiplier": 0.6,
                # neighbor rendering
                "nodeSelectionDegree": 1,
                # labels
                "drawGroupLabels": True,
                # layout rendering
                # "xAxShow": False, # not needed for 'original' (network) layout
                # "yAxShow": False, # not needed for 'original' (network) layout
                # "invertX": False, # not needed for 'original' (network) layout
                # "invertY": False, # not needed for 'original' (network) layout
                # "scatterAspect": 0.3,  # shigher than 0.5 spreads out the scatterplot horizontally
            },
        },
    )
    
    # snapshot - scatterplot
    sn2 = create_snapshot(
        name="Geographic Map",
        subtitle="Where people are based",
        summaryImg="https://www.dl.dropboxusercontent.com/s/lfa3a2w44k0t2kw/Screen%20Shot%202021-03-31%20at%207.01.37%20AM.png?dl=0",
        description="<p>This is a geographic view of Summit Impact community members, using data from LinkedIn on where they are currently based. \
                    In the <b>Filters</b> panel you can also filter peole by 'Geo' tags, which include any geographic places mentioned \
                    in the full text of their LinkedIn Profile. \
                    If you hover over a person, it will show links to their most similar 'neighbors'. \
                    You can select a group of peole on the map by holding 'shift' while you drag the cursor. \
                    In the <b>Filters</b> panel, if you hover over a keyword or tag you can see it's geographic dispersion. \
                    </p><p>\
                    <b>Node Color: </b><span>Country</span><br/></p><p>\
                    <b>Node Size:</b> System Theme Centrality: Larger nodes are more archetypal of their theme</p>",
        layout_params={
            "plotType": "geo",
            "xaxis": "Latitude",
            "yaxis": "Longitude",
            "camera": {"normalizeCoords": True, "x": 0, "y": 43.9873417721519, "r": 1.5},
            "settings": {
                # node sizing
                "nodeSizeAttr": "ClusterCentrality",
                "nodeSizeScaleStrategy": "linear",  # "linear" or "log"
                "nodeSizeMin": 4,
                "nodeSizeMax": 15,
                "nodeSizeMultiplier": 1,
                # node color and images
                "nodeColorAttr": "Country (based)",
                "nodeColorPaletteOrdinal": [
                    {"col": "#1F4B8E"},
                    {"col": "#DE432F"},
                    {"col": "#7BA1DB"},
                    {"col": "#B4E026"},
                    {"col": "#7E8F49"},
                    {"col": "#2A768F"},
                    {"col": "#DE2F5C"},
                    {"col": "#7BC3DB"},
                ],
                "nodeImageShow": True,
                "nodeImageAttr": "Photo",
                # link rendering
                "drawEdges": False,
                "edgeCurvature": 0.6,
                "edgeDirectionalRender": "outgoing",
                "edgeSizeStrat": "fixed",  # or "attr"
                "edgeSizeAttr": "weight",  # size by similarity
                "edgeSizeMultiplier": 0.8,
                "edgeColorStrat": "gradient",  # source / target / gradient / attr / select
                "edgeColorAttr": "OriginalColor",
                # neighbor rendering
                "nodeSelectionDegree": 1,
                # labels
                "drawGroupLabels": False,  # cluster labels
                # layout rendering
                #"xAxShow": False,  not needed for geo layout
                #"yAxShow": False,  not needed for geo layout
                #"invertX": False,  not needed for geo layout
                #"invertY": True,  not needed for geo layout
                #"scatterAspect": 0.5,  # shigher than 0.5 spreads out the scatterplot horizontally
                "isGeo": True,  # geographic layout
                # node right panel
                "nodeFocusShow": True,
            },
        },
    )
    
    
    # create map
    create_map(
        nodesFile,
        linksFile,
        nodeAttrsFile,
        node_attr_map,
        link_attr_map,
        snapshots= [sn2,sn1],
        playerSettings={
            "startPage": "filter",  # filter // snapshots // list // legend // splash?
            "headerTitle": "Summit Impact Community",
            "modalTitle": "Summit Impact",
            "headerImageUrl": "",
            "modalSubtitle": "<p>This is a demonstration of visualizing a community of people using information scraped from their public LinkedIn profiles. \
                        People where then tagged with keywords from a curated corpus of terms \
                        by searching the full text of their profiles for mentions of those terms. \
                        Similarly, people were tagged with where in the world they work or have worked by searching through \
                        their Profiles for any mentions of geographic place names. \
                        The geographic location for where each person is based was derived from  the city and/or country \
                        mentioned in their LinkedIn title. These were then geo-coded using the Google Maps API to derive latitude and longitude for mapping. \
                        Note that for some people - the geography in their LinkedIn title is very broad (e.g. 'United States'), so their location on the map \
                        will be similarly coarse. </p>\
                            <p>NOTE - This visualization is designed for desktop viewing and has not been optimized for mobile. \
                            It works best in Chrome or Safari. </p>",
            "modalDescription": "<h3>How to Navigate this Network:</h3><ul>\
                            <li>Click on any node to to see more details about it. </li>\
                            <li>Click the '<b>Reset</b>' button to clear any selection.</li>\
                            <li>Use the <b>Filters</b> panel to select nodes by any  combination of attributes. </li>\
                            <li>Click the <b>'Apply'</b> button to subset the data to \
                            the selected nodes - The <b>Filters</b> panel will then show a summary of that selection.<br/></li>\
                            <li>Use the <b>List</b> panel to see a sortable list of any nodes selected. \
                            You can also browse their details in the list by clicking on them.</li>\
                            <li>Use the Snapshots panel to navigate between views.</li></ul><p><br/></p><p>\
                            This visualization is not optimized for mobile devices and is best viewed in Chrome or Safari browsers\ \
                            on the laptop/desktop. </p>&#10;",
        },
        outFolder=outFolder,
    )
    
    if upload_s3:
        launch_upload_player.upload_to_s3(str(outFolder), ref.player_s3_bucket)

    if launch_local:
        launch_upload_player.run_local(str(outFolder), PORT=5000)


############################
if __name__ == '__main__':
    #  read nodes file
    ndf = pd.read_excel(ref.nw_name, engine='openpyxl', sheet_name='Nodes') # recipients with metadata including tags
    ldf = pd.read_excel(ref.nw_name, engine='openpyxl', sheet_name='Links') # recipients with metadata including tags

    build_run_player(ndf,ldf, launch_local=True, upload_s3=True)


