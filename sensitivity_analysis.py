# -*- coding: utf-8 -*-

'''
Build a reference network
Repeatedly randomly sample 50% of records and build a network
Compare clusters in subsampled network to clusters in the reference network
'''


# %%
from ast import literal_eval
from build_decorate_network import build_creative_style_network
from Network.BuildNetwork import buildTagNetwork
import pandas as pd
import numpy as np
from collections import Counter
import sys
# import os
import pathlib as pl
# sys.path.append("../../OneDrive/Rich/Software/Tag2Network/tag2network")
sys.path.append("../../../GitHub/Tag2Network/tag2network")


# %%


# 1) build an ensemble of datasets sampled from the whole dataset.
# 2) build a network for the reference dataset
# 3) for each subsample, build a network and compare the clusters in the subsampled
# network to the clusters in the reference network
# 4) for each cluster in the reference network, identify the most-similar cluster
# in the subsampled network
#
# similarity is computed by comparing a list of most common tags in each cluster,
# where "common" is common relative to the global frequency of the tag
#
# alternative similarity method uses all tags and assigns a weight to each tag - weight is the
# product of local and global frequency. Then similarity is measure with weighted Jaccard similarity
#
def build_reference_network(df, idf, tag_attr, clus_attr):
    # build reference network by tag similarity
    # note: tagAttr must be a list of tags, not string

    print("Building network %s and IDF %s" % (tag_attr, str(idf)))
    return buildTagNetwork(df, color_attr=clus_attr, tagAttr=tag_attr,
                           idf=True, toFile=False, doLayout=False, draw=False)


def get_ref_network(reffile):
    df = pd.read_excel(reffile, sheet_name='nodes')
    df['top_tags'] = df['top_tags'].apply(
        literal_eval)  # convert from string to list
    df.fillna('', inplace=True)
    return df


def build_sample_networks(df, idf, tag_attr, niter, frac, linksPer=8, blacklist=[]):
    # build sample networks by tag similarity
    sample_networks = []
    idx = 0
    while idx < niter:
        idx += 1
        print("Building sample network %d" % idx)
        smpl_df = df.sample(frac=frac)
        '''
        smpl_nw_df, smpl_edges_df = buildTagNetwork(smpl_df, color_attr="Cluster", tagAttr=tag_attr,
                    toFile=False, idf=False, doLayout=False)
        '''
        smpl_nw_df, smpl_edges_df = build_creative_style_network(smpl_df, tag_attr,
                                                                 idf=idf, linksPer=linksPer, blacklist=blacklist,
                                                                 )
        sample_networks.append(smpl_nw_df)
    return sample_networks


# get tag weight in each cluster
# returns df where column is a tag, row is a cluster
def get_cluster_tag_weights(nwdf, clus_attr, global_tags=None):
    all_tag_counts = Counter()
    if global_tags:
        for val in global_tags:
            all_tag_counts[val] = 0
    nwdf['tags'].str.split('|').apply(lambda x: all_tag_counts.update(x))
    grps = nwdf.groupby(clus_attr)
    all_tags = list(all_tag_counts.keys())
    all_tags.sort()
    all_counts = np.array(list(all_tag_counts.values()))
    all_freq = all_counts / all_counts.sum()
    tag_idx = dict(zip(all_tags, range(len(all_tags))))
    clus_weights = []
    clusters = {}
    for clus, cdf in grps:
        grp_counts = Counter()
        cdf['tags'].str.split('|').apply(lambda x: grp_counts.update(x))
        grp_tags = grp_counts.keys()
        clus_tag_idx = list(map(lambda x: tag_idx[x], grp_tags))
        clus_tag_cnt = np.array(list(map(lambda x: grp_counts[x], grp_tags)))
        clus_freq = np.zeros(len(all_tags))
        clus_freq[clus_tag_idx] = clus_tag_cnt / clus_tag_cnt.sum()
        clus_weights.append(clus_freq / all_freq)
        clusters[clus] = clus_tag_cnt.sum() / all_counts.sum()
    df = pd.DataFrame(clus_weights, columns=all_tags,
                      index=list(clusters.keys()))
    return df, clusters


# compute pairwise comparison of weighted tags in all pairs of clusters in two networks
def compare_network_clusters_weighted(idx_1, idx_2, ref_tag_wts, smpl_tag_wts, clus_frac, smpl_frac, all_sims, is_self=False):
    # compute weighted Jaccard similarity of two sets of weights
    def weighted_similarity(w1, w2):
        wt_max = np.maximum(w1, w2)
        wt_min = np.minimum(w1, w2)
        return wt_min.sum() / wt_max.sum()

    results = []
    sims = []
    for ref_clus in ref_tag_wts.index:
        clus_results = []
        for smpl_clus in smpl_tag_wts.index:
            if is_self and smpl_clus == ref_clus:
                continue
            clus_sim = weighted_similarity(ref_tag_wts.loc[ref_clus].to_numpy(),
                                           smpl_tag_wts.loc[smpl_clus].to_numpy())
            clus_results.append({'smpl_clus': smpl_clus,
                                 'smpl_frac': smpl_frac[smpl_clus],
                                 'clus_sim': clus_sim})
        if len(clus_results) > 0:
            clus_df = pd.DataFrame(clus_results)
            idxmax = clus_df['clus_sim'].idxmax()
            results.append({'idx_1': idx_1,
                            'idx_2': idx_2,
                            # 'idxmax_clus': idxmax,
                            'ref_clus': ref_clus,
                            'ref_frac': clus_frac[ref_clus],
                            'max_sim': clus_df.loc[idxmax, 'clus_sim'],
                            'max_clus': clus_df.loc[idxmax, 'smpl_clus'],
                            'max_frac': clus_df.loc[idxmax, 'smpl_frac'],
                            'sim_mn': clus_df['clus_sim'].mean(),
                            'sim_sd': clus_df['clus_sim'].std(),
                            })
            sims.append({'clus': ref_clus, 'sims': clus_df['clus_sim']})
    if all_sims is None:
        all_sims = pd.DataFrame(sims).explode('sims')['sims'].to_numpy()
        all_sims.sort()
    for res in results:
        res['percentile_max_sim'] = np.searchsorted(
            all_sims, res['max_sim']) / all_sims.size
    return results, all_sims


def compute_sampled_similarity(df, reffile, tag_attr, suffix,
                               idf=False, linksPer=8, blacklist=[],
                               clus_attr='Cluster',
                               niter=100, frac=0.5, maxtags=10, weighted=True):
    """
    # get tag distribution in each cluster
    def get_tag_distr(nwdf, clus_attr, tag_attr):
        grps = nwdf.groupby(clus_attr)
        clus_counts = grps[tag_attr].count()
        tag_counts = grps[tag_attr].sum().apply(lambda x: Counter(x))
        df = pd.DataFrame({'TagCount': tag_counts, 'Count': clus_counts})
        df['TagFreq'] = df.apply(lambda x: {k: v/x['Count'] for k, v in x['TagCount'].items()}, axis=1)
        df['Frac'] = df['Count']/df['Count'].sum()
        return df

    # compute weighted Jaccard similarity of two distributions
    def distr_similarity(d1, d2):
        all_labels = list(set(d1.keys()).union(set(d2.keys())))
        l1 = np.array([d1[val] if val in d1 else 0 for val in all_labels])
        l2 = np.array([d2[val] if val in d2 else 0 for val in all_labels])
        return np.minimum(l1, l2).sum() / np.maximum(l1, l2).sum()

    # compute pairwise comparison of tag distribution in all pairs of clusters in two networks    
    def compare_network_clusters_by_tag_distr(ref_distr, nw, clus_attr, tag_attr):
        results = []
        smpl_distr = get_tag_distr(nw, clus_attr, tag_attr)
        for ref_clus in ref_distr.index:
            if ref_distr.loc[ref_clus]['Count'] > 10:
                for smpl_clus in smpl_distr.index:
                    if smpl_distr.loc[smpl_clus]['Count'] > 10:
                        results.append((ref_clus, smpl_clus, distr_similarity(ref_distr.loc[ref_clus]['TagFreq'], smpl_distr.loc[smpl_clus]['TagFreq'])))
        return results


    # compute reference network tag distribution in each cluster
    ref_distr = get_tag_distr(ref_df, clus_attr, tag_attr)
    self_sim = compare_network_clusters_by_tag_distr(ref_distr, ref_df, clus_attr, tag_attr)

    # compare each sampled network to the reference network
    results = []
    for nw in sample_networks:
        results.append(compare_network_clusters_by_tag_distr(ref_distr, nw, clus_attr, tag_attr))
    """
    ##########################################################################
    # do cluster similarity computation based on top tags - these tags are selected
    # as common relative to the global frequency

    # compute Jaccard similarity of two sets
    def tag_similarity(d1, d2):
        s1 = set(d1)
        s2 = set(d2)
        return len(s1.intersection(s2))/len(s1.union(s2))

    # get limited number of top tags of each cluster
    def get_top_tags(nwdf, clus_attr, maxtags):
        tt = 'top_tags'
        grps = nwdf.groupby(clus_attr)
        clus_counts = grps[tt].count()
        tags = grps[tt].first().apply(lambda x: x[:maxtags])
        df = pd.DataFrame({'Tags': tags, 'Count': clus_counts})
        df['Frac'] = df['Count']/df['Count'].sum()
        df['Tags'] = df['Tags'].apply(lambda x: [ss.strip() for ss in x])
        return df

    # compute pairwise comparison of toptags in all pairs of clusters i two networks
    def compare_network_clusters_top_tags(ref_tags, nw, clus_attr, idx, maxtags, is_self=False):
        results = []
        smpl_tags = get_top_tags(nw, clus_attr, maxtags)
        for ref_clus in ref_tags.index:
            if ref_tags.loc[ref_clus]['Count'] <= 10:
                continue
            clus_results = []
            for smpl_clus in smpl_tags.index:
                if is_self and smpl_clus == ref_clus:
                    continue
                if smpl_tags.loc[smpl_clus]['Count'] <= 10:
                    continue
                tag_sim = tag_similarity(
                    ref_tags.loc[ref_clus]['Tags'], smpl_tags.loc[smpl_clus]['Tags'])
                clus_results.append({'smpl_clus': smpl_clus,
                                     'smpl_frac': smpl_tags.loc[smpl_clus]['Frac'],
                                     'tag_sim': tag_sim})
            if len(clus_results) > 0:
                clus_df = pd.DataFrame(clus_results)
                idxmax = clus_df['tag_sim'].idxmax()
                results.append({'idx': idx,
                                'ref_clus': ref_clus,
                                'ref_frac': ref_tags.loc[ref_clus]['Frac'],
                                'max_sim': clus_df.loc[idxmax, 'tag_sim'],
                                'max_clus': clus_df.loc[idxmax, 'smpl_clus'],
                                'max_frac': clus_df.loc[idxmax, 'smpl_frac'],
                                'sim_mn': clus_df['tag_sim'].mean(),
                                'sim_sd': clus_df['tag_sim'].std(),
                                #  'sims': clus_df
                                })
        return results

    ref_df = get_ref_network(reffile)

    if weighted:
        clus_tag_wts, clus_frac = get_cluster_tag_weights(ref_df, clus_attr)

        # compute and output reference set intra-cluster similarity
        self_clus_sim, all_sims = compare_network_clusters_weighted(0, clus_tag_wts, clus_tag_wts,
                                                                    clus_frac, clus_frac, None, is_self=True)
        self_sim_df = pd.DataFrame(self_clus_sim)
        self_sim_df = self_sim_df.sort_values('ref_frac', ascending=False)
        self_sim_df.to_csv(
            "results/CreativeStyles_SelfSimWtd_" + suffix + ".csv", index=False)

        # build subsample networks using same settings as reference network
        sample_networks = build_sample_networks(df, idf, tag_attr, niter, frac,
                                                linksPer=linksPer, blacklist=blacklist)

        # compare each sampled network to the reference network
        results_tags = []
        for idx, nw in enumerate(sample_networks):
            smpl_tag_wts, smpl_frac = get_cluster_tag_weights(
                nw, clus_attr, clus_tag_wts.columns.to_list())
            results_tags.extend(compare_network_clusters_weighted(idx, clus_tag_wts, smpl_tag_wts,
                                                                  clus_frac, smpl_frac, all_sims)[0])
    else:
        # ref_df, ref_edgesdf = build_reference_network(df, idf, tag_attr, clus_attr)
        ref_tags = get_top_tags(ref_df, clus_attr, maxtags)

        # compute and output reference set intra-cluster similarity
        self_tag_sim = compare_network_clusters_top_tags(
            ref_tags, ref_df, clus_attr, 0, maxtags, is_self=True)
        self_sim_df = pd.DataFrame(self_tag_sim)
        self_sim_df = self_sim_df.sort_values('ref_frac', ascending=False)
        self_sim_df.to_csv("results/CreativeStyles_SelfSim_" +
                           suffix + ".csv", index=False)

        # build subsample networks using same settings as reference network
        sample_networks = build_sample_networks(df, idf, tag_attr, niter, frac,
                                                linksPer=linksPer, blacklist=blacklist)

        # compare each sampled network to the reference network
        results_tags = []
        for idx, nw in enumerate(sample_networks):
            results_tags.extend(compare_network_clusters_top_tags(
                ref_tags, nw, clus_attr, idx, maxtags))

    # output raw tag similarity results for all replicates
    rdf = pd.DataFrame(results_tags)
    rdf = rdf.sort_values(['ref_frac', 'max_sim'], ascending=[False, False])
    if weighted:
        tagsimbase = "results/CreativeStyles_TagSimilarity_Wtd_"
        clusstatbase = "results/CreativeStyles_ClusterStats_Wtd_"
    else:
        tagsimbase = "results/CreativeStyles_TagSimilarity_"
        clusstatbase = "results/CreativeStyles_ClusterStats_"
    rdf.to_csv(tagsimbase + suffix + ".csv", index=True)

    # compute and output aggregate stats for each cluster
    clus_stat_df = rdf.groupby('ref_clus').agg({'max_sim': ['mean', 'std'],
                                                'z_sim': ['mean', 'std'],
                                                'ref_frac': 'first',
                                                'max_frac': 'mean'}).reset_index()
    clus_stat_df.columns = ['Cluster', 'Avg_Similarity', 'Std_Similarity', 'Avg_Sim_Z', 'Std_Sim_Z',
                            'Cluster_frac', 'Avg_SimCluster_Frac']
    clus_stat_df['Avg_Frac_Overlap'] = clus_stat_df['Avg_Similarity'].apply(
        lambda x: (2*x)/(1+x))
    clus_stat_df = clus_stat_df.sort_values('Cluster_frac', ascending=False)
    clus_stat_df.to_csv(clusstatbase + suffix + ".csv", index=False)
    return clus_stat_df


def compare_network_clusters(nw_list, clus_attr='cluster_name'):
    """Pairwise comparison of network clusters in a list of networks."""
    results = []
    for idx, nw in enumerate(nw_list):
        wts_1, frac_1 = get_cluster_tag_weights(nw, clus_attr)
        for idx2, nw2 in enumerate(nw_list[idx:]):
            wts_2, frac_2 = get_cluster_tag_weights(nw2, clus_attr)
            res = compare_network_clusters_weighted(idx, idx + idx2, wts_1, wts_2,
                                                    frac_1, frac_2, None)[0]
            results.extend(res)
    return pd.DataFrame(results)


##########################################################################
if __name__ == '__main__':
    # paths
    wd = pl.Path.cwd()
    datapath = wd/"data"
    resultspath = wd/"results"
    figpath = wd/"figures"

    # ## parameters for building network
    linksPer = 8
    tags = 'tags'
    tagattr = tags+"_list"  # buildNetwork needs tags as a list
    # ["Early Bird", "Night Owl", "Tortured Artist"]
    blacklist = ['Emotionally Stable', 'Tortured Artist']
    maxtags = 5

    # ## filename params
    version = "2020_11_25"
    if blacklist == ['Emotionally Stable', 'Tortured Artist']:
        # run_params = "allTags_" + str(linksPer) + "links_" + version #tag blasklisted, linksPer Node, date
        # tag blasklisted, linksPer Node, date
        run_params = "minus" + str(blacklist) + "_" + \
            str(linksPer) + "links_" + version
    else:
        run_params = "minus" + str(blacklist) + "_" + str(linksPer) + "links_" + str(
            maxtags) + "maxtags_" + version  # tag blasklisted, linksPer Node, date

    sim_params = run_params  # + "_" + str(maxtags) + "maxtags"
    # filenames
    infile = datapath/"CreativeStyle_Responses_Tagged_Cleaned.xlsx"
    ref_nw_file = resultspath / \
        ("CreativeStyle_Network_" + run_params + ".xlsx")  # network file

    # ## run sensitivituy analysis
    print('reading file')
    df = pd.read_excel(infile)  # get raw data
    # convert from string to list
    df[tagattr] = df[tagattr].apply(literal_eval)
    df = df.fillna('')

    clus_stat_df = compute_sampled_similarity(df, ref_nw_file, tagattr, sim_params,
                                              idf=False, linksPer=linksPer, blacklist=blacklist,
                                              clus_attr='cluster_name',
                                              niter=10, frac=0.5, maxtags=maxtags)


'''
IDEA:
Build similarity distribution from pairwise cluster similarities of full dataset of 
all non-identical clusters

Then in the sample to full dataset comparison, look for similarities that are 
high-value outliers from this distribution of all non-matching cluster pairs.
These are clusters that are more similar than expected by chance.
'''
