import os
import numpy as np
import shutil
from pyiron_base import Project, GenericJob, DataContainer, state, Executable, ImportAlarm

with ImportAlarm(
    "paraprobe functionality requires the `paraprobe` module (and its dependencies) specified as extra"
    "requirements. Please install it and try again."
) as paraprobe_alarm:
    from paraprobe_parmsetup.tools.transcoder_guru import ParmsetupTranscoder
    from paraprobe_parmsetup.tools.ranger_guru import ParmsetupRanger
    from paraprobe_transcoder.paraprobe_transcoder import ParaprobeTranscoder
    from paraprobe_autoreporter.wizard.ranger_report import AutoReporterRanger
    
class ParaprobeRanger(GenericJob):
    def __init__(self, project, job_name):
        super().__init__(project, job_name) 
        self.input = DataContainer(table_name="input")
        self.input.input_path = None
        self._executable = None
        self._executable_activate()
        state.publications.add(self.publication)
        self.jobid = 636502001
        self._transcoder_config = None
        self._transcoder_results = None
        self._ranger_config = None
        self._pos_file = None
        self._rrng_file = None
        
    @property
    def transcoder_config(self):
        return H5Web(self._transcoder_config)

    @property
    def transcoder_results(self):
        return H5Web(self._transcoder_results)

    @property
    def ranger_config(self):
        return H5Web(self._ranger_config)

    @property
    def ranger_results(self):
        return H5Web(self._ranger_results)
    
    @property
    def pos_file(self):
        return self._pos_file

    @pos_file.setter
    def pos_file(self, filename):
        if os.path.exists(filename):
            self._pos_file = filename

    @property
    def rrng_file(self):
        return self._rrng_file
    
    @rrng_file.setter
    def rrng_file(self, filename):
        if os.path.exists(filename):
            self._rrng_file = filename

    def _copy_file(self, filename):
        newfilename = os.path.join(self.working_directory, os.path.basename(filename))
        shutil.copy(filename, newfilename)
        return newfilename
    
    def _executable_activate(self, enforce = False):
        if self._executable is None or enforce:
            self._executable = Executable(
                codename='paraprobe-ranger',
                module='paraprobe-ranger',
                path_binary_codes=state.settings.resource_paths
            )
    
    def _configure_transcoder(self):
        transcoder = ParmsetupTranscoder()
        transcoder.add_task()
        transcoder.set_reconstruction_filename(self._pos_file)
        transcoder.set_ranging_filename(self._rrng_file)
        transcoder.commit_task()
        self._transcoder_config = transcoder.configure(self.jobid)
        
    def _execute_transcoder(self):
        transcoder = ParaprobeTranscoder(self._transcoder_config)
        self._transcoder_results = transcoder.execute()
    
    def _configure_ranger(self):
        ranger = ParmsetupRanger()
        self._ranger_config = ranger.apply_existent_ranging(self.working_directory, self.jobid)        
        
    def write_input(self):
        if ((self.pos_file is None) or (self.rrng_file is None)):
            raise ValueError("Set files")
    
    def run_static(self):
        self.pos_file = self._copy_file(self.pos_file)
        self.rrng_file = self._copy_file(self.rrng_file)
        self._configure_transcoder()
        self._execute_transcoder()
        self._configure_ranger()

    def collect_output(self):
        self._ranger_results = os.path.join(self.working_directory, f"PARAPROBE.Ranger.Results.SimID.{self.jobid}.h5")
    
    def to_hdf(self, hdf=None, group_name=None): 
        super().to_hdf(
            hdf=hdf,
            group_name=group_name
        )
        with self.project_hdf5.open("input") as h5in:
            self.input.to_hdf(h5in)

    def from_hdf(self, hdf=None, group_name=None): 
        super().from_hdf(
            hdf=hdf,
            group_name=group_name
        )
        with self.project_hdf5.open("input") as h5in:
            self.input.from_hdf(h5in)
    
    @property
    def publication(self):
        return {
            "paraprobe": [
                {
                    "title": "On Strong-Scaling and Open-Source Tools for High-Throughput Quantification of Material Point Cloud Data: Composition Gradients, Microstructural Object Reconstruction, and Spatial Correlations",
                    "journal": "arxiv",
                    "volume": "1",
                    "number": "1",
                    "year": "2022",
                    "doi": "10.48550/arXiv.2205.13510",
                    "url": "https://doi.org/10.48550/arXiv.2205.13510",
                    "author": ["Markus Kühbach", "Vitor Vieira Rielli", 
                               "Sophie Primig", "Alaukik Saxena", "David Mayweg",
                               "Benjamin Jenkins", "Stoichkov Antonov", "Alexander Reichmann",
                               "Stefan Kardos", "Lorenz Romaner", "Sandor Brockhauser"],
                }
            ]
        }