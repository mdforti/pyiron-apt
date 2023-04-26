import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pylab as plt

from pyiron_base import DataContainer
from pyiron_base import GenericJob, ImportAlarm

from compositionspace.segmentation import CompositionClustering
from compositionspace.postprocessing import DataPostprocess
from compositionspace.datautils import DataPreparation

class CompositionSpace(GenericJob):
    """
    Add some docs
    """
    def __init__(self, project, job_name):
        super().__init__(project, job_name)
        self.input = DataContainer(self._default_input, table_name="inputdata")
        self._composition_clusters_found = False
        self._data = None
        self._comp = None
        self._post = None
        self.input.analysis = None
        self.input.fileindex=0
        self.input.cluster_id=0
        self.input.plot=False
        self.input.plot3d=False
        self._input_dict = {}
        self._analyse_PCA_cumsum = False
        self._analyse_bics_minimization= False
        self._analyse_composition_clustering = False
        self._analyse_dbscan_clustering = False
        self._analyse_PCA_cumsum_done = False
        self._analyse_bics_minimization_done = False
        self._analyse_composition_clustering_done = False
        self._analyse_dbscan_clustering_done = False
        
    @property
    def _default_input(self):
        return {
            "input_path": None,
            #"output_path": None,
            "n_big_slices": 10,
            "voxel_size": 2,
            "bics_clusters": 10,
            "n_phases": 2,
            "ml_models": {
                "name": "GaussianMixture", 
                "GaussianMixture": {
                    "n_components": 2,
                    "max_iter": 100000,
                    "verbose": 0,
                    },
                "RandomForest": {
                    "max_depth": 0,
                    "n_estimators": 0,
                    },
                "DBScan": {
                    "eps": 3,
                    "min_samples": 5,
                    },
            }
        }



    def _create_input(self, indict, datacontainer):
        for key, val in indict.items():
            if key in datacontainer:
                if isinstance(val, dict):
                    self._create_input(indict[key], datacontainer[key])
                else:
                    indict[key] = getattr(datacontainer, key)
        return indict
    
    def write_input(self):
        #prepare data
        indict = self._create_input(self._default_input, self.input)
        indict["output_path"] = self.working_directory
        self._input_dict = indict
        self.input.fileindex=0
        self.input.plot=True
        self.input.plot3d=True
        if self.input.input_path is None:
            raise FileNotFoundError("Input path needs to be set before analysis")
            
    def _prepare_comp(self):
        if self._comp is None:      
            self._comp = CompositionClustering(self._input_dict)

    def _prepare_post_process(self):
        if self._post is None:
            self._post = DataPostprocess(self._input_dict)

    def _get_PCA_cumsum(self):
        self._prepare_comp()
        self._comp.get_PCA_cumsum(self._data.voxel_ratio_file, 
            self._data.voxel_files[self.input.fileindex])

    def _get_bics_minimization(self):
        self._prepare_comp()
        self._comp.get_bics_minimization(self._data.voxel_ratio_file, 
            self._data.voxel_files[self.input.fileindex])

    def _get_composition_clusters(self):
        self._prepare_comp()
        self._comp.get_composition_clusters(self._data.voxel_ratio_file, 
            self._data.voxel_files[self.input.fileindex])
        self._composition_clusters_found = True

    def _get_dbscan_clustering(self):        
        if not self._composition_clusters_found:
            self._get_composition_clusters()
        
        self._prepare_post_process()
        
        self._post.DBSCAN_clustering(self._comp.voxel_centroid_output_file, 
                        cluster_id = self.input.cluster_id,
                        plot=self.input.plot, plot3d=self.input.plot3d, save=True)

    def plot3d(self, **kwargs):
        if self._comp is None:
            raise RuntimeError("Run any composition calculation before to plot")
        return self._comp.plot3d(**kwargs)
    
    def analyse_PCA_cumsum(self):
        self._analyse_PCA_cumsum = True

    def analyse_bics_minimization(self):
        self._analyse_bics_minimization= True

    def analyse_composition_clustering(self):
        self._analyse_composition_clustering = True
        
    def analyse_dbscan_clustering(self):
        self._analyse_dbscan_clustering = True        

    def run_static(self):   
        self.status.running = True
        self._data = DataPreparation(self._input_dict)
        self._data.get_big_slices()
        self._data.get_voxels()
        self._data.calculate_voxel_composition()
        
        if self._analyse_PCA_cumsum:
            self._get_PCA_cumsum()
            self._analyse_PCA_cumsum_done = True

        if self._analyse_bics_minimization:
            self._get_bics_minimization()
            self._analyse_bics_minimization_done = True

        if self._analyse_composition_clustering:
            self._get_composition_clusters()
            self._analyse_composition_clustering_done = True

        if self._analyse_dbscan_clustering:
            self._get_dbscan_clustering()
            self._analyse_dbscan_clustering_done = True

        self.status.collect = True


    def collect_output(self):
        pass
        #self.collect_gene