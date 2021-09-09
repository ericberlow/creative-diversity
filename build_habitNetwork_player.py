#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 10:03:11 2021

@author: ericberlow
"""


import sys
import pandas as pd
#sys.path.append("../../../Github/Tag2Network/tag2network/")  # add Tag2Network directory
sys.path.append("../../../Github/py2mappr/src")  # add Tag2Network directory
#sys.path.append("../CommonFunctions") # build network and layout functiont
from build_openmappr_files import write_openmappr_files
from map_utils import create_map, create_snapshot

import params

import boto3
import os
import configparser
import pathlib as pl
import http.server
import socketserver
import webbrowser

### Config Setup ###
config = configparser.ConfigParser()
wd = pl.Path.cwd() 
configpath = wd/'config.ini'
config.read(configpath)
# load AWS settings from config file
REGION = config['aws']['region']
ACCESS_KEY = config['aws']['access_key_id']
SECRET_KEY = config['aws']['secret_access_key']


# launch local server and open browser to display map
def run_local(project_directory, PORT=5000):
    """
    launches a new tab in active browswer with the map
    project_directory : string, the directory with the project data (index.html and 'data' folder)
    """
    web_dir = os.path.join(os.getcwd(), project_directory)
    os.chdir(web_dir)  # change to project directory where index.html and data folder are

    webbrowser.open_new_tab("http://localhost:" + str(PORT))  # open new tab in browswer

    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("\nServing locally at port", PORT, "go to http://localhost:%s \nCTL_C to quit\n" % str(PORT))
        httpd.serve_forever()

def upload_to_s3(path, bucket_name):
    print("\nUploading map to AWS S3 Bucket, named %s, as static website"%bucket_name)
    S3_CLIENT = boto3.client(
                            's3',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY,
                            region_name=REGION
                            )   
    # create public bucket if it doesn't exist
    S3_CLIENT.create_bucket(Bucket=bucket_name, ACL='public-read')

    # Create the configuration for the website
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
    }
    # Set the new policy on the selected bucket
    S3_CLIENT.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration=website_configuration
    )

    session = boto3.Session(
        aws_access_key_id= ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name= REGION
    )
    s3 = session.resource('s3')
    bucket = s3.Bucket(bucket_name)
 
    for subdir, dirs, files in os.walk(path):
        for file in files:
            full_path = os.path.join(subdir, file)
            with open(full_path, 'rb') as data:
                bucket.put_object(Key=full_path[len(path)+1:], Body=data,
                                  ACL='public-read', ContentType=  "text/html")
                
    print("\nView map at http://%s.s3-website-us-east-1.amazonaws.com/"%bucket_name)
    
#######################################################################    
########### PLAYER SNAPSHOTS AND SETTINGS #############################    

def build_run_player(ndf,ldf, 
                    hide_add,  # list custom attributes to hide from filters
                    hideProfile_add, # list custom attributes to hide from right profile
                    hideSearch_add, # list custom attribs to hide from search
                    liststring_add, # string attribs to force as liststring
                    tags_add,  # custom string attribs to render as tag-cloud
                    wide_tags_add, # custom string attribs to render as wide tag-cloud
                    text_str_add ,   # custom string attribs to render as long text in profile
                    email_str_add,  # custom string attribs to render as email link  in profile)
                    playerpath, # path for player files
                    player_s3_bucket, # name of s3 bucket
                    launch_local=True, 
                    upload_s3=True):
    '''
    Build player from nodes and links dataframes
    First generate openmappr player files - including attribute type render settings
    Then build player - snapshot settings and global settings
    Then launch in browser locally and/or upload to s3 static website
    '''
    
    #ndf = ndf[finalNodeAttrs] # clean columns
    
    # configure the files and folders
    # create player directories if they don't exist
    inDataPath = playerpath / "data_in"
    outFolder = playerpath / "data_out"
    
    playerpath.mkdir(exist_ok=True) # create directory if it doesn't exist
    inDataPath.mkdir(exist_ok=True) # create directory if it doesn't exist
    outFolder.mkdir(exist_ok=True) # create directory if it doesn't exist
    
    nodesFile = inDataPath / "nodes.csv"
    linksFile = inDataPath / "links.csv"
    nodeAttrsFile = inDataPath / "node_attrs.csv"
    
    
    # Write openMappr files
    write_openmappr_files(ndf, ldf, playerpath/"data_in", labelCol='label', 
                    hide_add = hide_add,  # list custom attributes to hide from filters
                    hideProfile_add = hideProfile_add, # list custom attributes to hide from right profile
                    hideSearch_add = hideSearch_add, # list custom attribs to hide from search
                    liststring_add = liststring_add, # string attribs to force as liststring
                    tags_add = tags_add,  # custom string attribs to render as tag-cloud
                    wide_tags_add = wide_tags_add  , # custom string attribs to render as wide tag-cloud
                    text_str_add = text_str_add,   # custom string attribs to render as long text in profile
                    email_str_add = email_str_add # custom string attribs to render as email link  in profile
                    )
    
     
    
    # configure the mapping for the read parameters
    # maps are in the form of {"required param name": "name of column in datasheet"}
    # the required param names are fixed and should not be changed.
    node_attr_map = {"OriginalLabel": "label", "OriginalX": "x_tsne", "OriginalY": "y_tsne"}
    link_attr_map = {"source": "Source", "target": "Target", "isDirectional": "isDirectional"}
    
    # create some snapshots
    # snapshot - scatterplot
    
    sn1 = create_snapshot(
        name="Creative Habit Clusters",
        subtitle="Clusters of habits that tend to co-occur",
        summaryImg="https://www.dl.dropboxusercontent.com/s/1jdc4hvp5zw6as9/Screen%20Shot%202021-03-31%20at%206.59.23%20AM.png?dl=0",
        description="<p>This is a network of the Creative Habits - creative preferences or tendencies - linked if they tend to co-occur in similar sets of people. \
                            The colored clusters are emergent groups of Creative Habits that tend to co-occur  with one another more than expected by chance. \
                            Hovering on a habit displays the other habits that it co-occurs with the most. \
                            Thicker links between habits indicate stronger overlap in the people they share. \
                            The clusters are labeled by the most 'Central', or 'Archetypal' Creative Habits of the cluster - which are defined as \
                            Habits with many links (i.e. strong co-associations) to others in the same cluster. \
                            The spatial layout of nodes and clusters was determined with t-SNE so that nodes and clusters which are more tightly interlinked \
                            tend to be closer to one another in space. \
                            Habits with few weak (thin) links tend to be more randomly distributed across people \
                            than Habits with more or thicker links.  \
                            The Creative Habits tend to sort horizontally into more 'deliberate' creative style preferences on the left and \
                            more 'open' creative style preferences on the right.</p>\
                <p>If you hover over individual Creative Habit tags in the <b>Filters</b> panel, you can see broader themes in creative preferences, \
                    for example, people on the left tend to have a more 'deliberate' creative style, while those to the right \
                    tend to have a more 'open' creative style. \
                If you <i>Apply</i> any selection, the <b>Filters</b> panel will summarize the top creative habits for the selected group. \
                </p>\
                <p><b>Node Color: </b>Creative Habit Cluster</p><p>\
                <b>Node Size:</b>  Cluster Archetype: Larger habits were are more central, or archetypal of the cluster</p>",
        layout_params={
            "plotType": "scatterplot", #"original", 
            "xaxis": 'x_tsne',  # not needed for 'original' network layout
            "yaxis": 'y_tsne',   # not needed for 'original' network layout
            
            "settings": {
                # scatterplot layout settings 
                "xAxShow": False, # not needed for 'original' (network) or geo layout
                "yAxShow": False, # not needed for 'original' (network) or geo layout
                "invertX": False, # not needed for 'original' (network) or geo layout
                "invertY": False, # not needed for 'original' (network) or geo layout
                "scatterAspect": 0.6,  # shigher than 0.5 spreads out the scatterplot horizontally
                # Geo layout setting
                "isGeo": False,  # True if geographic layout 

                # node size
                "nodeSizeAttr": "ClusterCentrality",
                "nodeSizeScaleStrategy": "linear",  # "linear" or "log"
                "nodeSizeMin": 4,
                "nodeSizeMax": 20,
                "nodeSizeMultiplier": 0.8,
                "bigOnTop": False,

                # node color and images
                "nodeColorAttr": "Most Central Habits", 
                "nodeColorPaletteOrdinal": [
                    {"col": "#2aadbf"},
                    {"col": "#f06b51"},
                    {"col": "#fbb44d"},
                    {"col": "#cd4747"},
                    {"col": "#1a7480"},
                    {"col": "#8c55aa"},
                    {"col": "#539280"},
                    {"col": "#bdbdbd"},
                ],
                "nodeImageShow": False,
                #"nodeImageAttr": "Photo",

                # link rendering
                "drawEdges": True,
                "edgeCurvature": 0,
                "edgeDirectionalRender": "outgoing",  # "outgoing", "incoming", "all"
                "edgeSizeStrat": "attr",  #  "attr" // "fixed"
                "edgeSizeAttr": "weight",  # size by
                "edgeColorStrat": "gradient",  # source / target / gradient / attr / select
                "edgeColorAttr": "OriginalColor",
                "edgeSizeMultiplier": 0.8,
                # neighbor rendering
                "nodeSelectionDegree": 1,

                # labels
                "drawGroupLabels": False,
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
        snapshots= [sn1],
        playerSettings={
            "startPage": "filter",  # filter // snapshots // list // legend // splash?
            "headerTitle": "Creative Habits Network",
            "modalTitle": "Creative Habits Network",
            "headerImageUrl": "",
            "modalSubtitle": "<p>This is a network of Creative Habits - or creative preferences and tendencies - from a survey of ~10,000 people. \
                            Each node is a 'Habit', and they are linked to other Habits with the most overlap in people that have them. \
                            The clusters of habits show broad themes in combinations of Creative Habits that tend to go together. \
                            </p>\
                            <p>NOTE - This visualization is designed for desktop viewing and has not been optimized for mobile. \
                            It works best in Chrome or Safari. </p>",
            "modalDescription": "<h3>How to Navigate this Network:</h3><ul>\
                            <li>Click on any node to to see more details about it. </li>\
                            <li>Click the '<b>Reset</b>' button to clear any selection.</li>\
                            <li>Use the <b>Filters</b> panel to select nodes by any combination of attributes. </li>\
                            <li>Click the <b>'Apply'</b> button to subset the data to the selected nodes - \
                            The <b>Filters</b> panel will then show a summary of that selection.<br/></li>\
                            <li>Use the <b>List</b> panel to see a sortable list of any nodes selected. \
                            You can also browse their details in the list by clicking on them.</li>\
                            <li>Use the Snapshots panel to see a description of the current view.</li></ul>\
                            <p><br/></p><p>\
                            This visualization is not optimized for mobile devices and is best viewed in Chrome or Safari browsers\ \
                            on the laptop/desktop. </p>&#10;",
        },
        outFolder=outFolder,
    )
    
    if upload_s3:
        upload_to_s3(str(outFolder), player_s3_bucket)

    if launch_local:
        run_local(str(outFolder), PORT=5000)



########################################################################
if __name__ == '__main__':
    
    #  build habits network 
    # read file
    ndf = pd.read_excel(params.final_habits_network, engine='openpyxl', sheet_name='nodes') # recipients with metadata including tags
    ldf = pd.read_excel(params.final_habits_network, engine='openpyxl', sheet_name='links') # recipients with metadata including tags
    

    build_run_player(ndf,ldf, 
                    params.habit_hide_add,  # list custom attributes to hide from filters
                    params.habit_hideProfile_add, # list custom attributes to hide from right profile
                    params.habit_hideSearch_add, # list custom attribs to hide from search
                    params.habit_liststring_add, # string attribs to force as liststring
                    params.habit_tags_add,  # custom string attribs to render as tag-cloud
                    params.habit_wide_tags_add, # custom string attribs to render as wide tag-cloud
                    params.habit_text_str_add,   # custom string attribs to render as long text in profile
                    params.habit_email_str_add, # custom string attribs to render as email link  in profile
                    params.habit_playerpath, # directory to hold player data
                    params.habit_s3_bucket,
                    launch_local=True, 
                    upload_s3=False)


