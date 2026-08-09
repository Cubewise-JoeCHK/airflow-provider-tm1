import subprocess

import pytest

container_name = "tests_integration-airflow-worker-1"


@pytest.fixture(autouse=True)
def setup_before_test(request):
    print("=============================================")
    print("Executing ", request.node.name)
    print("=============================================")


def run_docker_exec(command):

    result = subprocess.run(
        ["docker", "exec", container_name] + command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    output = result.stdout.decode("utf-8")
    print(output)

    return result, output


def assert_airflow_dag_log_contains(string, output):
    assert string in output, output


def assert_airflow_dag_completed(result):
    assert result.returncode == 0


def assert_airflow_dag_failed(result):
    assert result.returncode == 1


# NOTE: the previous assert_tm1server_log_contains() helper read a local
# tm1server.log from the volume-mounted TM1 container. TM1 is now an external
# persistent instance (airflow-provider-ci.joechowhk.internal), so that file is
# not available in CI. The process-execution status + error details are already
# surfaced by the Airflow operator output, which these DAG-output assertions
# check.


def test_airflow_test_success_dag():

    command = "airflow dags test airflow_test_success_dag"
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)
    assert_airflow_dag_log_contains("Process executed successfully. Status: CompletedSuccessfully", output)


def test_airflow_test_params_success_dag():

    command = "airflow dags test airflow_test_params_success_dag"
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)
    assert_airflow_dag_log_contains("Process executed successfully. Status: CompletedSuccessfully", output)


def test_airflow_test_aborted_dag():

    command = "airflow dags test airflow_test_aborted_dag"
    result, output = run_docker_exec(command)

    assert_airflow_dag_failed(result)
    assert_airflow_dag_log_contains("Process execution failed. Status: Aborted", output)


def test_ariflow_test_data_error_dag():

    command = "airflow dags test airflow_test_data_error_dag"
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)
    assert_airflow_dag_log_contains("Process executed with minor errors. Status: HasMinorErrors", output)


def test_airflow_test_timeout_dag():

    command = "airflow dags test airflow_test_timeout_dag"
    result, output = run_docker_exec(command)

    assert_airflow_dag_failed(result)
    assert_airflow_dag_log_contains("Timeout after 3 seconds", output)


def test_airflow_test_execute_mdx():
    command = "airflow dags test airflow_test_execute_mdx"
    result, output = run_docker_exec(command)

    assert_airflow_dag_log_contains("test1 dim values:['test1_dim1' 'test_dim2' 'test1_dim3']", output)
    assert_airflow_dag_log_contains("test2 dim values:['test2_dim2' 'test2_dim2' 'test2_dim2']", output)


def test_airflow_test_execute_mdx_mapreduce():
    command = "airflow dags test airflow_test_execute_mdx_mapreduce"
    result, output = run_docker_exec(command)

    assert_airflow_dag_log_contains("test1 dim values:['test1_dim1' 'test_dim2' 'test1_dim3']", output)
    assert_airflow_dag_log_contains("test2 dim values:['test2_dim2' 'test2_dim2' 'test2_dim2']", output)
    assert_airflow_dag_log_contains("Returned dataframe size: 2", output)


def test_airflow_test_dry_run():
    command = "airflow dags test airflow_test_dry_run_dag"
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)
    assert_airflow_dag_log_contains(
        "Triggering TM1 airflow_test_success in dry-run mode with timeout 300 with parameters  {'async_request_mode': True}",
        output,
    )


def test_airflow_filesystem_dag():
    command = "airflow dags test tm1_filesystem_example"
    result, output = run_docker_exec(command)

    assert_airflow_dag_completed(result)
    assert_airflow_dag_log_contains("Sample output file written to TM1", output)
    assert_airflow_dag_log_contains("stat: size=", output)
    assert_airflow_dag_log_contains("Copied", output)
    assert_airflow_dag_log_contains("test_file_copy.txt", output)


if __name__ == "__main__":
    pytest.main()
