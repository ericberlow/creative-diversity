# -*- coding: utf-8 -*-

import pandas as pd
import pathlib as pl 
from collections import Counter, OrderedDict
import numpy as np
import params


def build_taglists(df):
    df['tagList']= df['tags'].str.split('|').apply(lambda x: [ss.strip() for ss in x])
    df['allTagList'] = df['allTags'].str.split('|').apply(lambda x: [ss.strip() for ss in x])

def buildTagHistDf (df, col, blacklist=[], mincnt=0):
    # generate dictionary of tags and tag counts for a column, exclude rows with no data
    # trim each dataset to tags with more than 10 ppl
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

def clean_biorhythm(x):
    # convert biorhythm tags into just "Early Bird" vs "Hight Owl" extremes
    taglist = str(x).split('|')
    taglist = [tag.strip(' ') for tag in taglist] # strip empty spaces for each item in each list
    bio_tags = [] # initialize new list of tags
    for tag in taglist:
        if tag in ["Pre Dawn", "Morning"]:
            bio_tags.append("Early Bird")
        if tag in ["Evening", "After Midnight"]:
            bio_tags.append("Night Owl")
    bio_tags = list(set(bio_tags)) # remove dupes
    n_tags = len(bio_tags)
    if n_tags == 2:
        bio_tags = [] # assume that if they list all, then no strong biorhythm
    return  "|".join(bio_tags) 

def make_tags_from_ordinal(df):
    # convert ordinal responses into tags
    # for each quesiton - look at the distribution. 
    # if it peaks in the middle (3), then tags are syummetrical (1 or 2 = low,  and 4 or 5 = high)
    # if it is skewed- then the tags are asymmetrical (e.g. 1 = low and 4 or 5 = high, or vice versa)

     
    # map column headers to (low,high) value pairs
    tagDict = {"Multitasking (Montasker -- Multitasker)": ("Monotasker", "Multitasker"),
               "Breadth (Specialist -- Generalist)": ("Specialist", "Generalist"),
               "Collaboration (Solo Creator -- Collaborator)": ("Solo Creator", "Collaborator"),
               "Confidence (Self-Critical -- Self-Assured)": ("Self-Critical", "Self-Assured"),
               "Focus (Distractible -- Focused)": ("Love Distractions", "Hate Distractions"),
               "Inspriation Source (Inward -- Outward)": ("Inwardly Inspired", "Outwardly Inspired"),
               "Creative Reasoning (Rational -- Intuitive)": ("Rational", "Intuitive"),
               "Motivation (Internal -- External)": ("Internally Motivated", "Externally Motivated"),
               "Movement (NonKinetic -- Kinetic)": ("NonKinetic", "Kinetic"),
               "Organization (Controlled Chaos -- Organized)": ("Comforting Mess", "Tidy Workspace"),
               "Pace (Slow -- Fast)": ("Slow Paced", "Fast Paced"),
               "Perfectionism (Pragmastist -- Perfectionist)": ("Pragmastist", "Perfectionist"),
               "Risk (Risk Averse -- Risk Loving)": ("Risk Averse", "Risk Friendly"),
               "Stategy (Make It Happen -- Let It Happen)": ("Make It Happen", "Let It Unfold"),
               "Tactic (Tenacious -- Reframer)": ("Tenacious", "Reframer"),
               "Workspace (Private -- Public)": ("Private Space", "Public Space"),
               "Noise (Silence -- Noise/Music)": ("Quiet/Silence", "Noise/Music"),
               "Nature (Urban -- Nature)": ("Non-Nature", "Nature"),
               "Ritual (Novetly Seeker -- Creature of Habit)": ("Novelty Seeker", "Routine Seeker"),
               "Constraints (Stifle By -- Stimulated By)": ("Stifled By Constraints", "Stimulated By Constraints")}


    # define places to put the results - a list (of tags), one for each row in the dataset
    allTagStrings = []  # includes tags from ordinal responses and biorhythm tag attribte

    
    for i in df.index:  # loop over rows in the dataframe
        if i %100 == 0: # print row number every 100 rows to show progress
            print("Processing row %d"%i)
        currTag = ""    # build tags for current row here
        row = df.loc[i] # get the row data
    
        # loop over all row headers that are (low,high) values
        for hd in tagDict:
            val = row[hd]
            tg = None
            if df[hd].median() == 3:
                if val == 1 or val == 2:
                    tg = tagDict[hd][0]
                elif val == 5 or val == 4:
                    tg = tagDict[hd][1]
                if tg != None:
                    if len(currTag) == 0:
                        currTag = tg
                    else:
                        currTag = currTag + '|' + tg    
            elif df[hd].median() > 3:
                if val == 1 or val == 2:
                    tg = tagDict[hd][0]
                elif val == 5:
                    tg = tagDict[hd][1]
                if tg != None:
                    if len(currTag) == 0:
                        currTag = tg
                    else:
                        currTag = currTag + '|' + tg    
            elif df[hd].median() < 3:
                if val == 1:
                    tg = tagDict[hd][0]
                elif val == 5 or val == 4:
                    tg = tagDict[hd][1]
                if tg != None:
                    if len(currTag) == 0:
                        currTag = tg
                    else:
                        currTag = currTag + '|' + tg    

        # add the current row's tags to the lists
        #tagStrings.append(currTag)
        
        # add biorhythm tag to the current list
        allTags = currTag
        val = row["Biorhythm"]
        if isinstance(val, str) and len(val) > 0:    # make sure it's not empty
            allTags = allTags + '|' + val
            
        allTagStrings.append(allTags)

    return allTagStrings # list of pipe-separated strings
   

def clean_HC_data(infile, outfile, tagsfile):
    
    df = pd.csv(infile)

    ####################################
    # clean columns and define column types
    
    dropCols = ['email','name','Profile Picture','Date Started','Date Completed', 'Date Completed Timestamp',
            'Percent Survey Complete', 'Percent Profile Complete','Referred By', 'Email Opt In',
           'Last Profile Edit','Twitter', 'Instagram', 'Allow Profile to be Shown', 'Media', 'Video']
    df.drop(columns= dropCols, inplace=True)

    # convert biorhythm to 2 tags (early vs late)
    df['Biorhythm'] = df['Creative Biorhythm'].apply(lambda x: clean_biorhythm(x))


    #######convert ordinal answers to tags
    df['tags'] =  make_tags_from_ordinal(df) 

    ###### remove users that answered less than 90%
    # remove users with no tags

    surveyCols = ['Multitasking (Montasker -- Multitasker)',
     'Breadth (Specialist -- Generalist)',
     'Collaboration (Solo Creator -- Collaborator)',
     'Confidence (Self-Critical -- Self-Assured)',
     'Focus (Distractible -- Focused)',
     'Inspriation Source (Inward -- Outward)',
     'Creative Reasoning (Rational -- Intuitive)',
     'Motivation (Internal -- External)',
     'Movement (NonKinetic -- Kinetic)',
     'Organization (Controlled Chaos -- Organized)',
     'Pace (Slow -- Fast)',
     'Perfectionism (Pragmastist -- Perfectionist)',
     'Risk (Risk Averse -- Risk Loving)',
     'Stategy (Make It Happen -- Let It Happen)',
     'Tactic (Tenacious -- Reframer)',
     'Workspace (Private -- Public)',
     'Noise (Silence -- Noise/Music)',
     'Nature (Urban -- Nature)',
     'Ritual (Novetly Seeker -- Creature of Habit)',
     'Constraints (Stifle By -- Stimulated By)',
     'Creative Biorhythm',
     ]
    
    df['fracAnswered'] = (len(surveyCols) - df[surveyCols].isnull().sum(axis=1))/len(surveyCols) #summarize by row across questions
    
    initial = len(df)
    df = df[df['fracAnswered']>.9]
    trim_df = df[df['tags'] != '']
    trim_df = trim_df.reset_index(drop=True) # reset index
    final = len(trim_df)
    fracKept = float(final)/float(initial)
    print ("%d respondents with >90pct completion (%.2f of %d total respondents)"%(final, fracKept, initial))

    ########### # Clean and re-order columns
    
    keepList = ['id','tags', 'Biorhythm',
     'Gender','Age', 'Discipline', 
     'City','Company', 'Department',
     'Creative Advice', #'What Does Creativity Mean to You?',
     'Multitasking (Montasker -- Multitasker)',
     'Breadth (Specialist -- Generalist)',
     'Collaboration (Solo Creator -- Collaborator)',
     'Confidence (Self-Critical -- Self-Assured)',
     'Focus (Distractible -- Focused)',
     'Inspriation Source (Inward -- Outward)',
     'Creative Reasoning (Rational -- Intuitive)',
     'Motivation (Internal -- External)',
     'Movement (NonKinetic -- Kinetic)',
     'Organization (Controlled Chaos -- Organized)',
     'Pace (Slow -- Fast)',
     'Perfectionism (Pragmastist -- Perfectionist)',
     'Risk (Risk Averse -- Risk Loving)',
     'Stategy (Make It Happen -- Let It Happen)',
     'Tactic (Tenacious -- Reframer)',
     'Workspace (Private -- Public)',
     'Noise (Silence -- Noise/Music)',
     'Nature (Urban -- Nature)',
     'Ritual (Novetly Seeker -- Creature of Habit)',
     'Constraints (Stifle By -- Stimulated By)'
     ]
    
    trim_df = trim_df[keepList]
    
    renameDict = {
     'Multitasking (Montasker -- Multitasker)': "Monotasker -- Multitasker",
     'Breadth (Specialist -- Generalist)': "Specialist -- Generalist",
     'Collaboration (Solo Creator -- Collaborator)': 'Solo Creator -- Collaborator',
     'Confidence (Self-Critical -- Self-Assured)': "Self-Critical -- Self-Assured",
     'Focus (Distractible -- Focused)': "Distractible -- Focused",
     'Inspriation Source (Inward -- Outward)': "Inwardly vs Outwardly Inspired",
     'Creative Reasoning (Rational -- Intuitive)': "Rational -- Intuitive",
     'Motivation (Internal -- External)': "Internally vs Externally Motivated",
     'Movement (NonKinetic -- Kinetic)': "NonKinetic -- Kinetic",
     'Organization (Controlled Chaos -- Organized)': "Controlled Chaos -- Organized",
     'Pace (Slow -- Fast)': "Slow -- Fast Paced",
     'Perfectionism (Pragmastist -- Perfectionist)': "Pragmatist -- Perfectionist",
     'Risk (Risk Averse -- Risk Loving)': "Risk Averse -- Risk Friendly",
     'Stategy (Make It Happen -- Let It Happen)': "Make It Happen -- Let It Happen",
     'Tactic (Tenacious -- Reframer)': "Tenacious -- Reframer",
     'Workspace (Private -- Public)': "Private -- Public Workspace",
     'Noise (Silence -- Noise/Music)': "Work in Silence -- Noise/Music",
     'Nature (Urban -- Nature)': "Urban -- Nature",
     'Ritual (Novetly Seeker -- Creature of Habit)': "Novetly Seeker -- Creature of Habit",
     'Constraints (Stifle By -- Stimulated By)': "Stifled_By -- Stimulated_By Constraints"}
 
    trim_df.rename(columns = renameDict,inplace=True)

    ###### add tag counts and tag lists for building network    
    trim_df['n_tags'] = trim_df['tags'].apply(lambda x: len(x.split("|")))
    trim_df['tags_list']= trim_df['tags'].str.split('|').apply(lambda x: [ss.strip() for ss in x])
    
    
    # remove recipients with less than 3 tags
    df_trimmed = trim_df[trim_df['n_tags']>=3]
    df_trimmed = df_trimmed.reset_index(drop=True)
    print ("%d respondents with 3 or more tags (%.2f of %d total respondents)"%(len(df_trimmed), (len(df_trimmed)/float(initial)), initial))

    ## summarize tag distribution
    tagsdf = buildTagHistDf (df, 'tags', mincnt=0)
    tagsdf.columns = ['Creative_Habits', 'count', 'percent']
    tagsdf.to_csv(tags_file, index=False)
   
    ###### and write out the dataframe
    print("Writing output files")
    df_trimmed.to_excel(outfile, index=False)
    
    
    
    return df_trimmed

############################################################################
if __name__ == '__main__':

    
    infile = params.responses_raw_data  # raw survey response data 
    outfile =  params.responses_cleaned_processed  #cleaned and tagged
    tags_file = params.tagdistr_file # creative habit tag distribution
    

    df = clean_HC_data(infile, outfile, tags_file)


    
