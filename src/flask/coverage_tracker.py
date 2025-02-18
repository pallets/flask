# coverage_tracker.py
branch_coverage = {}
total_run_branches = 20
for i in range(1, total_run_branches + 1):
    branch_coverage[i] = 0

def mark_branch(branch_id):
    branch_coverage[branch_id] += 1

