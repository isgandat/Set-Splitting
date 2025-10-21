import os
import subprocess
import sys

# Helper to write CNF in DIMACS format
def write_dimacs(clauses, num_vars):
    dimacs = f"p cnf {num_vars} {len(clauses)}\n"
    for clause in clauses:
        dimacs += " ".join(map(str, clause)) + " 0\n"
    return dimacs   

# Set Splitting Problem instance encoding
def encode_set_splitting(universe, subsets):
    clauses = []
    variable_map = {}
    var_counter = 1

    # Mapping each element to a unique variable
    for elem in universe:
        variable_map[elem] = var_counter
        var_counter += 1

    # Ensuring at least one element in each subset is true
    for subset in subsets:
        clause = [variable_map[elem] for elem in subset]
        clauses.append(clause)

    # Ensuring no two elements in the same subset are both true
    for subset in subsets:
        for i in range(len(subset)):
            for j in range(i + 1, len(subset)):
                clauses.append([-variable_map[subset[i]], -variable_map[subset[j]]])

    return clauses, var_counter - 1, variable_map

# SAT solver interface
def solve_cnf_with_glucose(cnf_content):
    try:
        result = subprocess.run(
            ["glucose", "-model"],
            input=cnf_content,
            text=True,
            capture_output=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"SAT solver failed: {e.stderr or str(e)}")

# Parse SAT solver output
def parse_solution(output, variable_map):
    if "UNSAT" in output:
        return "No solution exists (UNSAT)."

    assignments = []
    for line in output.splitlines():
        if line.startswith("v "): 
            assignments.extend(map(int, line[2:].split()))

    if not assignments:
        raise ValueError("No variable assignment line found in SAT solver output.")

    solution = {
        elem: (assignments[variable_map[elem] - 1] > 0) for elem in variable_map
    }
    return solution

# Main script
def main(input_file, output_cnf=False, print_output=False):
    with open(input_file, "r") as f:
        lines = f.readlines()
    universe = list(map(int, lines[0].split()))
    subsets = [list(map(int, line.split())) for line in lines[1:]]

    clauses, num_vars, variable_map = encode_set_splitting(universe, subsets)
    cnf_content = write_dimacs(clauses, num_vars)

    if output_cnf:
        print("CNF content:")
        print(cnf_content)
        return

    try:
        result = solve_cnf_with_glucose(cnf_content)

        if print_output:
            print("Raw Glucose Output:")
            print(result)

        solution = parse_solution(result, variable_map)
        print("Solution:", solution)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "_main_":
    if len(sys.argv) < 2:
        print("Usage: python set_splitting.py <input_file> [--output-cnf] [--print-output]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_cnf = "--output-cnf" in sys.argv
    print_output = "--print-output" in sys.argv

    main(input_file, output_cnf, print_output)