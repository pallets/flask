branch_coverage = {
    "get_send_file_max_age_1": False, 
    "get_send_file_max_age_2": False,
    "get_send_file_max_age_3": False, 
    "dispatch_request_1": False,
    "dispatch_request_2": False,
    "dispatch_request_3": False,
}

def track_coverage(branch_name):
    global branch_coverage
    branch_coverage[branch_name] = True