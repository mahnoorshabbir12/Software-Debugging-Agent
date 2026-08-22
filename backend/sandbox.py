import os
import tarfile
import io
import docker
from docker.errors import DockerException

class DockerSandbox:
    def __init__(self, image: str = "python:3.11-slim"):
        self.image = image
        try:
            self.client = docker.from_env()
        except DockerException as e:
            raise RuntimeError(f"Could not connect to Docker daemon. Is Docker running? Error: {e}")
        
        self.container = None

    def create_sandbox(self, project_root: str):
        """
        Spins up a locked-down container and copies the project into it.
        """
        # Ensure the image exists
        try:
            self.client.images.get(self.image)
        except docker.errors.ImageNotFound:
            print(f"Pulling image {self.image}...")
            self.client.images.pull(self.image)

        # Create container with strict resource limits and NO network
        self.container = self.client.containers.run(
            self.image,
            command="tail -f /dev/null", # Keep it running
            detach=True,
            network_mode="none", # Disconnect from internet
            mem_limit="512m", # Restrict memory
            cpu_period=100000,
            cpu_quota=50000, # Max 50% of 1 CPU
            working_dir="/app"
        )
        
        # Copy the project into the container
        self._copy_to_container(project_root, "/app")

    def _copy_to_container(self, src: str, dst: str):
        """Helper to copy a local directory into the container using a tar stream."""
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode='w') as tar:
            # We use arcname='.' so the contents of src are placed at the root of the tar
            tar.add(src, arcname='.')
        
        stream.seek(0)
        
        # Create dst directory in container if it doesn't exist
        self.container.exec_run(f"mkdir -p {dst}")
        
        # Put the archive directly into dst
        self.container.put_archive(dst, stream)

    def run_command(self, cmd: str, timeout: int = 10) -> tuple[int, str]:
        """
        Executes a command inside the sandbox.
        Returns (exit_code, output).
        """
        if not self.container:
            raise RuntimeError("Sandbox is not running. Call create_sandbox() first.")
            
        # We run the command via exec_run
        # The docker SDK doesn't natively support timeout for exec_run easily,
        # so we wrap the command in a `timeout` shell command.
        wrapped_cmd = f"timeout {timeout} {cmd}"
        
        exit_code, output = self.container.exec_run(
            ["sh", "-c", wrapped_cmd],
            workdir="/app"
        )
        
        return exit_code, output.decode('utf-8', errors='replace')

    def cleanup(self):
        """Stops and removes the container."""
        if self.container:
            try:
                self.container.stop(timeout=1)
                self.container.remove(force=True)
            except Exception as e:
                print(f"Warning: Failed to cleanup container: {e}")
            finally:
                self.container = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
