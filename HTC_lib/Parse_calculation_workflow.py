
# coding: utf-8

# # created on Feb 18 2018

# In[1]:


import os


# In[2]:


class Read_Only_Dict(dict):
    def __init__(self, *args, **kwargs):
        super(Read_Only_Dict, self).__init__(*args, **kwargs)
        
    def __setitem__(self, key, value):
        raise Exception("{} instance is read-only and cannot be changed!".format(self.__class__.__name__))
    
    def __delitem__(self, key):
        raise Exception("{} instance is read-only and cannot be changed!".format(self.__class__.__name__))
    
    @classmethod
    def from_dict(cls, dictionary):
        read_only_dictionary = {}
        for key, value in dictionary.items():
            if isinstance(value, list):
                value = tuple(value)   
            elif isinstance(value, dict):
                value = Read_Only_Dict.from_dict(value)
                
            read_only_dictionary[key] = value
            
        return Read_Only_Dict(**read_only_dictionary)


# In[4]:


def parse_calculation_workflow(filename="Calculation_setup"):
    """
    the input file describes a sequence of DFT calculations and modifications of vasp input files before calculations.
    """
    
    workflow = []
    
    with open(filename, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    firework_block_list = []
    for line in lines:
        line = line.split("#")[0].strip()
        if line:
            if line.startswith("**start"):
                firework_block_list.append([])
            else:
                if not line.startswith("**end"):
                    firework_block_list[-1].append(line)
    firework_block_list = [block for block in firework_block_list if block]
        
    for firework_block_ind, firework_block in enumerate(firework_block_list):
        workflow.append(parse_firework_block(block_str_list=firework_block, step_no=firework_block_ind+1)) 
                    
    return workflow              


# In[5]:


def old_parse_calculation_workflow(filename="Calculation_setup"):
    """
    the input file describes a sequence of DFT calculations and modifications of vasp input files before calculations.
    """
    
    workflow = []
    
    with open(filename, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    valid_lines = []
    for line in lines:
        if line.startswith("#"):
            continue
        elif "#" in line:
            valid_lines.append(line.split("#")[0])
        else:
            valid_lines.append(line)
    lines = valid_lines
    
    line_ind, line_ind_max = 0, len(lines)-1
    while line_ind <= line_ind_max:
        line = lines[line_ind].lower()
        line_ind += 1
            
        if line.startswith("**start"):
            firework = {}
        elif line.startswith("**end"):
            assert "step_no" in firework.keys(), "Error: Must specify tag step_no starting from 1."
            firework["step_no"] = int(firework["step_no"])
            if firework["step_no"] > 1:
                if firework["step_no"] != workflow[-1]["step_no"]+1:
                    print("the step_no of the nearest previous step must be 1 less than the step_no of the current step.")
                    print("e.g.")
                    print("\t\tfor the first firework, step_no=1")
                    print("\t\tfor the second firework, step_no=2")
                    print("\t\tfor the third firework, step_no=3")
                    print("\t\tfor the fourth firework, step_no=4")
                    raise Exception("See above for the error information")
                    
            assert "cal_name" in firework.keys(), "Error: you should name each calculation through tag cal_name!"
            firework["firework_folder_name"] = "step_" + str(firework["step_no"]) + "_" + firework["cal_name"].replace(" ", "_")
            
            if firework["step_no"] == 1:
                #Some tags must be specified in the first firework and they will be used for all fireworks.
                #firework["initial_vasp_input_set"] = firework.get("initial_vasp_input_set", "pymatgen")
                assert "job_query_command" in firework.keys(), "Error: must specify job_query_command in the first firework. (e.g. 'bjobs -w' on GRC)"
                assert "job_killing_command" in firework.keys(), "Error: must specify job_killing_command by job_killing_command in the first firework. (e.g. 'bkill' on GRC)"
                assert "where_to_parse_queue_id" in firework.keys(), "Error: must specify which file to parse queue id by where_to_parse_queue_id in the first firework. (e.g. if job_submission_command is 'bsub < vasp.lsf > job_id', it is 'job_id')"
                assert "re_to_parse_queue_id" in firework.keys(), "Error: must specify the regular expression by tag re_to_parse_queue_id to parse queue id in the first firework. (e.g. '<([0-9]+)>' on GRC)"
                firework["queue_stdout_file_prefix"] = firework.get("queue_stdout_file_prefix", "")
                firework["queue_stdout_file_suffix"] = firework.get("queue_stdout_file_suffix", "")
                firework["queue_stderr_file_prefix"] = firework.get("queue_stderr_file_prefix", "")
                firework["queue_stderr_file_suffix"] = firework.get("queue_stderr_file_suffix", "")
                pref_suf_sum = firework["queue_stdout_file_prefix"] + firework["queue_stdout_file_suffix"]
                pref_suf_sum += firework["queue_stderr_file_prefix"] + firework["queue_stderr_file_suffix"]
                if pref_suf_sum == "":
                    print("Error: must specify at least one of the tags below in the first firework:")
                    print("\t\tqueue_stdout_file_prefix, queue_stdout_file_suffix, queue_stderr_file_prefix, queue_stderr_file_suffix")
                    raise Exception("See above for the error information.")
                    
                firework["job_name"] = firework.get("job_name", "")
                
                if "vasp.out" not in firework.keys():
                    print("Error: vasp.out must be specified in the first firework")
                    print("\t\tIn the job submission script,")
                    print("\t\t\t\t-If vasp_cmd is 'mpirun -n 16 vasp_std > out', then vasp.out = out")
                    print("\t\t\t\t-If vasp_cmd is 'mpirun -n 16 vasp_ncl', then vasp.out=vasp.out")
                    raise Exception("Error: vasp.out must be specified in the first firework")
                
                if "force_gamma" in firework.keys():
                    if "y" in firework["force_gamma"].lower():
                        firework["force_gamma"] = True
                    else:
                        firework["force_gamma"] = False
                else:
                    firework["force_gamma"] = False
                    
                if "2d_system" in firework.keys():
                    if "y" in firework["2d_system"].lower():
                        firework["2d_system"] = True
                    else:
                        firework["2d_system"] = False
                else:
                    firework["2d_system"] = False
                    
                if "sort_structure" in firework.keys():
                    if "n" in firework["sort_structure"].lower():
                        firework["sort_structure"] = False
                    else:
                        firework["sort_structure"] = True
                else:
                    firework["sort_structure"] = True
                    
                #set the calculation folder, structure folder, max_running_job
                if "cal_folder" not in firework.keys():
                    firework["cal_folder"] = os.path.join(os.getcwd(), "cal_folder")
                
                assert "structure_folder" in firework.keys(), "Error: Must specify tag 'structure_folder' containing to-be-calculated structures in the first firework."
                assert os.path.isdir(firework["structure_folder"]), "Error: The directory specified by tag 'structure_folder' in the first firework below does not exist:\n\t\t{}".format("structure_folder")

                firework["max_running_job"] = int(firework.get("max_running_job", 30))
                
                   
                
            firework["copy_from_prev_cal"] = firework.get("copy_from_prev_cal", [])
            firework["move_from_prev_cal"] = firework.get("move_from_prev_cal", [])
            firework["contcar_to_poscar"] = firework.get("contcar_to_poscar", "no")
            if "y" in firework["contcar_to_poscar"].lower():
                firework["contcar_to_poscar"] = True
            else:
                firework["contcar_to_poscar"] = False
            firework["remove_after_cal"] = firework.get("remove_after_cal", [])
            firework["new_incar_tags"] = firework.get("new_incar_tags", {})
            firework["comment_incar_tags"] = firework.get("comment_incar_tags", [])
            firework["remove_incar_tags"] = firework.get("remove_incar_tags", [])
            firework["copy_from_prev_cal"] = firework.get("copy_from_prev_cal", [])
            if len(workflow) == 0:
                firework["copy_which_step"] = -1
            else:
                firework["copy_which_step"] = int(firework.get("copy_which_step", workflow[-1]["step_no"]))
            
            firework["extra_copy"] = firework.get("extra_copy", [])
            firework["final_extra_copy"] = firework.get("final_extra_copy", [])
            
            if "bader_charge" not in firework.keys():
                firework["bader_charge"] = False
            else:
                if "y" in firework["bader_charge"].lower():
                    firework["bader_charge"] = True
                else:
                    firework["bader_charge"] = False
            
            if "kpoints_type" not in firework.keys():
                print("\nYou don't set tag kpoints_type for step {}".format(firework["step_no"]))
                print("kpoints_type option: MPRelaxSet, MPStaticSet, MPNonSCFSet_line, MPNonSCFSet_uniform")
                print("\t\tFor MPRelaxSet, MPStaticSet, float denser_kpoints (default int 1) can be set to make kpoints denser")
                print("\t\tFor MPNonSCFSet_line, kpoints_line_density can be set. Default: 40")
                print("\t\tFor MPNonSCFSet_uniform, reciprocal_density can be set. Default: 1000\n")
                raise Exception("See above for the error information")
            elif firework["kpoints_type"] not in ["MPRelaxSet", "MPStaticSet", "MPNonSCFSet_line", "MPNonSCFSet_uniform", "Line-mode"]:
                raise Exception("kpoints_type must be one of MPRelaxSet, MPStaticSet, MPNonSCFSet_line, MPNonSCFSet_uniform or Line-mode @ step {}".format(firework["step_no"]))
                
            firework["reciprocal_density"] = int(firework.get("reciprocal_density", 1000))
            firework["kpoints_line_density"] = int(firework.get("kpoints_line_density", 40))
            firework["intersections"] = int(firework.get("intersections", 20))
            

            
            firework["denser_kpoints"] = firework.get("denser_kpoints", (1, 1, 1))
            if isinstance(firework["denser_kpoints"], str):
                firework["denser_kpoints"] = [float(k_multiple) for k_multiple in firework["denser_kpoints"].split(",") if k_multiple.strip()]
                assert len(firework["denser_kpoints"])==3, "Error: tag denser_kpoints must be three float/integer numbers separated by commas at step {}.".format(firework["step_no"])
            
            
            firework["user_defined_cmd"] = firework.get("user_defined_cmd", [])
            firework["final_user_defined_cmd"] = firework.get("final_user_defined_cmd", [])
            firework["user_defined_postprocess_cmd"] = firework.get("user_defined_postprocess_cmd", [])
        
            
            assert "job_submission_script" in firework.keys(), "Error: must specify job_submission_script for every calculation."
            assert "job_submission_command" in firework.keys(), "Error: must specify how to submit job for every calculation."
            
            firework = Read_Only_Dict.from_dict(firework)
            workflow.append(firework)
        elif line.startswith("*begin(add_new_incar_tags)"):
            new_incar_tags = {}
            while True:
                line = lines[line_ind]
                line_ind += 1
                if line.lower().startswith("*end(add_new_incar_tags)"):
                    firework["new_incar_tags"] = new_incar_tags
                    break
                        
                items = line.split("=")
                items = [item.strip() for item in items]
                if len(items) == 2:
                    new_incar_tags[items[0]] = items[1]
        else:
            items = lines[line_ind-1].split("=")
            items = [item.strip() for item in items]
            if "comment_incar_tags" in line:
                tags = [tag.strip().upper() for tag in items[1].split(",")]
                firework["comment_incar_tags"] = tags
            elif "remove_incar_tags" in line:
                tags = [tag.strip().upper() for tag in items[1].split(",")]
                firework["remove_incar_tags"] = tags
            elif "remove_after_cal" in line:
                files = [file.strip() for file in items[1].split(",")]
                firework["remove_after_cal"] = files
            elif "move_from_prev_cal" in line:
                files = [file.strip() for file in items[1].split(",")]
                firework["move_from_prev_cal"] = files
            elif "copy_from_prev_cal" in line:
                files = [file.strip() for file in items[1].split(",")]
                firework["copy_from_prev_cal"] = files
            elif "final_extra_copy" in line:
                files = [file.strip() for file in items[1].split(",")]
                for file in files:
                    assert os.path.isfile(file), "Error: file {} specifized in tag final_extra_copy does not exists.".format(file)
                firework["final_extra_copy"] = files
            elif "extra_copy" in line:
                files = [file.strip() for file in items[1].split(",")]
                for file in files:
                    assert os.path.isfile(file), "Error: file {} specifized in tag extra_copy does not exists.".format(file)
                firework["extra_copy"] = files
            elif "kpoints_type" in line:
                firework["kpoints_type"] = items[1]
            elif "final_user_defined_cmd" in line:
                firework["final_user_defined_cmd"] = [cmd_.strip().replace("@", " ") for cmd_ in items[1].split(",") if cmd_.strip()]
            elif "user_defined_cmd" in line:
                firework["user_defined_cmd"] = [cmd_.strip().replace("@", " ") for cmd_ in items[1].split(",") if cmd_.strip()]
            elif "user_defined_postprocess_cmd" in line:
                firework["user_defined_postprocess_cmd"] = [cmd_.strip().replace("@", " ") for cmd_ in items[1].split(",") if cmd_.strip()]
            else:
                firework[items[0].lower()] = items[1]
                    
    return workflow              


# In[3]:


def parse_firework_block(block_str_list, step_no):
    """
    parse the calculation setup for a firework.
    """
    firework = {"new_incar_tags":{}}
    
    for line in block_str_list:
        if line.count("=") != 1 and "*begin(add_new_incar_tags)" not in line.lower() and "*end(add_new_incar_tags)" not in line.lower():
            raise Exception("Each line is supposed to have only one '=', while the line below has {}\n{}\n".format(line.count("="), line))
    
    incar_subblock = False
    for line in block_str_list:            
        if line.lower().startswith("*begin(add_new_incar_tags)"):
            incar_subblock = True
        elif line.lower().startswith("*end(add_new_incar_tags)"):
            incar_subblock = False
        else:
            tag, value = [item.strip() for item in line.split("=")]
            if incar_subblock:
                firework["new_incar_tags"][tag.upper()] = value
            else:
                firework[tag.lower()] = value
    
    #Check the validity of the setting and assign default values to unspecified tags
    
    #1. step_no and calculation name
    if "step_no" in firework.keys():
        if step_no == int(firework["step_no"]):
            firework["step_no"] = step_no
        else:
            print("\n")
            print("*"*20)
            print("step_no of firework {} must be set to {}.".format(step_no, step_no))
            print("Please change step_no to {} in the line below:".format(step_no))
            print("{}".format(line))
            print('*'*20)
            print("\n")
            raise Exception("See above for the error information")
    else:
        raise Exception("tag step_no is required for every firework. Please set step_n={} for firework {}".format(step_no, step_no))
    assert "cal_name" in firework.keys(), "Error: you should name each firework through tag cal_name!"
    firework["firework_folder_name"] = "step_" + str(step_no) + "_" + firework["cal_name"].replace(" ", "_")
         
        
    #2. tags involved in copying
    firework["copy_from_prev_cal"] = firework.get("copy_from_prev_cal", "")
    firework["copy_from_prev_cal"] = [item.strip() for item in firework["copy_from_prev_cal"].split(",") if item.strip()]
    if "copy_which_step" in firework.keys():
        firework["copy_which_step"] = int(firework["copy_which_step"])
        if firework["copy_which_step"] < 1 or firework["copy_which_step"]  >= step_no:
            raise Exception("step {}: tag copy_which_step should be >=1 and <{}".format(step_no, step_no))
    else:
        if step_no == 1:
            firework["copy_which_step"] = -1
        else:
            firework["copy_which_step"] = step_no -1
    for tag in ["extra_copy", "final_extra_copy"]:
        firework[tag] = firework.get(tag, "")
        file_list = [file_.strip() for file_ in firework[tag].split(",") if file_.strip()]
        for file_ in file_list:
            assert os.path.isfile(file_), "the file below listed in tag {} doesn't exist.\n\t\t\t{}\n".format(tag, file_)
        firework[tag] = file_list

       
    
    #3. tags involved in moving, removing and renaming
    for tag in ["move_from_prev_cal", "remove_after_cal"]:
        firework[tag] = firework.get(tag, "")
        firework[tag] = [item.strip() for item in firework[tag].split(",") if item.strip()]
    firework["contcar_to_poscar"] = firework.get("contcar_to_poscar", "No").lower()
    firework["contcar_to_poscar"] = True if "y" in firework["contcar_to_poscar"] else False
               
        
    #4. INCAR related tags
    for tag in ["comment_incar_tags", "remove_incar_tags"]:
        firework[tag] = firework.get(tag, "")
        firework[tag] = [item.strip().upper() for item in firework[tag].split(",") if item.strip()]
    
    firework["bader_charge"] = firework.get("bader_charge", "No").lower()
    firework["bader_charge"] = True if "y" in firework["bader_charge"] else False
        
        
    #5. KPOINTS related tags
    if "kpoints_type" not in firework.keys():
        print("\nYou don't set tag kpoints_type for step {}".format(step_no))
        print("kpoints_type option: MPRelaxSet, MPStaticSet, MPNonSCFSet_line, MPNonSCFSet_uniform, Line-mode")
        print("\t\tFor MPRelaxSet, MPStaticSet, float denser_kpoints (three float/int numbers) can be set to make kpoints denser. Default: 1, 1, 1")
        print("\t\tFor MPNonSCFSet_line, kpoints_line_density can be set. Default: 40")
        print("\t\tFor MPNonSCFSet_uniform, reciprocal_density can be set. Default: 1000")
        print("\t\tFor Line-mode, intersections can be set. Default: 20\n")
        raise Exception("See above for the error information")
    elif firework["kpoints_type"] not in ["MPRelaxSet", "MPStaticSet", "MPNonSCFSet_line", "MPNonSCFSet_uniform", "Line-mode"]:
        raise Exception("kpoints_type must be one of MPRelaxSet, MPStaticSet, MPNonSCFSet_line, MPNonSCFSet_uniform or Line-mode @ step {}".format(step_no))
                
    firework["reciprocal_density"] = int(firework.get("reciprocal_density", 1000))
    firework["kpoints_line_density"] = int(firework.get("kpoints_line_density", 40))
    firework["intersections"] = int(firework.get("intersections", 20))
         
    firework["denser_kpoints"] = firework.get("denser_kpoints", (1, 1, 1))
    if isinstance(firework["denser_kpoints"], str):
        firework["denser_kpoints"] = [float(k_multiple) for k_multiple in firework["denser_kpoints"].split(",") if k_multiple.strip()]
        assert len(firework["denser_kpoints"])==3, "Error: tag denser_kpoints must be three float/integer numbers separated by commas at step {}.".format(step_no)           
       
    
    #6. cmd defined by users
    for tag in ["user_defined_cmd", "final_user_defined_cmd", "user_defined_postprocess_cmd"]:
        if tag in firework.keys(): 
            firework[tag] = [cmd_.strip() for cmd_ in firework[tag].split(",") if cmd_.strip()]
        else:
            firework[tag] = []
      

        
    #7. job submissions
    assert "job_submission_script" in firework.keys(), "Error: must specify job_submission_script for every firework."
    assert os.path.isfile(firework["job_submission_script"]), "Step {}: the specified job submission script does not exist.".format(step_no)
    assert "job_submission_command" in firework.keys(), "Error: must specify how to submit a job for every firework."
    
      
        
    #tags only required for the first firework
    if step_no == 1:
        assert "job_query_command" in firework.keys(), "Error: must specify job_query_command in the first firework. (e.g. 'bjobs -w' on GRC)"
        assert "job_killing_command" in firework.keys(), "Error: must specify job_killing_command by job_killing_command in the first firework. (e.g. 'bkill' on GRC)"
        assert "where_to_parse_queue_id" in firework.keys(), "Error: must specify which file to parse queue id by where_to_parse_queue_id in the first firework. (e.g. if job_submission_command is 'bsub < vasp.lsf > job_id', it is 'job_id')"
        assert "re_to_parse_queue_id" in firework.keys(), "Error: must specify the regular expression by tag re_to_parse_queue_id to parse queue id in the first firework. (e.g. '<([0-9]+)>' on GRC)"
        firework["queue_stdout_file_prefix"] = firework.get("queue_stdout_file_prefix", "")
        firework["queue_stdout_file_suffix"] = firework.get("queue_stdout_file_suffix", "")
        firework["queue_stderr_file_prefix"] = firework.get("queue_stderr_file_prefix", "")
        firework["queue_stderr_file_suffix"] = firework.get("queue_stderr_file_suffix", "")
        pref_suf_sum = firework["queue_stdout_file_prefix"] + firework["queue_stdout_file_suffix"]
        pref_suf_sum += firework["queue_stderr_file_prefix"] + firework["queue_stderr_file_suffix"]
        if pref_suf_sum == "":
            print("Error: must specify at least one of the tags below in the first firework:")
            print("\t\tqueue_stdout_file_prefix, queue_stdout_file_suffix, queue_stderr_file_prefix, queue_stderr_file_suffix")
            raise Exception("See above for the error information.")
         
        firework["job_name"] = firework.get("job_name", "")
        
        if "vasp.out" not in firework.keys():
            print("Error: vasp.out must be specified in the first firework")
            print("\t\tIn the job submission script,")
            print("\t\t\t\t-If vasp_cmd is 'mpirun -n 16 vasp_std > out', then vasp.out = out")
            print("\t\t\t\t-If vasp_cmd is 'mpirun -n 16 vasp_ncl', then vasp.out=vasp.out")
            raise Exception("Error: vasp.out must be specified in the first firework")
        
        firework["force_gamma"] = firework.get("force_gamma", "No").lower()
        firework["2d_system"] = firework.get("2d_system", "No").lower()
        firework["sort_structure"] = firework.get("sort_structure", "Yes").lower()
        for tag in ["force_gamma", "2d_system", "sort_structure"]:
            firework[tag] = True if 'y' in firework[tag] else False
                
                    
        #set the calculation folder, structure folder, max_running_job
        if "cal_folder" not in firework.keys():
            firework["cal_folder"] = os.path.join(os.getcwd(), "cal_folder")
                
        assert "structure_folder" in firework.keys(), "Error: Must specify tag 'structure_folder' containing to-be-calculated structures in the first firework."
        assert os.path.isdir(firework["structure_folder"]), "Error: The directory specified by tag 'structure_folder' in the first firework below does not exist:\n\t\t{}".format("structure_folder")

        firework["max_running_job"] = int(firework.get("max_running_job", 30))
        assert firework["max_running_job"] >= 0, "tag max_running_job must be 0 or a positive integer."
                
                   
    return Read_Only_Dict.from_dict(firework)                  


# workflow = parse_calculation_workflow("Calculation_setup_GRC")
# workflow[0]

# workflow[4]
