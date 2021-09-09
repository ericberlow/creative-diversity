#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 21 08:54:57 2021

@author: ericberlow
"""


import pathlib as pl

# paths
wd = pl.Path.cwd()
datapath = wd/"data"
resultspath = wd/"results"
figpath = wd/"figures"
arch_playerpath = wd/"archetype_network_player"
habit_playerpath = wd/"habitat_network_player"
final_resultspath = wd/"results"/"submitted"

# network generation parameters
version = "2020_11_25"
all_linksPer = [6, 7, 8, 9, 10, 11, 12]  # list of link densities to run - > 10 links is final optimal one
final_linksPer = 10
tags = 'tags' # tag attribute for linking
tagattr = tags + "_list"  # buildNetwork needs tags as a list
blacklist = []  # excluded habits from original survey
maxtags = 10  # top tags to compare for cluster similarity
weighted = True # compare clusters using weighted tag distribution rather than top tags.


# filenames 
responses_raw_data = datapath/"CreativeStyle_Responses.csv"  # raw survey respones
responses_cleaned_processed = datapath/"CreativeStyle_Responses_Tagged_Cleaned.xlsx"  # cleaned file with tags
tagdistr_file = datapath/"tags_distribution.csv"  # tag distribution summary
discipline_map = datapath/"discipline_mapping.csv" # map detailed discipline tags to art, science, business
gender_map = datapath/"gender_mapping.csv"

# final run filenames
run_params = "minus" + str(blacklist) + "_" + str(final_linksPer) + "links_" + version
habit_network_params = "6links_2020_11_25"
creative_styles_network = resultspath/("CreativeStyle_Network_" + run_params + ".xlsx") # full network
archetype_network =  resultspath/("CreativeStyle_Network_Trimmed_10links_" + version +  ".xlsx") # archetype network
disciplines_by_cluster_sampled = resultspath/("Disciplines_byCluster_zScores_FullNetwork.csv") # sampled zScores of diciplines in each cluster
disciplines_by_cluster_permuted = resultspath/("Disciplines_byCluster_permuted_FullNetwork.csv") # permuted zScores of diciplines in each cluster
gender_by_cluster_permuted = resultspath/("Gender_byCluster_permuted_FullNetwork.csv") # permuted zScores of gender in each cluster
cluster_stats = resultspath/("CreativeStyles_ClusterStats_Wtd_"+ run_params + ".csv") # results of subsampling 100 networks
network_comparision = resultspath/("NetworkComparison.csv") # compare different linksPer settings
habits_network = resultspath/("Habits_Network_" + habit_network_params +".xlsx") # habits linked if they co-occur


# output files 
style_tag_summary_table = figpath/("CreativeStyles_Tag_Summary_"+ str(final_linksPer) +"links_" + version + ".xlsx") # top tags per cluster - full dataset
final_archetype_network =  final_resultspath/("CreativeStyle_Archetype_Network.xlsx") # archetype network final submitted
final_creative_styles_network = final_resultspath/("CreativeStyle_Network.xlsx") # full network final submitted
final_habits_network = final_resultspath/("Habits_Network.xlsx") # full network final submitted

## colors 
# also see vega color schemes here https://vega.github.io/vega/docs/schemes/ 
cluster_colors = ['#2aadbf','#f06b51', '#fbb44d', '#cd4747','#1a7480','#8c55aa', '#539280', '#bdbdbd',] # blue, orange, yellow, red, ocean green,  purple,light green, grey
cluster_colors_30 = ['#2aadbf','#f06b51', '#fbb44d', '#cd4747','#1a7480','#8c55aa', '#539280', # blue, orange, yellow, red, ocean green,  purple,light green,
                     '#bdbdbd', '#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd',
                     '#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd','#bdbdbd',
                     '#bdbdbd','#bdbdbd','#bdbdbd',] #grey


#rename columns with typo fixes and updated habit endpoints
ordCol_renameDict = {'Montasker -- Multitasker':  'Monotasker -- Multitasker',
                     'Distractible -- Focused': "Like Distractions -- Dislike Distractions", 
                     'Inwardly vs Outwardly Inspired': 'Inwardly -- Outwardly Inspired', 
                     'Internally vs Externally Motivated': 'Internally -- Externally Motivated',
                     'Controlled Chaos -- Organized': "Comforting Mess -- Tidy",
                     'Slow -- Fast Paced': "Slow-Paced -- Fast-Paced", 
                     'Risk Averse -- Risk Friendly': "Risk-Averse -- Risk-Friendly", 
                     'Stifled_By vs Stimulated_By Constraints': 'Stifled By -- Stimulated By Constraints',
                     'Private vs Public Workspace': "Private Spaces -- Public Spaces", 
                     'Work in Silence vs Noise/Music': "Silence -- Noise", 
                     'Urban -- Nature': "Nature-Agnostic -- Nature Lover", 
                     'Novetly Seeker -- Creature of Habit': "Novely-Seeker -- Routine-Seeker",
                     'Pragmastist -- Perfectionist': 'Pragmatist -- Perfectionist'
                    }

habit_renameDict = {'Distractible': 'Like Distractions',
                    'Focused': 'Dislike Distractions',
                    'Hate Distractions': 'Dislike Distractions',
                    'Controlled Chaos': 'Comforting Mess',
                    'Organized': 'Tidy',
                    'Slow Paced': 'Slow-Paced',
                    'Fast Paced': 'Fast-Paced',
                    'Risk Averse': 'Risk-Averse',
                    'Private': 'Private Spaces',
                    'Public': 'Public Spaces',
                    'Risk Friendly': 'Risk-Friendly',
                    "Silence": "Quiet/Silence", 
                    "Urban": "Nature-Agnostic" , 
                    "Nature": "Nature-Lover", 
                    "Novelty Seeker": "Novelty-Seeker", 
                    "Routine Seeker": "Routine-Seeker",
                    "Pragmastist": 'Pragmatist'
                    }

final_Network_renameDict = {'n_tags': 'n_Creative_Habits', 
                        'Cluster_frac': 'Cluster_Fraction',
                        'Creative_Style': 'Creative_Species'}

final_HabitNetwork_renameDict = {'Habit': 'Creative Habit', 
                        'Central_Habits': 'Most Central Habits',
                        'Cluster_frac': 'Cluster Fraction',
                        'Label': 'label'}

creative_species_dict = {'Creative Species 1': 'Mono Routinus',
                         'Creative Species 2': 'Yolo Chaotis',
                         'Creative Species 3': 'Socialis Adventurous',
                         'Creative Species 4': 'Focus Mononovous',
                         'Creative Species 5': 'Novo Gregarious',
                         'Creative Species 6': 'Sui Inspira',
                         'Creative Species 7': 'Solo Noctus',
    }

####################
## openmappr attribute render types 


# ARCHETYPE NETWORK

# s3 player bucket 
arch_s3_bucket = 'creative-styles-archetype-network'


habit_dimension_cols = ['Monotasker -- Multitasker', 'Specialist -- Generalist', 'Solo Creator -- Collaborator', 'Self-Critical -- Self-Assured', 
                'Like Distractions -- Dislike Distractions', 'Inwardly -- Outwardly Inspired', 'Rational -- Intuitive', 
                'Internally -- Externally Motivated', 'NonKinetic -- Kinetic', 'Comforting Mess -- Tidy', 'Slow-Paced -- Fast-Paced', 
                'Pragmatist -- Perfectionist', 'Risk-Averse -- Risk-Friendly', 'Make It Happen -- Let It Happen', 'Tenacious -- Reframer', 
                'Private Spaces -- Public Spaces', 'Silence -- Noise', 'Nature-Agnostic -- Nature Lover', 'Novely-Seeker -- Routine-Seeker', 
                'Stifled By -- Stimulated By Constraints'] 

other_final_cols = ['id','Creative Habits', 'Creative Species', 'Top Species Habits', 'Gender', 'Discipline', 'Cluster', 
                    'n_Creative_Habits', 'ClusterBridging', 'ClusterCentrality', 'Cluster_Fraction', 'x_tsne', 'y_tsne']

final_arch_cols = ['id', 'Creative Habits', 'Creative Species', 'Top Species Habits', 
                   'Gender', 'Discipline', 'Cluster', 
                   'n_Creative_Habits', 'ClusterBridging', 'ClusterCentrality', 'Cluster_Fraction', 
                   'x_tsne', 'y_tsne', 'label']

# list  attributes to hide from filters
arch_hide_add = ['x_tsne', 'y_tsne', 'Cluster_Fraction'] + habit_dimension_cols

# list  attributes to hide from right profile
arch_hideProfile_add =['id', 'ClusterBridging', 'ClusterCentrality'] 
                    
# list attributes to hide from search
arch_hideSearch_add = ['id', 'Gender', 'Discipline', 'Cluster'] 

# list attributes to render as different string types
arch_liststring_add = []  
arch_tags_add = []
arch_wide_tags_add = [ 'Gender', 'Discipline', 'Cluster', 'Creative Species']
arch_text_str_add = []
arch_email_str_add = []


# HABITS NETWORK

# s3 player bucket 
habit_s3_bucket = 'creative-habits-network'

habit_final_cols = ['id', 'Creative Habit', 'Most Central Habits', 'Frequency', 'Percent', 
                 'Cluster_size', 'Degree', 'ClusterCentrality', 'ClusterBridging', 'Cluster_ID', 'label', 'x_tsne', 'y_tsne']

# list  attributes to hide from filters
habit_hide_add = ['x_tsne', 'y_tsne', 'Cluster_Fraction'] + habit_dimension_cols

# list  attributes to hide from right profile
habit_hideProfile_add =['label', 'ClusterBridging', 'ClusterCentrality', 'Cluster_size', 'Degree'] 
                    
# list attributes to hide from search
habit_hideSearch_add = ['label', 'id'] 

# list attributes to render as different string types
habit_liststring_add = []  
habit_tags_add = []
habit_wide_tags_add = ['Most Central Habits', 'Discipline']
habit_text_str_add = []
habit_email_str_add = []