from typing import Any

from airflow.sdk.bases.operator import BaseOperator
from airflow.sdk.definitions.context import Context
from airflow.exceptions import AirflowException

from airflow_provider_tm1.hooks.tm1 import TM1Hook

class TM1MDXChunkOperator(BaseOperator):
    """
    This operator executes an MDX query in chunks.

    :param mdx: Valid MDX Query
    :param chunk_size: Size of each chunk to be processed
    :param tm1_conn_id: The Airflow connection used for TM1 credentials.
    :param skip_chunk_process: If True, skips processing of chunks and only returns the MDX query.
    """
    
    default_conn_name = 'tm1_default'
    ui_color = '#BDDDEF'
    ui_fgcolor = '#434b53'
    
    def __init__(
        self,
        mdx: str,
        chunk_size: int = 1000,
        tm1_conn_id: str = default_conn_name,
        skip_chunk_process: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.mdx = mdx
        self.chunk_size = chunk_size
        self.tm1_conn_id = tm1_conn_id
        self.skip_chunk_process = skip_chunk_process
    
    def execute(self, context: Context): 
        from airflow_provider_tm1.utils.mdx_alchemy.optimizer import chunk_query
        from airflow_provider_tm1.utils.mdx_alchemy import mdx_to_mdx_builder
        hook = TM1Hook(tm1_conn_id=self.tm1_conn_id)
        if self.skip_chunk_process:
            self.log.info("Skipping chunk processing. Returning MDX query.")
            return [mdx_to_mdx_builder(self.mdx).to_mdx()]
        with hook.get_conn() as tm1:
            try:
                result = chunk_query(tm1, self.mdx, self.chunk_size)
                self.log.info("MDX query executed successfully in chunks.")
                return result
            except Exception as e:
                self.log.error("Error executing MDX query in chunks: %s", e)
                raise AirflowException(f"Failed to execute MDX query in chunks: {e}")
