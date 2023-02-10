import os
import numpy as np
import shutil
import sys

from jupyterlab_h5web import H5Web
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
        self.output = DataContainer(table_name="output")
        self.input.input_path = None
        #self.executable = f"mpiexec -n $1 paraprobe_ranger 636502001 {self.working_directory}/PARAPROBE.Ranger.Config.SimID.636502001.nxs;"
        self._executable = None
        self._executable_activate()
        state.publications.add(self.publication)
        self.jobid = 636502001
        self._transcoder_config = None
        self._transcoder_results = None
        self._ranger_config = None
        self._pos_file = None
        self._rrng_file = None
        self._current_dir = os.getcwd()
    
    def _pipe_output_to_file(filename):
        def _wrapper(method):
            """
            This is a temporary fix until paraprobe input outputs etc can be fixed
            """
            def change_stdout(self):
                orig_stdout = sys.stdout
                outfile = os.path.join(self.working_directory, filename)
                f = open(outfile, 'w')
                sys.stdout = f
                method(self)
                sys.stdout = orig_stdout
                f.close()
            return change_stdout
        return _wrapper
    
    def _change_directory(method):
        """
        Temporarily switch directory
        """
        def change_dir(self):
            os.chdir(self.working_directory)
            method(self)
            os.chdir(self._current_dir)            
        return change_dir
    
    def _read_temporary_output_file(self, filename, clean=True):
        outfile = os.path.join(self.working_directory, filename)
        if clean:
            lines = []
            with open(outfile, "r") as fin:
                for line in fin:
                    line = line.strip().split()
                    lines.append(line)
        else:
            with open(outfile, "r") as fin:
                lines = fin.read()
        return lines
            
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
        self._pos_file = filename

    @property
    def rrng_file(self):
        return self._rrng_file
    
    @rrng_file.setter
    def rrng_file(self, filename):
        self._rrng_file = filename

    def _copy_file(self, filename):
        if os.path.exists(filename):
            shutil.copy(filename, self.working_directory)
            return os.path.basename(filename)
        else:
            raise FileNotFoundError(f"file {filename} not found")
            
    def _executable_activate(self, enforce = False):
        if self._executable is None or enforce:
            self._executable = Executable(
                codename='paraprobe-ranger',
                module='paraprobe-ranger',
                path_binary_codes=state.settings.resource_paths
            )
    
    @_change_directory
    @_pipe_output_to_file("config_transcoder.log")
    def _configure_transcoder(self):
        transcoder = ParmsetupTranscoder()
        self._transcoder_config = transcoder.load_reconstruction_and_ranging(
        working_directory=self.working_directory,
        reconstructed_dataset=self.pos_file,
        ranging_definitions=self.rrng_file,
        jobid=self.jobid)
    
    @_change_directory
    @_pipe_output_to_file("execute_transcoder.log")
    def _execute_transcoder(self):
        transcoder = ParaprobeTranscoder(self._transcoder_config)
        self._transcoder_results = transcoder.execute()
    
    @_change_directory
    @_pipe_output_to_file("config_ranger.log")
    def _configure_ranger(self):
        ranger = ParmsetupRanger()
        self._ranger_config = ranger.apply_existent_ranging(self.working_directory, 
                                    transcoder_config_sim_id=self.jobid,
                                    transcoder_results_sim_id=self.jobid,
                                    ranger_results_sim_id=self.jobid)
        
    def write_input(self):
        if ((self.pos_file is None) or (self.rrng_file is None)):
            raise ValueError("Set files")

        self.pos_file = self._copy_file(self.pos_file)
        self.rrng_file = self._copy_file(self.rrng_file)
        self._configure_transcoder()
        self._execute_transcoder()
        self._configure_ranger()
    
    def _collect_logs(self):
        config_transcoder_log = self._read_temporary_output_file("config_transcoder.log", clean=False)
        execute_transcoder_log = self._read_temporary_output_file("execute_transcoder.log", clean=False)
        config_ranger_log = self._read_temporary_output_file("config_ranger.log", clean=False)
        self.output["log/configure/transcoder"] = config_transcoder_log
        self.output["log/execute/transcoder"] = execute_transcoder_log
        self.output["log/configure/ranger"] = config_ranger_log
        self.output["log/execute/ranger"] = ""
        
    @_pipe_output_to_file("result_ranger.log")
    def _collect_ranger_results(self):
        self._ranger_results = os.path.join(self.working_directory, f"PARAPROBE.Ranger.Results.SimID.{self.jobid}.h5")
        ranger_report = AutoReporterRanger(self._ranger_results, self.jobid)
        ranger_report.get_summary()
    
    def _parse_ranger_results(self):
        lines = self._read_temporary_output_file("result_ranger.log")
        self.output["ranger/ion_count"] = int(lines[0][2].strip(','))
        self.output["ranger/unit"] = "at. wt%"
        for line in lines[1:]:
            key = line[3].strip(',')  
            self.output[f'ranger/{key}'] = float(line[1].strip(','))        
        
    def collect_output(self):
        self._collect_ranger_results()
        self._parse_ranger_results()
        self._collect_logs()
        
    
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