from fsspec import AbstractFileSystem
from TM1py import TM1Service
import io
from airflow_provider_tm1.hooks.tm1 import TM1Hook 
import logging 

from fsspec import AbstractFileSystem 
from TM1py import TM1Service
import io
from TM1py.Utils.Utils import verify_version
from TM1py.Services.FileService import FileService
import weakref


log = logging.getLogger(__name__)

def get_fs(conn_id: str | None = None, storage_options: dict | None = None) -> AbstractFileSystem:
    if conn_id is None:
        conn_id = TM1Hook.default_conn_name
    tm1_hook = TM1Hook(tm1_conn_id=conn_id)
    tm1_service = tm1_hook.get_conn()
    fs = TM1BlobStorage(tm1_service=tm1_service, owns_service=True, **(storage_options or {}))
    return fs

def _refine_path_for_v11(path: str, tm1_service: TM1Service) -> str:
    """Refine the path for TM1 version 11 and above."""
    
    if verify_version(required_version=FileService.SUBFOLDER_REQUIRED_VERSION, version=tm1_service.version):
        #* v12 may allow subfolders, so we do not need to change the path
        return path 
    
    if not path.startswith('/'):
        #* If the path does not start with '/', we assume it is a absolute path
        return path

    if not path.startswith('//'):
        #* only care about paths that start with a single '/', like '/myfile.txt'
        return path[1:]
    
    return path

class TM1Blob(io.BytesIO):
    def __init__(self, buffer: bytes, tm1_service: TM1Service, path: str, mode='rb'):
        super().__init__(buffer)
        self._tm1 = tm1_service
        self._path = path
        self._mode = mode
    
    def __exit__(self, exc_type, exc_value, traceback):
        """Context manager exit method."""
        self._tm1.files.update_or_create(self._path, self.getvalue())

class TM1BlobStorage(AbstractFileSystem):
    """A file system for TM1 that allows interaction with TM1 objects as files."""
    protocol = ('tm1', )
    def __init__(self, tm1_service: TM1Service, owns_service=False, **kwargs):
        super().__init__(**kwargs)
        self._tm1: TM1Service = tm1_service
        self._owns_service = owns_service
        if self._owns_service:
            self._finalizer = weakref.finalize(self, self._cleanup_tm1_service, self._tm1)
        else:
            self._finalizer = None
            
    @staticmethod
    def _cleanup_tm1_service(tm1_service):        
        try:
            if tm1_service and hasattr(tm1_service, 'logout'):
                log.debug("Finalizer cleaning up TM1 service")
                tm1_service.logout()
        except Exception as e:
            log.warning(f"Finalizer cleanup failed: {e}")
    
    def _refine_path(self, path: str) -> str:
        """Central path refinement for all operations."""
        return _refine_path_for_v11(path, self._tm1)
    
    def _strip_protocol(self, path):
        """Override to apply path refinement at the protocol level."""
        path = super()._strip_protocol(path)
        return self._refine_path(path)
        
    def exists(self, path, **kwargs):
        """Check if a file exists in TM1."""
        assert self._tm1, "TM1Service instance is not registered."
        refined_path = self._refine_path(path)
        log.debug(f"Checking existence of path: {refined_path}")
        return self._tm1.files.exists(refined_path)

    def ls(self, path, detail=True, **kwargs):
        """List files in a given TM1 path."""
        assert self._tm1, "TM1Service instance is not registered."
        
        log.debug(f"Listing files in path: {path}")
        if not self._tm1:
            raise ValueError("TM1Service instance is not registered. Use register_tm1_service() to set it.")
        if path == '/':
            return self._tm1.files.get_all_names()
        
        refined_path = _refine_path_for_v11(path, self._tm1)
        return self._tm1.files.get_all_names(refined_path) if not detail else [self.info(file_path) for file_path in self._tm1.files.get_all_names(refined_path)]

    def info(self, path, **kwargs):
        """Get information about a file in TM1."""
        assert self._tm1, "TM1Service instance is not registered."
        refined_path = self._refine_path(path)
        log.debug(f"Getting info for path: {refined_path}")
        if not self._tm1:
            raise ValueError("TM1Service instance is not registered. Use register_tm1_service() to set it.")
        return {'name': refined_path, 'size': 0, 'type': 'file'}
    
    def open(self, path, mode='rb', **kwargs):
        """Open a file in TM1."""
        assert self._tm1, "TM1Service instance is not registered."
        log.debug(f"Opening file: {path} in mode: {mode}")
        refined_path = self._refine_path(path)
        if not self._tm1:
            raise ValueError("TM1Service instance is not registered. Use register_tm1_service() to set it.")
        if mode not in ['rb', 'wb']:
            raise ValueError("Mode must be 'rb' or 'wb'.")

        if not self._tm1.files.exists(refined_path):
            if mode == 'rb':
                raise FileNotFoundError(f"File {refined_path} does not exist in TM1.")
            data = b''
        else:
            data = self._tm1.files.get(refined_path)

        return TM1Blob(data, self._tm1, refined_path, mode)

    def _rm(self, path, **kwargs):
        """Remove a file in TM1."""
        assert self._tm1, "TM1Service instance is not registered."
        refined_path = _refine_path_for_v11(path, self._tm1)
        log.debug(f"Removing file: {refined_path}")
        if not self._tm1:
            raise ValueError("TM1Service instance is not registered. Use register_tm1_service() to set it.")
        self._tm1.files.delete(refined_path)
