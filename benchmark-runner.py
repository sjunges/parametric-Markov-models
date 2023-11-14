import argparse
import os.path
import sys
import logging
import subprocess

logger = logging.getLogger(__file__)
FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT, stream=sys.stdout, level=logging.INFO)


class Benchmark:
    def __init__(self, benchmark_path, model_name, property_name, constants = {}):
        self.benchmark_path = benchmark_path
        self.model_name = model_name
        self.property_name = property_name
        self.constants = constants

    @property
    def model_path(self):
        return os.path.join(self.benchmark_path, self.model_name)

    @property
    def property_path(self):
        if self.property_name.endswith(".pctl"):
          return os.path.join(self.benchmark_path, self.property_name)
        return self.property_name

    def __str__(self):
        return f"<Benchmark:{self.benchmark_path}/{self.model_name}&{self.property_name},{self.constants}>"


class FeasibilityQuery:
    def __init__(self, direction : str|None = None, threshold : float|None = None, graph_epsilon = 0.0, guarantee_precision = None):
        self.direction = direction
        self.threshold = threshold
        self.graph_epsilon = graph_epsilon
        self.guarantee_precision = guarantee_precision

    def __str__(self):
        return f"<FeasibilityQuery:dir={self.direction},threshold={self.threshold},eps={self.graph_epsilon},guarantee={self.guarantee_precision}>"


class VerificationQuery:
    def __init__(self, graph_epsilon = 0.05):
        self.graph_epsilon = graph_epsilon

    def __str__(self):
        return f"<VerificationQuery:eps={self.graph_epsilon}>"


class SolutionFunctionQuery:
    def __init__(self):
        pass


class StormConfig:
    def __init__(self, path : str, arguments : list[str] = [], feasibility_method = None, config_name="storm"):
        self.path = path
        self.arguments = arguments
        self.feasibility_method = feasibility_method
        self._config_name = config_name

    def specify_model(self, path : str) -> list[str]:
        if path.endswith(".jani"):
            return ["--jani", path]
        return ["--prism", path]

    def specify_property(self, path : str) -> list[str]:
        return ["--prop", path]

    def query_dependent_arguments(self, query) -> list[str]:
        if not isinstance(query,SolutionFunctionQuery) and query.graph_epsilon != 0.0:
            region_selection = ["--regionbound", str(query.graph_epsilon)]
        else:
            region_selection = []

        return self._mode_selection(query) + region_selection

    def _mode_selection(self, query) -> list[str]:
        if isinstance(query, FeasibilityQuery):
            if query.guarantee_precision is not None:
                guarantee = ["--guarantee", str(query.guarantee_precision), "rel"]
            else:
                guarantee = []
            if query.direction is not None:
                direction = ["--direction", query.direction]
            else:
                direction = []
            return ["--mode", "feasibility", "--feasibility:method", self.feasibility_method] + direction + guarantee
        if isinstance(query, VerificationQuery):
            return ["--mode", "verification"]
        if isinstance(query, SolutionFunctionQuery):
            return ["--mode", "solutionfunction"]
        raise RuntimeError("unexpected")

    def specify_constants(self, constants : dict[str, str]):
        if len(constants) == 0:
            return []
        return ["-const", ",".join([f"{k}={v}" for k,v in constants.items()])]

    def __str__(self):
        return f"<Config:{self._config_name}>"


def create_benchmarks_with_varying_constants(path, modelfile, propertyfile, constants, query) -> list[tuple[Benchmark,FeasibilityQuery]]:
    return [(Benchmark(path, modelfile, propertyfile, c), query) for c in constants]


def run_benchmark(benchmark, query, tool_config):
    """

    :param benchmark:
    :param query:
    :param tool_config:
    :return:
    """
    invocation = [tool_config.path] + tool_config.query_dependent_arguments(query) + tool_config.arguments + tool_config.specify_model(benchmark.model_path) + tool_config.specify_property(benchmark.property_path) + tool_config.specify_constants(benchmark.constants)
    logger.info("Running " + " ".join(invocation))
    tool_call = subprocess.Popen(invocation, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, errors = tool_call.communicate()
    tool_call.wait()
    error = False
    if (len(errors)) > 0:
        error = True
        logger.error(errors)
    if tool_call.returncode > 0:
        error = True
    logger.debug(output)
    if error:
        logger.warning("Produced an error!")
        return False
    else:
        logger.info("Done sucesfully!")
        return True


def create_solution_function_benchmarks() -> list[tuple[Benchmark, SolutionFunctionQuery]]:
    return create_benchmarks_with_varying_constants("pmc/brp", "brp.pm", "P=? [F \"target\"]", [{"N": "16", "MAX": "2"}],
                                             SolutionFunctionQuery()) + \
            create_benchmarks_with_varying_constants("pmc/crowds", "crowds.pm", "P=? [F observe0>1 ]",
                                             [{"CrowdSize": "3", "TotalRuns": "3"}], SolutionFunctionQuery()) + \
            create_benchmarks_with_varying_constants("pmc/egl", "egl.pm", "R{\"messages_A_needs\"}=? [ F phase=4 ];",
                                             [{"N": 2, "L": 2}],
                                             SolutionFunctionQuery()) + \
            create_benchmarks_with_varying_constants("pmc/herman", "herman3.pm", "R=? [F \"stable\" ]", [{}],
                                             SolutionFunctionQuery()) + \
            create_benchmarks_with_varying_constants("pmc/nand", "nand.pm", "P=? [F \"target\" ]", [{"N": "5", "K": 5}],
                                             SolutionFunctionQuery()) + \
            create_benchmarks_with_varying_constants("pmc/zeroconf", "zeroconf.pm", "P=? [F s=n+1 ]", [{"n": "10"}],
                                             SolutionFunctionQuery())


def create_test_pmc_feas_gd_benchmarks() -> list[tuple[Benchmark, FeasibilityQuery]]:
    return create_benchmarks_with_varying_constants("pmc/brp", "brp.pm", "P<=0.01 [F \"target\"]", [{"N": "32", "MAX": "5"}], FeasibilityQuery()) + \
           create_benchmarks_with_varying_constants("pmc/crowds", "crowds.pm", "P>0.9 [F observe0>1 ]", [{"CrowdSize": "5", "TotalRuns" : "5"}], FeasibilityQuery()) + \
           create_benchmarks_with_varying_constants("pmc/egl", "egl.pm", "R{\"messages_A_needs\"}<=1.6 [ F phase=4 ];", [{"N": 4, "L": 4}],
                                                    FeasibilityQuery()) + \
           create_benchmarks_with_varying_constants("pmc/herman", "herman7.pm", "R<=10 [F \"stable\" ]", [{}], FeasibilityQuery()) + \
           create_benchmarks_with_varying_constants("pmc/nand", "nand.pm", "P<=0.03 [F \"target\" ]", [{"N": "5", "K": 5}], FeasibilityQuery()) + \
           create_benchmarks_with_varying_constants("pmc/zeroconf", "zeroconf.pm", "P>=0.9 [F s=n+1 ]", [{"n": "100"}], FeasibilityQuery())


TEST_PMDP_FEAS_BENCHMARKS = [(Benchmark("pmdp/consensus", "consensus2.nm", "R{\"steps\"}min=? [ F \"finished\" ]", {"K" : 2}), FeasibilityQuery(direction="min", graph_epsilon=0.03, guarantee_precision=0.01)),
                             (Benchmark("pmdp/csma", "csma2-2.nm", "time.pctl"), FeasibilityQuery(direction="max", graph_epsilon=0.03, guarantee_precision=0.1))] + \
                              create_benchmarks_with_varying_constants("pmdp/routing", "routing.nm", "Rmin>=0.3 [F \"done\"]" , [{"N": "2", "Z": "2", "M": "2"}], FeasibilityQuery(graph_epsilon=0.03)) + \
                              create_benchmarks_with_varying_constants("pmdp/hotelroom", "room.nm", "room.pctl", [{"N": "5"}], FeasibilityQuery("min", None, graph_epsilon=0.03, guarantee_precision=0.01))# + \

# TODO this benchmark times out with the current storm setup. (Benchmark("pmdp/drone-weather", "drone.nm", "drone.prctl"), FeasibilityQuery(direction="max", graph_epsilon=0.03, guarantee_precision=0.9))]


TEST_PMDP_VERIF_BENCHMARKS = create_benchmarks_with_varying_constants("pmdp/routing", "routing.nm", "Rmin>=0.3 [F \"done\"]" , [{"N": "2", "Z": "2", "M": "2"}], VerificationQuery(graph_epsilon=0.03)) + \
                              create_benchmarks_with_varying_constants("pmdp/routing", "routing.nm", "Rmin<=0.2 [F \"done\"]" , [{"N": "8", "Z": "4", "M": "4"}], VerificationQuery(graph_epsilon=0.03)) + \
                              create_benchmarks_with_varying_constants("pmdp/hotelroom", "room.nm", "room.pctl", [{"N": "20"}], VerificationQuery(graph_epsilon=0.03))


def main():
    parser = argparse.ArgumentParser(
        prog='ParametricModelBenchmarkRunner',
        description='Analyzes parametric Markov model through a model checker')
    parser.add_argument("path_to_storm")
    args = parser.parse_args()
    collected_errors = []

    storm_config = StormConfig(args.path_to_storm, feasibility_method="gd", config_name="StormGD")
    i = 1
    for entry in create_solution_function_benchmarks() + create_test_pmc_feas_gd_benchmarks():
        print(i)
        benchmark, query = entry[0], entry[1]
        success = run_benchmark(benchmark, query, storm_config)
        if not success:
            collected_errors.append((i,benchmark,query,storm_config))
        print("******")
        i+=1
    storm_config = StormConfig(args.path_to_storm, feasibility_method="pla", config_name="StormPLA")
    for entry in TEST_PMDP_FEAS_BENCHMARKS + TEST_PMDP_VERIF_BENCHMARKS:
        print(i)
        benchmark, query = entry[0], entry[1]
        success = run_benchmark(benchmark, query, storm_config)
        if not success:
            collected_errors.append((i,benchmark,query,storm_config))
        print("******")
        i += 1
    for ce in collected_errors:
        print("" + str(ce[0]) + ":" + str(ce[1]) + "," + str(ce[2]) + "," + str(ce[3]))

if __name__ == "__main__":
    main()