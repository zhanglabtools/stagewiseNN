# -*- coding: utf-8 -*-
"""
Created on Fri May 29 19:50:50 2020

@author: xyliu
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
import scanpy as sc

WORKDIR = Path(r'D:\Users\xyliu\003')
os.chdir(WORKDIR)

from PipeHandler import PipeHandler 
import Build as B
import funx as fx
import funx_amph as fxa
from StagewiseNN import stagewise_knn

datadir = fxa.DATADIR / 'afterQC_formal' /'merged'
resdir = fxa.DATADIR / 'res-scanpy' / 'stg_nn-hvgs-later'
figdir = resdir / 'figs'
fx.check_dirs(figdir)

genedir = fxa.DATADIR / 'genes'
sc.set_figure_params(fontsize=14)

# In[]
''' subsampled for testing '''
Adata = sc.read_h5ad(datadir / 'merged_subsampled.h5ad')
name = 'sub-stg_nn0'

# In[]
''' Whole data '''
Adata = sc.read_h5ad(datadir  / 'merged_afterQC.h5ad')
name = 'stg_nn'
Adata = B.TakeGroups(Adata, fxa.Stages, key='stage')

# In[]

hvg_freq = pd.read_csv(fxa.DATADIR / 'genes' / 'hvg_freq_scanpy-later.csv', index_col=0, header=None).iloc[:, 0]
used_genes1 = hvg_freq[hvg_freq >= 3].index.tolist()
hvg_freq.value_counts()
#used_genes1 = fx.load_namelist(datadir.parent / 'merged_hvgs.csv')
#relate_genes = fx.load_namelist(genedir / 'related_genes_-0.7_0.7.csv')
candi_markers = fx.load_namelist(genedir / 'candidate_marker_ids.csv', header='infer')

#fx.VennPlot([tmp, used_genes1])
#fx.VennPlot([tmp, candi_markers])
fx.VennPlot([candi_markers, used_genes1])


# In[]
#B.cross_labeling(Adata.obs, ['stage', 'primer'], inplace=True)
#Adata
#Adata.X.data[:5]

ph = PipeHandler(Adata, name=name, resdir=resdir)
#ph.name += '_mk-hvg' 
#B.cross_labeling(ph.adata.obs, ['stage', 'primer'], inplace=True)

ph.NormLog_rev()

if False:
    # HVGs or provided gene-list
    ph.HVGs(min_mean=0.04, min_disp=0.25, batch_key='stage_primer',)# n_top_genes=3000)
    fx.VennPlot([candi_markers, ph.hvgs()])
else:
    _used_genes = list(set(candi_markers + used_genes1))
    ph.SetHVGs(_used_genes, slim=True)
ph.adata.raw.X.data[:5]

# inspect cells-per-gene
#ph.adata.var['n_cells'] = (ph.adata.X > 0).sum(axis=0).flatten()
#ph.adata.var['n_cells'] = (ph.adata.X > 0).sum(axis=0).A1
#ph.adata.var['n_cells'].describe()
#(ph.adata.var['n_cells'] <= 200).sum()


# ===================
#B.ResetX(ph.adata, copy=False)
scale = True
ph.scale(groupby='stage_primer', scale=scale)
ph.PCA(n_comps=50, )

#ph.Neighbors(nneigh=15, n_pcs=50, )
#orig_neigh = ph.adata.uns['neighbors'].copy()
#ph.Umap(min_dist=0.1)
#ph.vis(color='stage', palette='Spectral', save=f'_{ph.name}_pipe0.png')
#ph.save(name='pipe3000')

# In[]
X = ph.adata.obsm['X_pca']
X = ph.adata.X
#ph.name += '_sepPCA'

#ph.adata.obs['stage'] = Adata.obs['stage'].copy()
stage_lbs0 = ph.adata.obs['stage'][:]
pd.value_counts(stage_lbs0)

Stages = fxa.Stages
#merge_late = False

stage_lbs = stage_lbs0
stage_ord = Stages
#stage_ord
    
# ===========================================
leaf_size = 1
n_pcs = [30] * 5 + [50] * 4
#n_pcs = 50
#k = [15] * 10 + [10] * 2 + [5] * 3
k = [10] * 7 + [5] + [3]
#k = [5] * 15
sigma = [_k / 2 for _k in k]

do_pca = False if X.shape[1] < 100 else True
distmat, connect0 = stagewise_knn(X, stage_lbs, stage_ord, 
                                 k=k, leaf_size=leaf_size, do_pca=do_pca,
                                 n_pcs = n_pcs,
                                 norm_dists=True,
                                 sigma=sigma, norm_sample=True)
sparse.save_npz(resdir / 'formal_distmat.npz', distmat)
sparse.save_npz(resdir / 'formal_connect0.npz', connect0)


connect = connect0.copy()
connect[connect > 0] = 1
# ===========================================
ph.adata.uns['neighbors'] = {
        'params': {'n_neighbors': k, 'method': 'umap', 'metric': 'cosine'},
        'connectivities': connect, #.to_csr(),
        'distances': distmat,}

sc.tl.umap(ph.adata, min_dist=0.1, spread=1)
ph.vis(color='stage', palette='Spectral',)

tt_glb = f'Total of {ph.adata.shape[0]} cells'
ph.vis(color='stage', palette='Spectral', title=tt_glb, save=f'_{ph.name}_stage.png')
ph.vis(color='stage', palette='Spectral', title=tt_glb, save=f'_{ph.name}_stage.pdf')
#
##
#sc.pl.umap(ph.adata, color='stage', palette='Spectral', save=f'_{ph.name}_stgNN.pdf')
sc.pl.umap(ph.adata, color='primer', palette='Spectral', save=f'_{ph.name}_primer.png')
#ph.save()

# In[]
ph.adata
ph.Clustering(res=2.5, keep_results=True)
ph.vis(color='leiden', save=f'_{ph.name}_leiden.png')

ph.save()
#ph.save_meta()



# In[]
''' inspect some certain markers
'''
# PGCs
#Tbx2 (bf_00016583)
#Nanos (bf_00004829)
MarkerIds = pd.read_csv(fxa.DATADIR / 'genes' / 'MarkerIDs0619-1.csv',
                        index_col=0)
ext_dict = {
        'bf_00013097': 'DNMT1',
        'bf_00019348': 'Hu_Elav', # neural ectoderm
#        'bf_00016583': 'Tbx2',
#        'bf_00004829': 'Nanos',
#        'bf_00008183': 'LRIG3',
        'bf_00002546': 'Sox17', # endoderm
        'bf_00006571': 'Wnt8', # Mesoderm
        'bf_00016125': 'FoxJ1', # Epithelial ectoderm
        'bf_00023325': 'Keratin', # Epithelial ectoderm
        'bf_00020985': 'CHRD', # notochord
        }
marker_dict = MarkerIds.iloc[:, 0].to_dict()
marker_dict.update(ext_dict)

cmap_g = fx.diy_cmap_grey_bg()

for gid, gn in marker_dict.items():
#for gid, gn in ext_dict.items():
    gexpr = ph.adata.raw[:, gid].X.flatten()
    _vmax = np.quantile(gexpr[gexpr > 0], 0.99)
    
    ph.vis(gid, title=gn, cmap=cmap_g, 
           vmax=_vmax,
           save=f'_{ph.name}_{gn}_{gid}.pdf' #+ '-sub.png'
           )
    ph.vis(gid, title=gn, cmap=cmap_g, 
           vmax=_vmax,
           save=f'_{ph.name}_{gn}_{gid}.png' #+ '-sub.png'
           )






# In[]
    
''' load merged scanpy-labels (produced by `amph_tree_on_clusters.py`)

'''
stage_ord
metadir = fxa.DATADIR / 'res-adjust' / '0622-v1'
fnames = [f'{sn}_metadata.csv' for sn in fxa.sampleNames(stage_ord)]
sc_lbs = fx.merge_metafiles(metadir, fnames, cols='leiden')
sc_lbs.head()

sc_key = 'stg_leiden'
#ph.adata.obs['stg_leiden'] = sc_lbs['leiden'].astype(str)
ph.adata.obs[sc_key] = sc_lbs.astype(str)
B.cross_labeling(ph.adata.obs, ['stage', sc_key], inplace=True)

ph.adata.obs.head()

#Adata.obs[sc_key] = sc_lbs.astype(str)
#B.cross_labeling(Adata.obs, ['stage', sc_key], inplace=True)
###Adata.write(datadir / 'merged_afterQC.h5ad')


# In[]
    
''' load merged srt-labels (produced by `amph_tree_on_clusters.py`)
'''
srt_lbs = pd.read_csv(datadir/ 'merged' / '_cated_tree_ident.csv', index_col=0)
srt_lbs.head()

ph.adata.obs['tree_ident'] = srt_lbs['tree.ident'].astype(str)
B.cross_labeling(ph.adata.obs, ['stage', 'tree_ident'], inplace=True)

ph.adata.obs.head()



# In[]
''' highlight the clusters in some specific stage
'''

def label_mask_others(df, key, keeps, key_new='tmp', lb_masked='others', copy=False):
    
    if copy:
        df = df.copy()
    df[key_new] = df[key].apply(lambda x: x if x in keeps else lb_masked)
    
    return df if copy else None

key = 'stage_tree_ident'
stg = 'E10'
key_new = f'{stg}_clusters'
keeps = ph.adata.obs[key][ph.adata.obs[key].str.startswith(stg)].unique()
label_mask_others(ph.adata.obs, key, keeps, key_new)

ph.vis(color = key_new, groups = keeps)


# In[]
''' connectivities between stage-clusters
connect and refine groups stage-by-stage
'''
import seaborn as sns
import networkx as nx
import amph_graph2tree as g2t

def dfFromG(G):
    node_pa = G.nodes.data('parent', default=np.nan)
    df_tree = pd.DataFrame(node_pa, columns=['node', 'parent'])
    df_tree['label'] = df_tree['node'].copy()
    df_tree['stage'] = df_tree['node'].apply(lambda x: x.split('_')[0])
    df_tree['stage_int'] = df_tree['stage'].apply(lambda x: int(x.strip('E')))
    return df_tree


df = ph.adata.obs
group_lbs = df['stage_stg_leiden'].values
stage_lbs = df['stage'].values
stage_ord = list(fxa.Stages0)

conn_upper = sparse.triu(connect0).tocsc()
adj_max = g2t.max_connection(conn_upper)



############[before refining]############
#gs0 = g2t.agg_group_edge_props(adj_max, group_lbs0=group_lbs, )
#
#sns.heatmap(gs0)
#G0 = fxa.TreeByStages(gs0, stages = stage_ord)
#fxa.plot_tree_by_stages(G0, )
#print(nx.info(G0))

#df_tree0 = dfFromG(G0)
#df_tree0.to_csv(resdir/ f'tree_struct_orig.csv', index=False, header=True)

#########################################


#stg_grp_dict = g2t.make_stage_group_dict(group_lbs, stage_lbs=stage_lbs)

edgedf, new_group_lbs = g2t.adaptiveTree(adj_max, group_lbs, stage_ord=stage_ord)
df['stg_groups_new'] = new_group_lbs

edgedf.prop.hist()
#########################################

cells_per_group = pd.value_counts(new_group_lbs)

all_groups = pd.unique(new_group_lbs)
gs1 = edgedf.pivot(index='parent', columns='node', values='prop')
gs1 = gs1.reindex(all_groups, all_groups)
gs1.fillna(0, inplace=True)

G = fxa.TreeByStages(gs1, stages = stage_ord, cross_stg=False)
fxa.plot_tree_by_stages(G, )



headr = 'sepPCA_'
headr = 'comPCA_'

edgedf.head()
edgedf = edgedf.set_index('node', drop=False)
edgedf['n_cells'] = cells_per_group
edgedf.to_csv(resdir / f'{headr}tree_struct_init.csv', index=False, header=True)

####ph.save(name='final-sepPCA50')


# In[]
''' prepare for ggTree
'''


df_tree = dfFromG(G)
df_tree.head()

df_tree.to_csv(resdir/ f'{headr}tree_struct.csv', index=False, header=True)

#
### compute group average for all genes
groupby = 'stg_groups_new'
adata = ph.adata
props_all = B.GroupMean(adata, groupby, use_raw=True, binary=True,)
means_all = B.GroupMean(adata, groupby, use_raw=True,)
props_all.to_csv(resdir / f'{headr}expr_prop_all.csv', index=True, header=True)
means_all.to_csv(resdir / f'{headr}avg_expr_all.csv', index=True, header=True)

#means_all.sum().hist()
'''
## normalize by total sums (NOT necessary)
'''
med = means_all.sum().median()
means_all_scaled = means_all.apply(lambda x: med * x / np.sum(x), axis=0)
means_all_scaled.to_csv(resdir / f'{headr}avg_expr_all_scaled.csv', index=True, header=True)


# In[]



























# In[]
''' Stage-related genes
'''

ph.DE(method='t-test', groupby='stage')
ph.dot_de(5, groupby='stage',
          color_map='RdPu',
          standard_scale='var', 
          save=f'_{ph.name}.png')
#ph.dot_de(5, groupby='stage',
#          color_map='RdPu',
#          standard_scale='var', 
#          save=f'_{ph.name}.pdf')




# In[]
''' PAGA : DO not work !!! (because no inner connection withib-stage)
'''

paga_on = key
cats = ph.adata.obs[paga_on].cat.categories
sc.tl.paga(ph.adata, groups=paga_on)

sc.pl.paga(ph.adata, )
sc.pl.paga_compare(ph.adata, )


group_sim_paga = pd.DataFrame(ph.adata.uns['paga']['connectivities'].toarray(), 
                              index=cats, columns=cats)

G = fxa.TreeByStages(group_sim_paga, stages = Stages)
fxa.plot_tree_by_stages(G, )


sns.heatmap(group_sim_paga.iloc[:40, :40])
sns.clustermap(group_sim_paga.iloc[:40, :40], figsize=(6, 6))

#key1 = 'paga_connect'
#key2 =  'paga_connect_tree'
#ph.adata.uns['paga_connect'] = ph.adata.uns['paga']['connectivities']
#ph.adata.uns['paga_connect_tree'] = ph.adata.uns['paga']['connectivities_tree']
#sc.pl.paga_adjacency(ph.adata, key1, key2, )



# In[]












